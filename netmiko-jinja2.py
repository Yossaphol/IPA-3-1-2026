import os
from jinja2 import Environment, FileSystemLoader
from netmiko import ConnectHandler

KEY_PATH = "/home/devasc/.ssh/id_rsa"

s1_device = {
    "device_type": "cisco_ios",
    "host": "172.31.30.3",
    "username": "admin",
    "use_keys": True,
    "key_file": KEY_PATH,
}

r1_device = {
    "device_type": "cisco_ios",
    "host": "172.31.30.4",
    "username": "admin",
    "use_keys": True,
    "key_file": KEY_PATH,
}

r2_device = {
    "device_type": "cisco_ios",
    "host": "172.31.30.5",
    "username": "admin",
    "use_keys": True,
    "key_file": KEY_PATH,
}

def deploy_config(device_info, config_commands, device_name):
    print(f"\n--- Deploying configuration to {device_name} ({device_info['host']}) ---")
    try:
        net_connect = ConnectHandler(**device_info)
        
        output = net_connect.send_config_set(config_commands)
        print(output)
        
        net_connect.send_command("write memory")
        print(f" Successfully configured {device_name} and saved to memory.")
        
        net_connect.disconnect()
    except Exception as e:
        print(f"Failed to configure {device_name}: {e}")

if __name__ == "__main__":
    env = Environment(loader=FileSystemLoader("templates"))
    
    network_devices = [
        {
            "info": s1_device,
            "name": "S1",
            "template_file": "s1_template.j2",
            "config": {
                "vlan_id": 101,
                "vlan_name": "control_data_plane",
                "interfaces": [
                    {"name": "GigabitEthernet0/1", "vlan": 101},
                    {"name": "GigabitEthernet0/2", "vlan": 101},
                ],
                "vty_acl": {"id": 10, "source": "172.31.30.0", "wildcard": "0.0.0.255"},
            },
        },
        {
            "info": r1_device,
            "name": "R1",
            "template_file": "r1_template.j2",
            "config": {
                "interfaces": [
                    {
                        "name": "GigabitEthernet0/1",
                        "vrf": "control-data",
                        "ip_address": "10.10.30.1",
                        "subnet_mask": "255.255.255.0",
                    },
                    {
                        "name": "GigabitEthernet0/2",
                        "vrf": "control-data",
                        "ip_address": "10.30.30.1",
                        "subnet_mask": "255.255.255.252",
                    },
                ],
                "ospf": {
                    "process_id": 1,
                    "vrf": "control-data",
                    "router_id": "1.1.1.1",
                    "networks": [
                        {"ip": "10.10.30.0", "wildcard": "0.0.0.255", "area": 0},
                        {"ip": "10.30.30.0", "wildcard": "0.0.0.3", "area": 0},
                    ],
                },
                "vty_acl": {"id": 10, "source": "172.31.30.0", "wildcard": "0.0.0.255"},
            },
        },
        {
            "info": r2_device,
            "name": "R2",
            "template_file": "r2_template.j2",
            "config": {
                "interfaces": [
                    {
                        "name": "GigabitEthernet0/1",
                        "vrf": "control-data",
                        "ip_address": "10.30.30.2",
                        "subnet_mask": "255.255.255.252",
                        "nat": "inside",
                    },
                    {
                        "name": "GigabitEthernet0/2",
                        "vrf": "control-data",
                        "ip_address": "10.20.30.1",
                        "subnet_mask": "255.255.255.0",
                        "nat": "inside",
                    },
                    {
                        "name": "GigabitEthernet0/3",
                        "ip_address": "dhcp",
                        "subnet_mask": "",
                        "nat": "outside",
                    },
                ],
                "ospf": {
                    "process_id": 1,
                    "vrf": "control-data",
                    "router_id": "2.2.2.2",
                    "networks": [
                        {"ip": "10.20.30.0", "wildcard": "0.0.0.255", "area": 0},
                        {"ip": "10.30.30.0", "wildcard": "0.0.0.3", "area": 0},
                    ],
                },
                "static_route": {
                    "vrf": "control-data",
                    "prefix": "0.0.0.0",
                    "mask": "0.0.0.0",
                    "interface": "GigabitEthernet0/3",
                },
                "nat_acl": {
                    "id": 1,
                    "source": "10.0.0.0",
                    "wildcard": "0.255.255.255",
                    "out_intf": "GigabitEthernet0/3",
                    "vrf": "control-data",
                },
                "vty_acl": {"id": 10, "source": "172.31.30.0", "wildcard": "0.0.0.255"},
            },
        },
    ]

    for device in network_devices:
        template = env.get_template(device["template_file"])
        
        rendered_config = template.render(**device["config"])
        
        config_commands = [line.strip() for line in rendered_config.splitlines() if line.strip()]
        
        deploy_config(device["info"], config_commands, device["name"])