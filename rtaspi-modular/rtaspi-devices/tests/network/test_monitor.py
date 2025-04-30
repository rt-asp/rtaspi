"""
Tests for the network device monitor.
"""

import pytest
from unittest.mock import Mock, patch
from rtaspi_devices.network import NetworkDeviceMonitor, NetworkDevice
from rtaspi_devices.base.device import DeviceStatus


@pytest.fixture
def config():
    """Create test configuration."""
    return {
        "network_devices": {
            "discovery_methods": ["onvif", "upnp", "mdns"],
            "scan_interval": 30
        }
    }


@pytest.fixture
def monitor(config):
    """Create a network device monitor."""
    return NetworkDeviceMonitor(config)


@pytest.fixture
def device():
    """Create a test device."""
    return NetworkDevice(
        device_id="192.168.1.100:554",
        name="Test Camera",
        type="video",
        ip="192.168.1.100",
        port=554,
        protocol="rtsp"
    )


def test_monitor_initialization(monitor, config):
    """Test monitor initialization."""
    assert monitor.config == config
    assert monitor.discovery_methods == ["onvif", "upnp", "mdns"]


@patch("socket.socket")
def test_check_device_status_online(mock_socket, monitor, device):
    """Test device status checking - online case."""
    # Mock socket to simulate successful connection
    mock_sock = Mock()
    mock_sock.connect_ex.return_value = 0
    mock_socket.return_value = mock_sock

    status = monitor.check_device_status(device)
    assert status == DeviceStatus.ONLINE

    mock_sock.connect_ex.assert_called_once_with(
        (device.ip, device.port)
    )


@patch("socket.socket")
def test_check_device_status_offline(mock_socket, monitor, device):
    """Test device status checking - offline case."""
    # Mock socket to simulate failed connection
    mock_sock = Mock()
    mock_sock.connect_ex.return_value = 1
    mock_socket.return_value = mock_sock

    status = monitor.check_device_status(device)
    assert status == DeviceStatus.OFFLINE


@patch("socket.socket")
def test_check_device_status_error(mock_socket, monitor, device):
    """Test device status checking - error case."""
    # Mock socket to simulate error
    mock_sock = Mock()
    mock_sock.connect_ex.side_effect = Exception("Test error")
    mock_socket.return_value = mock_sock

    status = monitor.check_device_status(device)
    assert status == DeviceStatus.UNKNOWN


def test_discover_devices(monitor):
    """Test device discovery process."""
    # Mock discovery methods
    with patch.multiple(
        monitor,
        _discover_onvif_devices=Mock(return_value=[
            {
                "name": "ONVIF Camera",
                "ip": "192.168.1.101",
                "port": 554,
                "type": "video",
                "protocol": "rtsp"
            }
        ]),
        _discover_upnp_devices=Mock(return_value=[
            {
                "name": "UPnP Camera",
                "ip": "192.168.1.102",
                "port": 554,
                "type": "video",
                "protocol": "rtsp"
            }
        ]),
        _discover_mdns_devices=Mock(return_value=[
            {
                "name": "mDNS Camera",
                "ip": "192.168.1.103",
                "port": 554,
                "type": "video",
                "protocol": "rtsp"
            }
        ])
    ):
        devices = monitor.discover_devices()
        assert len(devices) == 3

        # Verify ONVIF device
        onvif_device = next(d for d in devices if d["name"] == "ONVIF Camera")
        assert onvif_device["ip"] == "192.168.1.101"

        # Verify UPnP device
        upnp_device = next(d for d in devices if d["name"] == "UPnP Camera")
        assert upnp_device["ip"] == "192.168.1.102"

        # Verify mDNS device
        mdns_device = next(d for d in devices if d["name"] == "mDNS Camera")
        assert mdns_device["ip"] == "192.168.1.103"


def test_discover_devices_with_error(monitor):
    """Test device discovery with method failure."""
    # Mock discovery methods - one fails
    with patch.multiple(
        monitor,
        _discover_onvif_devices=Mock(side_effect=Exception("ONVIF error")),
        _discover_upnp_devices=Mock(return_value=[
            {
                "name": "UPnP Camera",
                "ip": "192.168.1.102",
                "port": 554,
                "type": "video",
                "protocol": "rtsp"
            }
        ]),
        _discover_mdns_devices=Mock(return_value=[])
    ):
        devices = monitor.discover_devices()
        assert len(devices) == 1
        assert devices[0]["name"] == "UPnP Camera"


def test_process_discovered_devices(monitor):
    """Test processing of discovered devices."""
    # Create some existing devices
    existing = {
        "192.168.1.100:554": NetworkDevice(
            device_id="192.168.1.100:554",
            name="Existing Camera",
            type="video",
            ip="192.168.1.100",
            port=554,
            protocol="rtsp"
        )
    }

    # Create some discovered devices
    discovered = [
        {
            "name": "Existing Camera",  # Should be filtered out
            "ip": "192.168.1.100",
            "port": 554,
            "type": "video",
            "protocol": "rtsp"
        },
        {
            "name": "New Camera",  # Should be included
            "ip": "192.168.1.101",
            "port": 554,
            "type": "video",
            "protocol": "rtsp"
        }
    ]

    new_devices = monitor.process_discovered_devices(discovered, existing)
    assert len(new_devices) == 1
    assert new_devices[0]["name"] == "New Camera"
    assert new_devices[0]["ip"] == "192.168.1.101"


def test_get_discovery_modules(monitor):
    """Test getting available discovery modules."""
    modules = monitor.get_discovery_modules()
    assert isinstance(modules, list)
    assert "onvif" in modules
    assert "upnp" in modules
    assert "mdns" in modules


def test_discovery_with_invalid_method(monitor):
    """Test discovery with invalid method."""
    monitor.discovery_methods.append("invalid")
    devices = monitor.discover_devices()
    assert isinstance(devices, list)
    # Should not raise an error, just skip invalid method


def test_process_discovered_devices_empty(monitor):
    """Test processing empty discovered devices list."""
    existing = {
        "192.168.1.100:554": NetworkDevice(
            device_id="192.168.1.100:554",
            name="Existing Camera",
            type="video",
            ip="192.168.1.100",
            port=554,
            protocol="rtsp"
        )
    }

    new_devices = monitor.process_discovered_devices([], existing)
    assert len(new_devices) == 0


def test_process_discovered_devices_all_new(monitor):
    """Test processing all new devices."""
    discovered = [
        {
            "name": "Camera 1",
            "ip": "192.168.1.101",
            "port": 554,
            "type": "video",
            "protocol": "rtsp"
        },
        {
            "name": "Camera 2",
            "ip": "192.168.1.102",
            "port": 554,
            "type": "video",
            "protocol": "rtsp"
        }
    ]

    new_devices = monitor.process_discovered_devices(discovered, {})
    assert len(new_devices) == 2
    assert new_devices[0]["name"] == "Camera 1"
    assert new_devices[1]["name"] == "Camera 2"
