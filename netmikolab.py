from netmiko import ConnectHandler

KEY_PATH = "/home/devasc/.ssh/id_rsa"

s1_device = {
    "device_type": "cisco_ios",
    "host": "172.31.30.3",
    "username": "admin",
    "use_keys": True,
    "key_file": KEY_PATH
}

r1_device = {
    "device_type": "cisco_ios",
    "host": "172.31.30.4",
    "username": "admin",
    "use_keys": True,
    "key_file": KEY_PATH
}

r2_device = {
    "device_type": "cisco_ios",
    "host": "172.31.30.5",
    "username": "admin",
    "use_keys": True,
    "key_file": KEY_PATH
}

# --- ชุดคำสั่งตาม IP ใน Topology ของคุณ ---
s1_commands = [
    "vlan 101",
    "name control_data_plane",
    "exit",
    "interface gigabitEthernet 0/1",
    "switchport mode access",
    "switchport access vlan 101",
    "interface gigabitEthernet 0/2",
    "switchport mode access",
    "switchport access vlan 101",
    "exit",
    # ACL อนุญาต Management (172.31.30.0/28) และ Lab306 (10.30.6.0/23)
    "access-list 10 permit 172.31.30.0 0.0.0.15",
    "access-list 10 permit 10.30.6.0 0.0.1.255",
    "line vty 0 4",
    "access-class 10 in",
]

r1_commands = [
    "router ospf 1 vrf control-data",
    "network 10.10.30.0 0.0.0.255 area 0",
    "network 10.30.30.0 0.0.0.255 area 0",
    "exit",
    "access-list 10 permit 172.31.30.0 0.0.0.15",
    "access-list 10 permit 10.30.6.0 0.0.1.255",
    "line vty 0 4",
    "access-class 10 in",
]

r2_commands = [
    "interface GigabitEthernet0/3",
    "no shutdown",
    "ip nat outside",
    "exit",
    "interface GigabitEthernet0/1",
    "ip nat inside",
    "exit",
    "interface GigabitEthernet0/2",
    "ip nat inside",
    "exit",
    "access-list 1 permit 10.0.0.0 0.255.255.255",
    "ip nat inside source list 1 interface GigabitEthernet0/3 overload",
    "router ospf 1 vrf control-data",
    "network 10.20.30.0 0.0.0.255 area 0",
    "network 10.30.30.0 0.0.0.255 area 0",
    "default-information originate always",
    "exit",
    "access-list 10 permit 172.31.30.0 0.0.0.15",
    "access-list 10 permit 10.30.6.0 0.0.1.255",
    "line vty 0 4",
    "access-class 10 in",
]


def deploy_config(device_info, config_commands, device_name):
    print(
        f"\n--- Deploying configuration to {device_name} ({device_info['host']}) ---"
    )
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
    deploy_config(s1_device, s1_commands, "S1")
    deploy_config(r1_device, r1_commands, "R1")
    deploy_config(r2_device, r2_commands, "R2")