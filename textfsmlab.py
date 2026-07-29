import os
import re
from netmiko import ConnectHandler

os.environ["NET_TEXTFSM"] = "/home/devasc/ipa_lab2/venv/lib/python3.8/site-packages/ntc_templates/templates"

KEY_PATH = os.path.expanduser("~/.ssh/id_rsa")

s1_device = {
    "device_type": "cisco_ios",
    "host": "172.31.30.3",
    "username": "admin",
    "use_keys": True,
    "key_file": KEY_PATH,
    'conn_timeout': 30,
    'auth_timeout': 30,
    'disabled_algorithms': {'pubkeys': ['rsa-sha2-512', 'rsa-sha2-256']},
}

r1_device = {
    "device_type": "cisco_ios",
    "host": "172.31.30.4",
    "username": "admin",
    "use_keys": True,
    "key_file": KEY_PATH,
    'conn_timeout': 30,
    'auth_timeout': 30,
    'disabled_algorithms': {'pubkeys': ['rsa-sha2-512', 'rsa-sha2-256']},
}

r2_device = {
    "device_type": "cisco_ios",
    "host": "172.31.30.5",
    "username": "admin",
    "use_keys": True,
    "key_file": KEY_PATH,
    'conn_timeout': 30,
    'auth_timeout': 30,
    'disabled_algorithms': {'pubkeys': ['rsa-sha2-512', 'rsa-sha2-256']},

}

pc_interfaces = {
    "S1-P": ["GigabitEthernet1/1"],
    "R1-P": ["GigabitEthernet0/1"],
    "R2-P": []
}

_PREFIX_MAP = {
    "gigabitethernet": "g", "gig": "g", "gi": "g", "g": "g",
    "fastethernet": "fa", "fa": "fa",
    "tengigabitethernet": "te", "tengige": "te", "te": "te",
    "ethernet": "e", "eth": "e", "et": "e", "e": "e",
}


def _split_prefix_number(name: str):
    name = name.strip().lower().replace(" ", "")
    m = re.match(r"^([a-z]+)([\d/]+)$", name)
    if not m:
        return name, ""
    return m.groups()


def normalize_for_match(name: str) -> str:
    if not name:
        return ""
    prefix, number = _split_prefix_number(name)
    short_prefix = _PREFIX_MAP.get(prefix, prefix)
    return f"{short_prefix}{number}"


def format_interface_display(name: str) -> str:
    if not name:
        return ""
    prefix, number = _split_prefix_number(name)
    short_prefix = _PREFIX_MAP.get(prefix, prefix)
    return f"{short_prefix.capitalize()}{number}"


def generate_description(device, interface, cdp_data=None, is_pc=False):
    display_int = format_interface_display(interface)

    if device == "R2" and display_int == "G0/3":
        return "Connect to WAN"
    if is_pc:
        return "Connect to PC"

    if cdp_data:
        raw_device = (
            cdp_data.get("neighbor_name")
            or cdp_data.get("hostname")
            or cdp_data.get("destination_host")
            or cdp_data.get("neighbor")
        )
        raw_port = cdp_data.get("neighbor_interface") or cdp_data.get("remote_port")

        raw_platform = cdp_data.get("platform", "")
        prefix_candidate, _ = _split_prefix_number(raw_platform)
        if _PREFIX_MAP.get(prefix_candidate) and re.match(r"^[\d/]+$", str(raw_port or "")):
            raw_port = f"{raw_platform}{raw_port}"

        if raw_device and raw_port:
            remote_device = str(raw_device).split(".")[0]

            remote_port = format_interface_display(raw_port)

            return f"Connect to {remote_port} of {remote_device}"

    return ""


def run_automation():
    devices = [
        {"info": s1_device, "name": "S1-P", "short_name": "S1"},
        {"info": r1_device, "name": "R1-P", "short_name": "R1"},
        {"info": r2_device, "name": "R2-P", "short_name": "R2"}
    ]

    pc_interfaces_normalized = {
        dev_name: {normalize_for_match(i) for i in intf_list}
        for dev_name, intf_list in pc_interfaces.items()
    }

    for dev in devices:
        print(f"\n--- Processing {dev['name']} ---")
        try:
            net_connect = ConnectHandler(**dev["info"])

            cdp_output = net_connect.send_command("show cdp neighbors", use_textfsm=True)

            interfaces_output = net_connect.send_command("show interfaces description", use_textfsm=True)

            config_commands = []

            for intf in interfaces_output:
                intf_name = intf.get("port") or intf.get("interface") or intf.get("intf")
                if not intf_name:
                    continue

                target_p = normalize_for_match(intf_name)
                is_pc = target_p in pc_interfaces_normalized.get(dev["name"], set())

                cdp_match = None
                if isinstance(cdp_output, list):
                    for neighbor in cdp_output:
                        local_raw = neighbor.get("local_interface", "") or neighbor.get("local_port", "")
                        local_p = normalize_for_match(local_raw)

                        if local_p == target_p:
                            cdp_match = neighbor
                            break

                desc = generate_description(
                    device=dev["short_name"],
                    interface=intf_name,
                    cdp_data=cdp_match,
                    is_pc=is_pc
                )

                if desc:
                    config_commands.extend([
                        f"interface {intf_name}",
                        f"description {desc}",
                        "exit"
                    ])

            if config_commands:
                print(f"Sending configuration to {dev['name']}...")
                output = net_connect.send_config_set(config_commands, delay_factor=4)
                print(output)
                write_output = net_connect.send_command_timing("write memory")
                print(write_output)
            else:
                print(f"No interface matching description rules on {dev['name']}.")

            net_connect.disconnect()

        except Exception as e:
            print(f"Error on {dev['name']}: {e}")


if __name__ == "__main__":
    run_automation()