import concurrent.futures
import os
import re
from netmiko import ConnectHandler
from tabulate import tabulate

KEY_PATH = os.path.expanduser("~/.ssh/id_rsa")

# ข้อมูลสำหรับเชื่อมต่อไปยัง Routers
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


def parse_cpu_memory(net_connect):
    """ดึงข้อมูล CPU และ Memory Usage"""
    cpu_usage = "N/A"
    mem_usage = "N/A"

    try:
        # 1. CPU Usage
        cpu_out = net_connect.send_command("show processes cpu | inc CPU utilization")
        # ตัวอย่าง: CPU utilization for five seconds: 2%/0%; one minute: 3%; five minutes: 2%
        cpu_match = re.search(r"five seconds:\s*(\d+%)", cpu_out)
        if cpu_match:
            cpu_usage = cpu_match.group(1)

        # 2. Memory Usage
        mem_out = net_connect.send_command("show processes memory | inc Processor")
        # ตัวอย่าง: Processor Pool Total:  458321484 Used:  125489124 Free:  332832360
        mem_match = re.search(
            r"Total:\s*(\d+),\s*Used:\s*(\d+),\s*Free:\s*(\d+)", mem_out
        )
        if mem_match:
            total = int(mem_match.group(1))
            used = int(mem_match.group(2))
            percent = (used / total) * 100
            mem_usage = f"{percent:.1f}% ({used//(1024**2)}MB / {total//(1024**2)}MB)"

    except Exception as e:
        pass

    return cpu_usage, mem_usage


def parse_cdp_neighbors(net_connect):
    """ดึงข้อมูลอุปกรณ์เพื่อนบ้านผ่าน CDP"""
    cdp_neighbors = []
    try:
        cdp_out = net_connect.send_command("show cdp neighbors")
        # Regex สำหรับดึง Local Int, Neighbor Device, Remote Int
        # ตัวอย่าง: R2.lab           Gig 0/1          120           R S I      C1900         Gig 0/0
        pattern = re.compile(
            r"^(\S+)\s+(\S+\s+\d+(?:/\d+)*)\s+\d+.*?\s+(\S+\s+\d+(?:/\d+)*)$",
            re.MULTILINE,
        )
        matches = pattern.findall(cdp_out)
        for match in matches:
            device, local_int, remote_int = match
            cdp_neighbors.append([local_int, device, remote_int])
    except Exception:
        pass

    return cdp_neighbors


def get_router_info(router_data):
    device_info = router_data["connection"]
    device_name = router_data["name"]
    output_lines = []

    header = f" Connecting to {device_name} ({device_info['host']}) "
    output_lines.append("\n" + "=" * 65)
    output_lines.append(f"{header:^65}")
    output_lines.append("=" * 65)

    try:
        net_connect = ConnectHandler(**device_info)

        # --- 1. Uptime ---
        show_version_output = net_connect.send_command("show version")
        uptime_match = re.search(r".* uptime is (.*)", show_version_output)
        uptime = uptime_match.group(1) if uptime_match else "Not found"

        # --- 2. CPU & Memory ---
        cpu_usage, mem_usage = parse_cpu_memory(net_connect)

        output_lines.append(f"[*] Uptime      : {uptime}")
        output_lines.append(f"[*] CPU Load    : {cpu_usage}")
        output_lines.append(f"[*] Memory Load : {mem_usage}")

        # --- 3. Active Interfaces ---
        show_ip_int_output = net_connect.send_command("show ip interface brief")
        intf_pattern = re.compile(
            r"^(\S+)\s+(\S+)\s+YES\s+\S+\s+(up)\s+(up)", re.MULTILINE
        )
        active_interfaces = intf_pattern.findall(show_ip_int_output)

        output_lines.append("\n[+] Active Interfaces (Status: up, Protocol: up):")
        if active_interfaces:
            table_intf = tabulate(
                active_interfaces,
                headers=["Interface", "IP Address", "Status", "Protocol"],
                tablefmt="github",
            )
            output_lines.append(table_intf)
        else:
            output_lines.append("    No active interfaces found.")

        # --- 4. CDP Neighbors ---
        cdp_list = parse_cdp_neighbors(net_connect)
        output_lines.append("\n[+] CDP Neighbors:")
        if cdp_list:
            table_cdp = tabulate(
                cdp_list,
                headers=["Local Interface", "Neighbor Device", "Neighbor Port"],
                tablefmt="github",
            )
            output_lines.append(table_cdp)
        else:
            output_lines.append("    No CDP neighbors found.")

        net_connect.disconnect()

        # Print ผลลัพธ์รวดเดียวเพื่อป้องกันข้อความตีกันเวลาทำ Multithreading
        print("\n".join(output_lines))

    except Exception as e:
        print(f"\n[!] Failed to connect or process {device_name}: {e}\n")


if __name__ == "__main__":
    # ทำงานแบบ Parallel พร้อมกันด้วย ThreadPoolExecutor
    print("Starting network discovery...")
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=len(routers)
    ) as executor:
        executor.map(get_router_info, routers)