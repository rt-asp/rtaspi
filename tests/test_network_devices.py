import pytest
from unittest.mock import MagicMock, patch

from rtaspi.core.mcp import MCPBroker
from rtaspi.device_managers.network_devices import NetworkDevicesManager
from rtaspi.device_managers.utils.device import NetworkDevice

@pytest.fixture
def mcp_broker():
    return MagicMock(spec=MCPBroker)

@pytest.fixture
def config():
    return {
        'network_devices': {
            'scan_interval': 60,
            'discovery_enabled': True,
            'discovery_methods': ['onvif', 'upnp', 'mdns']
        },
        'system': {
            'storage_path': '/tmp'
        }
    }

@pytest.fixture
def network_manager(config, mcp_broker):
    return NetworkDevicesManager(config, mcp_broker)

def test_network_manager_initialization(network_manager, config):
    assert isinstance(network_manager, NetworkDevicesManager)
    assert hasattr(network_manager, 'mcp_broker')
    assert hasattr(network_manager, 'devices')
    assert isinstance(network_manager.devices, dict)
    assert network_manager.scan_interval == config['network_devices']['scan_interval']
    assert set(network_manager.discovery_methods) == set(['onvif', 'upnp', 'mdns'])

def test_add_device(network_manager):
    device_id = network_manager.add_device(
        name="Test Camera",
        ip="192.168.1.100",
        port=554,
        username="admin",
        password="admin",
        type="video",
        protocol="rtsp",
        paths=["/stream1", "/stream2"]
    )
    
    assert device_id is not None
    assert device_id in network_manager.devices
    device = network_manager.devices[device_id]
    assert isinstance(device, NetworkDevice)
    assert device.name == "Test Camera"
    assert device.ip == "192.168.1.100"
    assert device.port == 554
    assert device.type == "video"
    assert device.protocol == "rtsp"
    assert len(device.streams) == 2

def test_remove_device(network_manager):
    # First add a device
    device_id = network_manager.add_device(
        name="Test Camera",
        ip="192.168.1.100",
        port=554,
        type="video",
        protocol="rtsp"
    )
    
    # Then remove it
    success = network_manager.remove_device(device_id)
    
    assert success
    assert device_id not in network_manager.devices

def test_discover_devices(network_manager):
    # Mock discovery modules
    mock_onvif_devices = [{
        'name': 'ONVIF Camera',
        'ip': '192.168.1.101',
        'port': 80,
        'type': 'video',
        'protocol': 'rtsp',
        'paths': ['/onvif-media/media.amp']
    }]
    
    mock_upnp_devices = [{
        'name': 'UPnP Camera',
        'ip': '192.168.1.102',
        'port': 80,
        'type': 'video',
        'protocol': 'rtsp'
    }]
    
    mock_mdns_devices = [{
        'name': 'mDNS Camera',
        'ip': '192.168.1.103',
        'port': 5353,
        'type': 'video',
        'protocol': 'rtsp'
    }]
    
    network_manager.discovery_modules['onvif'].discover = MagicMock(return_value=mock_onvif_devices)
    network_manager.discovery_modules['upnp'].discover = MagicMock(return_value=mock_upnp_devices)
    network_manager.discovery_modules['mdns'].discover = MagicMock(return_value=mock_mdns_devices)
    
    # Run discovery
    network_manager._discover_devices()
    
    # Verify all discovery methods were called
    network_manager.discovery_modules['onvif'].discover.assert_called_once()
    network_manager.discovery_modules['upnp'].discover.assert_called_once()
    network_manager.discovery_modules['mdns'].discover.assert_called_once()
    
    # Verify devices were added
    assert len(network_manager.devices) == 3

def test_handle_command(network_manager):
    # Test scan command
    with patch.object(network_manager, '_scan_devices') as mock_scan:
        network_manager._handle_command("command/network_devices/scan", {})
        mock_scan.assert_called_once()
    
    # Test add command
    device_data = {
        'name': 'Test Camera',
        'ip': '192.168.1.100',
        'port': 554,
        'type': 'video',
        'protocol': 'rtsp'
    }
    network_manager._handle_command("command/network_devices/add", device_data)
    assert len(network_manager.devices) == 1
