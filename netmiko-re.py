import os
import re
from netmiko import ConnectHandler

KEY_PATH = os.path.expanduser("~/.ssh/id_rsa")

# ข้อมูลสำหรับเชื่อมต่อไปยัง R1 และ R2
routers = [
    {
        "name": "R1",
        "connection": {
            "device_type": "cisco_ios",
            "host": "172.31.30.4",
            "username": "admin",
            "use_keys": True,
            "key_file": KEY_PATH,
            "allow_agent": False,
            "system_host_keys": False,
        },
    },
    {
        "name": "R2",
        "connection": {
            "device_type": "cisco_ios",
            "host": "172.31.30.5",
            "username": "admin",
            "use_keys": True,
            "key_file": KEY_PATH,
            "allow_agent": False,
            "system_host_keys": False,
        },
    },
]

def get_router_info(device_info, device_name):
    print(f"==========================================")
    print(f" Connecting to {device_name} ({device_info['host']})")
    print(f"==========================================")
    
    try:
        net_connect = ConnectHandler(**device_info)
        
        # 1. ดึง Uptime จาก show version
        show_version_output = net_connect.send_command("show version")
        # Regular Expression หาคำว่า "... uptime is ..."
        uptime_match = re.search(r".* uptime is (.*)", show_version_output)
        if uptime_match:
            uptime = uptime_match.group(1)
            print(f"[*] Uptime: {uptime}")
        else:
            print("[*] Uptime: Not found")
            
        print("\n[*] Active Interfaces (Status: up, Protocol: up):")
        print(f"{'Interface':<25} {'IP Address':<18} {'Status':<10} {'Protocol':<10}")
        print("-" * 65)
        
        # 2. ดึง Active Interfaces จาก show ip interface brief
        show_ip_int_output = net_connect.send_command("show ip interface brief")
        
        # Regex สำหรับจับคู่บรรทัด interface ที่มี Status = up และ Protocol = up
        # ตัวอย่างบรรทัด: GigabitEthernet0/1  10.10.30.1  YES manual up  up
        intf_pattern = re.compile(
            r"^(\S+)\s+(\S+)\s+YES\s+\S+\s+(up)\s+(up)", re.MULTILINE
        )
        
        active_interfaces = intf_pattern.findall(show_ip_int_output)
        
        for intf in active_interfaces:
            intf_name, ip_addr, status, protocol = intf
            print(f"{intf_name:<25} {ip_addr:<18} {status:<10} {protocol:<10}")
            
        net_connect.disconnect()
        print("\n")
        
    except Exception as e:
        print(f"Failed to connect or process {device_name}: {e}\n")

if __name__ == "__main__":
    for router in routers:
        get_router_info(router["connection"], router["name"])