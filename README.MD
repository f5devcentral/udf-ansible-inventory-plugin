# Ansible Dynamic Inventory Plugin for F5 UDF

Uses the UDF metadata API, which is callable from inside a UDF deployment.

## Usage
- Copy the `inventory/udf.yml` and `plugin` folder contents to your Ansible playbook project.
- Set values for hostname and groups options in the `inventory/udf.yml` file
- Copy the contents of the `ansible.cfg` file to your local Ansible config file.

To test the inventory, use `ansible-inventory -i inventory/udf.yml --list`

## Authors
[Daniel Edgar](https://github.com/aknot242)

## Credits
Based on the [Online Ansible dynamic inventory plugin](https://github.com/ansible-collections/community.general/blob/main/plugins/inventory/online.py) by author Remy Leone (@sieben)
