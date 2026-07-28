import time
import paramiko

devices = [
    ("R0-P", "172.31.30.1"),
    ("R1-P", "172.31.30.4"),
    ("R2-P", "172.31.30.5"),
    ("S0-P", "172.31.30.2"),
    ("S1-P", "172.31.30.3")
]

for name, ip in devices:
    print(f"Connecting to {name}...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh.connect(
        hostname = ip,
        username = "admin",
        key_filename = "/home/devasc/.ssh/id_rsa",
        look_for_keys = False
    )

    shell = ssh.invoke_shell()
    time.sleep(1)

    output = shell.recv(65535).decode()
    print(output)

    print(f"SSH to {name} successful.\n")

    ssh.close()