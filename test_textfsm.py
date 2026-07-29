import pytest
from textfsmlab import generate_description

def test_cdp_neighbor_description():
    mock_cdp_data = {
        "destination_host": "R2",
        "local_port": "G0/2",
        "management_ip": "172.31.30.5",
        "platform": "Cisco",
        "remote_port": "G0/1"
    }
    
    result = generate_description(device="R1", interface="G0/2", cdp_data=mock_cdp_data)
    assert result == "Connect to G0/1 of R2"

def test_pc_connection_description():
    result = generate_description(device="R1", interface="G0/1", cdp_data=None, is_pc=True)
    assert result == "Connect to PC"

def test_r2_wan_description():
    result = generate_description(device="R2", interface="G0/3", cdp_data=None)
    assert result == "Connect to WAN"