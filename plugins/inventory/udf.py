# Copyright (c) 2020 F5 Networks
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = '''
    name: udf
    plugin_type: inventory
    author:
      - Daniel Edgar (@aknot242)
    short_description: UDF inventory source
    description:
        - Get inventory hosts from UDF
    options:
        plugin:
            description: token that ensures this is a source file for the 'udf' plugin.
            type: str
            required: true
            choices:
              - udf
              - community.general.udf
        hostname:
            description: Preference setting for which variable to use as a hostname.
            type: str
            default: private_ipv4
            choices: ['private_ipv4', 'id']
        groups:
            description: Preference setting for which source variables to use the source for groups.
            type: list
            choices: ['os']
'''

EXAMPLES = '''
# udf.yml file in YAML format
# Example command line: ansible-inventory -i inventory/udf.yml --list

plugin: udf
hostname: private_ipv4
groups:
  - os
'''

import json
from sys import version as python_version

from ansible.errors import AnsibleError
from ansible.module_utils.urls import open_url
from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.module_utils._text import to_native, to_text
from ansible.module_utils.ansible_release import __version__ as ansible_version
from ansible.module_utils.six.moves.urllib.parse import urljoin


class InventoryModule(BaseInventoryPlugin):
    NAME = 'udf'
    API_ENDPOINT = "http://metadata.udf"

    def extract_private_ipv4(self, host_infos):
        try:
            return host_infos["mgmtIp"]
        except (KeyError, TypeError, IndexError):
            self.display.warning("An error happened while extracting private IPv4 address. Information skipped.")
            return None

    def extract_internal_ssh_port(self, host_infos):
        try:
            return host_infos["accessMethods"]["ssh"][0]["internalPort"]
        except (KeyError, TypeError, IndexError):
            # self.display.warning("No internal ssh port for host. Information skipped.")
            return None

    def extract_name(self, host_infos):
        try:
            return host_infos["name"]
        except (KeyError, TypeError):
            self.display.warning("An error happened while extracting name. Information skipped.")
            return None

    def extract_id(self, host_infos):
        try:
            return host_infos["id"]
        except (KeyError, TypeError):
            self.display.warning("An error happened while extracting id. Information skipped.")
            return None

    def extract_os_name(self, host_infos):
        try:
            return host_infos["osName"]
        except (KeyError, TypeError):
            self.display.warning("An error happened while extracting OS name. Information skipped.")
            return None

    def extract_os_name_for_group(self, host_infos):
        try:
            return host_infos["osName"].replace(" ", "_").replace(".", "_").lower()
        except (KeyError, TypeError):
            self.display.warning("An error happened while extracting OS name for group. Information skipped.")
            return None

    def _fetch_information(self, url):
        USE_MOCK = False

        if USE_MOCK:
            with open('udf-mock.json') as f:
                return json.load(f)
        else:
            try:
                response = open_url(url, headers=self.headers)
            except Exception as e:
                self.display.error("An error happened while fetching: %s %s" % (url, to_native(e)))
                return None

            try:
                raw_data = to_text(response.read(), errors='surrogate_or_strict')
                return json.loads(raw_data)
            except UnicodeError:
                raise AnsibleError("Incorrect encoding of fetched payload from UDF servers")
            except ValueError:
                raise AnsibleError("Incorrect JSON payload")

    def _fill_host_variables(self, hostname, host_infos):

        if self.extract_private_ipv4(host_infos=host_infos):
            self.inventory.set_variable(hostname, "private_ipv4", self.extract_private_ipv4(host_infos=host_infos))

        if self.extract_internal_ssh_port(host_infos=host_infos):
            self.inventory.set_variable(hostname, "internal_ssh_port", self.extract_internal_ssh_port(host_infos=host_infos))

        if self.extract_name(host_infos=host_infos):
            self.inventory.set_variable(hostname, "name", self.extract_name(host_infos=host_infos))

        if self.extract_id(host_infos=host_infos):
            self.inventory.set_variable(hostname, "id", self.extract_name(host_infos=host_infos))

        if self.extract_os_name(host_infos=host_infos):
            self.inventory.set_variable(hostname, "os_name", self.extract_os_name(host_infos=host_infos))

    def _filter_host(self, host_infos, hostname_preference):

        if self.extractors[hostname_preference](host_infos):
            return self.extractors[hostname_preference](host_infos)

        return None

    def do_server_inventory(self, host_infos, hostname_preference, group_preferences):

        hostname = self._filter_host(host_infos=host_infos,
                                     hostname_preference=hostname_preference)

        # No suitable hostname were found in the attributes and the host won't be in the inventory
        if not hostname:
            return

        self.inventory.add_host(host=hostname)
        self._fill_host_variables(hostname=hostname, host_infos=host_infos)

        for g in group_preferences:
            if g not in self.group_extractors:
                self.display.warning("Invalid group name '%s' specified." % g)
                return
            group = self.group_extractors[g](host_infos)

            if not group:
                return

            self.inventory.add_group(group=group)
            self.inventory.add_host(group=group, host=hostname)

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path)
        self._read_config_data(path=path)

        hostname_preference = self.get_option("hostname")

        group_preferences = self.get_option("groups")
        if group_preferences is None:
            group_preferences = []

        self.extractors = {
            "private_ipv4": self.extract_private_ipv4,
            "id": self.extract_id,
        }

        self.group_extractors = {
            "os": self.extract_os_name_for_group
        }

        self.headers = {
            'User-Agent': "ansible %s Python %s" % (ansible_version, python_version.split(' ')[0]),
            'Content-type': 'application/json'
        }

        servers_url = urljoin(InventoryModule.API_ENDPOINT, "deployment")
        deployment_info = self._fetch_information(url=servers_url)

        if deployment_info is None:
            self.display.error("Error occurred. No inventory could be fetched from UDF API.")
            return

        for component_info in deployment_info['deployment']['components']:
            self.do_server_inventory(host_infos=component_info,
                                     hostname_preference=hostname_preference,
                                     group_preferences=group_preferences)
