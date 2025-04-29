import pytest
from unittest.mock import MagicMock, patch

from rtaspi.core.mcp import MCPBroker
from rtaspi.device_managers.local_devices import LocalDeviceManager
from rtaspi.device_managers.utils.device import Device

@pytest.fixture
def mcp_broker():
    return MagicMock(spec=MCPBroker)

@pytest.fixture
def local_manager(mcp_broker):
    return LocalDeviceManager(mcp_broker)

def test_local_manager_initialization(local_manager):
    assert isinstance(local_manager, LocalDeviceManager)
    assert hasattr(local_manager, 'mcp_broker')

@pytest.mark.asyncio
async def test_discover_devices(local_manager):
    # Mock device discovery
    mock_device = Device(
        id="test_device",
        name="Test Device",
        type="camera",
        status="online",
        capabilities=["video", "audio"]
    )
    
    with patch('rtaspi.device_managers.local_devices.DeviceDiscovery') as mock_discovery:
        mock_discovery_instance = mock_discovery.return_value
        mock_discovery_instance.discover_devices.return_value = [mock_device]
        
        devices = await local_manager.discover_devices()
        
        assert len(devices) == 1
        assert devices[0].id == "test_device"
        assert devices[0].name == "Test Device"
        assert devices[0].type == "camera"
        assert devices[0].status == "online"
        assert devices[0].capabilities == ["video", "audio"]

@pytest.mark.asyncio
async def test_connect_device(local_manager):
    device = Device(
        id="test_device",
        name="Test Device",
        type="camera",
        status="offline",
        capabilities=["video", "audio"]
    )
    
    # Test successful connection
    with patch.object(local_manager, '_establish_connection') as mock_connect:
        mock_connect.return_value = True
        
        success = await local_manager.connect_device(device)
        
        assert success
        assert device.status == "online"
        mock_connect.assert_called_once_with(device)

    # Test failed connection
    with patch.object(local_manager, '_establish_connection') as mock_connect:
        mock_connect.return_value = False
        
        success = await local_manager.connect_device(device)
        
        assert not success
        assert device.status == "offline"
        mock_connect.assert_called_once_with(device)
