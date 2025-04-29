import pytest
from unittest.mock import MagicMock, patch

from rtaspi.core.mcp import MCPBroker
from rtaspi.device_managers.network_devices import NetworkDeviceManager
from rtaspi.device_managers.utils.device import Device
from rtaspi.device_managers.utils.protocols import NetworkProtocol

@pytest.fixture
def mcp_broker():
    return MagicMock(spec=MCPBroker)

@pytest.fixture
def network_manager(mcp_broker):
    return NetworkDeviceManager(mcp_broker)

def test_network_manager_initialization(network_manager):
    assert isinstance(network_manager, NetworkDeviceManager)
    assert hasattr(network_manager, 'mcp_broker')
    assert hasattr(network_manager, 'connected_devices')
    assert isinstance(network_manager.connected_devices, dict)

@pytest.mark.asyncio
async def test_discover_devices(network_manager):
    # Mock device discovery
    mock_device = Device(
        id="test_network_device",
        name="Test Network Device",
        type="ip_camera",
        status="online",
        capabilities=["video", "audio", "ptz"],
        network_info={
            "ip": "192.168.1.100",
            "port": 554,
            "protocol": NetworkProtocol.RTSP
        }
    )
    
    with patch('rtaspi.device_managers.network_devices.DeviceDiscovery') as mock_discovery:
        mock_discovery_instance = mock_discovery.return_value
        mock_discovery_instance.discover_devices.return_value = [mock_device]
        
        devices = await network_manager.discover_devices()
        
        assert len(devices) == 1
        assert devices[0].id == "test_network_device"
        assert devices[0].name == "Test Network Device"
        assert devices[0].type == "ip_camera"
        assert devices[0].status == "online"
        assert devices[0].capabilities == ["video", "audio", "ptz"]
        assert devices[0].network_info["ip"] == "192.168.1.100"
        assert devices[0].network_info["port"] == 554
        assert devices[0].network_info["protocol"] == NetworkProtocol.RTSP

@pytest.mark.asyncio
async def test_connect_device(network_manager):
    device = Device(
        id="test_network_device",
        name="Test Network Device",
        type="ip_camera",
        status="offline",
        capabilities=["video", "audio", "ptz"],
        network_info={
            "ip": "192.168.1.100",
            "port": 554,
            "protocol": NetworkProtocol.RTSP
        }
    )
    
    # Test successful connection
    with patch.object(network_manager, '_establish_connection') as mock_connect:
        mock_connect.return_value = True
        
        success = await network_manager.connect_device(device)
        
        assert success
        assert device.status == "online"
        assert device.id in network_manager.connected_devices
        mock_connect.assert_called_once_with(device)

    # Test failed connection
    with patch.object(network_manager, '_establish_connection') as mock_connect:
        mock_connect.return_value = False
        
        success = await network_manager.connect_device(device)
        
        assert not success
        assert device.status == "offline"
        assert device.id not in network_manager.connected_devices
        mock_connect.assert_called_once_with(device)

@pytest.mark.asyncio
async def test_disconnect_device(network_manager):
    device = Device(
        id="test_network_device",
        name="Test Network Device",
        type="ip_camera",
        status="online",
        capabilities=["video", "audio", "ptz"],
        network_info={
            "ip": "192.168.1.100",
            "port": 554,
            "protocol": NetworkProtocol.RTSP
        }
    )
    
    # Add device to connected devices
    network_manager.connected_devices[device.id] = device
    
    success = await network_manager.disconnect_device(device)
    
    assert success
    assert device.status == "offline"
    assert device.id not in network_manager.connected_devices
