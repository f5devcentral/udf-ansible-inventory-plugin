# Ansible Dynamic Inventory Plugin for F5 UDF

Uses the UDF metadata API, which is callable from inside a UDF deployment.

## Usage
Copy the `inventory/udf_inventory.yml` and `plugin` folder contents to your Ansible playbook project.
Copy the contents of the `ansible.cfg` file to your local Ansible config file.

To test the inventory, use `ansible-inventory -i inventory/udf_inventory.yml --list`
