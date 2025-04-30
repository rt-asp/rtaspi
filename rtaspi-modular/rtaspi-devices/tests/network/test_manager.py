"""
Tests for the network device manager.
"""

import os
import json
import pytest
from unittest.mock import Mock, patch
from rtaspi_devices.network import NetworkDeviceManager, NetworkDevice
from rtaspi_devices.base.device import DeviceStatus


@pytest.fixture
def mcp_broker():
    """Create a mock MCP broker."""
    broker = Mock()
    broker.subscribe = Mock()
    broker.publish = Mock()
    return broker


@pytest.fixture
def config():
    """Create test configuration."""
    return {
        "network_devices": {
            "scan_interval": 10,
            "discovery_methods": ["onvif", "upnp"]
        },
        "system": {
            "storage_path": "/tmp/rtaspi-test"
        }
    }


@pytest.fixture
def manager(config, mcp_broker):
    """Create a network device manager."""
    manager = NetworkDeviceManager(config, mcp_broker)
    yield manager
    # Cleanup
    if os.path.exists("/tmp/rtaspi-test"):
        import shutil
        shutil.rmtree("/tmp/rtaspi-test")


def test_manager_initialization(manager, config, mcp_broker):
    """Test manager initialization."""
    assert manager.config == config
    assert manager.mcp_broker == mcp_broker
    assert manager.running is False
    assert manager.devices == {}
    assert manager.scan_interval == 10
    assert manager.discovery_methods == ["onvif", "upnp"]


def test_manager_start_stop(manager, mcp_broker):
    """Test manager start/stop."""
    # Mock the mcp_client
    manager.mcp_client = Mock()
    manager.mcp_client.close = Mock()

    manager.start()
    assert manager.running is True
    mcp_broker.subscribe.assert_called_once()

    manager.stop()
    assert manager.running is False
    manager.mcp_client.close.assert_called_once()


def test_add_device(manager, mcp_broker):
    """Test adding a device."""
    device_id = manager.add_device(
        name="Test Camera",
        ip="192.168.1.100",
        port=554,
        type="video",
        protocol="rtsp"
    )

    assert device_id == "192.168.1.100:554"
    assert device_id in manager.devices
    device = manager.devices[device_id]
    assert isinstance(device, NetworkDevice)
    assert device.name == "Test Camera"
    assert device.ip == "192.168.1.100"
    assert device.port == 554

    # Verify event was published
    mcp_broker.publish.assert_called_with(
        f"event/network_devices/added/{device_id}",
        device.to_dict()
    )

    # Test adding duplicate device
    with pytest.raises(ValueError):
        manager.add_device(
            name="Test Camera",
            ip="192.168.1.100",
            port=554
        )


def test_remove_device(manager, mcp_broker):
    """Test removing a device."""
    # Add a device first
    device_id = manager.add_device(
        name="Test Camera",
        ip="192.168.1.100",
        port=554,
        type="video",
        protocol="rtsp"
    )

    # Reset mock to clear add_device call
    mcp_broker.publish.reset_mock()

    # Remove device
    assert manager.remove_device(device_id) is True
    assert device_id not in manager.devices

    # Verify event was published
    mcp_broker.publish.assert_called_with(
        f"event/network_devices/removed/{device_id}",
        {"device_id": device_id}
    )

    # Test removing non-existent device
    with pytest.raises(ValueError):
        manager.remove_device("unknown")


def test_update_device(manager, mcp_broker):
    """Test updating a device."""
    # Add a device first
    device_id = manager.add_device(
        name="Test Camera",
        ip="192.168.1.100",
        port=554,
        type="video",
        protocol="rtsp"
    )

    # Reset mock to clear add_device call
    mcp_broker.publish.reset_mock()

    # Update device
    assert manager.update_device(
        device_id,
        name="Updated Camera",
        protocol="rtmp"
    ) is True

    device = manager.devices[device_id]
    assert device.name == "Updated Camera"
    assert device.protocol == "rtmp"

    # Verify event was published
    mcp_broker.publish.assert_called_with(
        f"event/network_devices/updated/{device_id}",
        device.to_dict()
    )

    # Test updating non-existent device
    with pytest.raises(ValueError):
        manager.update_device("unknown", name="Test")


def test_device_status_update(manager, mcp_broker):
    """Test device status updates."""
    # Add a device first
    device_id = manager.add_device(
        name="Test Camera",
        ip="192.168.1.100",
        port=554,
        type="video",
        protocol="rtsp"
    )

    # Reset mock to clear add_device call
    mcp_broker.publish.reset_mock()

    # Update status
    device = manager.devices[device_id]
    device.status = DeviceStatus.ONLINE

    # Publish status
    manager._publish_device_status(device_id, device.status)

    # Verify event was published
    mcp_broker.publish.assert_called_with(
        f"event/network_devices/status/{device_id}",
        {"device_id": device_id, "status": "online"}
    )


def test_command_handling(manager):
    """Test command handling."""
    # Test scan command
    manager._handle_command("command/network_devices/scan", {})
    # No assertion needed as scan is a no-op in tests

    # Test add command
    manager._handle_command(
        "command/network_devices/add",
        {
            "name": "Test Camera",
            "ip": "192.168.1.100",
            "port": 554,
            "type": "video",
            "protocol": "rtsp"
        }
    )
    assert "192.168.1.100:554" in manager.devices

    # Test update command
    manager._handle_command(
        "command/network_devices/update",
        {
            "device_id": "192.168.1.100:554",
            "name": "Updated Camera"
        }
    )
    assert manager.devices["192.168.1.100:554"].name == "Updated Camera"

    # Test remove command
    manager._handle_command(
        "command/network_devices/remove",
        {"device_id": "192.168.1.100:554"}
    )
    assert "192.168.1.100:554" not in manager.devices

    # Test invalid command
    with pytest.raises(ValueError):
        manager._handle_command("command/network_devices/invalid", {})


def test_state_persistence(manager):
    """Test state persistence."""
    # Add some devices
    manager.add_device(
        name="Camera 1",
        ip="192.168.1.100",
        port=554,
        type="video",
        protocol="rtsp"
    )
    manager.add_device(
        name="Camera 2",
        ip="192.168.1.101",
        port=554,
        type="video",
        protocol="rtsp"
    )

    # Save state
    manager._save_devices()

    # Create new manager
    new_manager = NetworkDeviceManager(manager.config, manager.mcp_broker)
    new_manager._load_saved_devices()

    # Verify devices were loaded
    assert len(new_manager.devices) == 2
    assert "192.168.1.100:554" in new_manager.devices
    assert "192.168.1.101:554" in new_manager.devices

    device1 = new_manager.devices["192.168.1.100:554"]
    assert device1.name == "Camera 1"
    assert device1.ip == "192.168.1.100"
    assert device1.port == 554

    device2 = new_manager.devices["192.168.1.101:554"]
    assert device2.name == "Camera 2"
    assert device2.ip == "192.168.1.101"
    assert device2.port == 554


def test_scan_interval(manager):
    """Test scan interval configuration."""
    assert manager._get_scan_interval() == 10

    # Test default interval
    manager.config["network_devices"]["scan_interval"] = None
    assert manager._get_scan_interval() == 60  # Default value


def test_client_id(manager):
    """Test client ID generation."""
    assert manager._get_client_id() == "network_devices_manager"


@pytest.mark.asyncio
async def test_device_discovery(manager):
    """Test device discovery process."""
    with patch.object(manager, '_discover_devices') as mock_discover:
        # Mock discovered devices
        mock_discover.return_value = [
            {
                "name": "Discovered Camera",
                "ip": "192.168.1.200",
                "port": 554,
                "type": "video",
                "protocol": "rtsp"
            }
        ]

        # Run discovery
        manager._scan_devices()

        # Verify device was added
        assert "192.168.1.200:554" in manager.devices
        device = manager.devices["192.168.1.200:554"]
        assert device.name == "Discovered Camera"
        assert device.ip == "192.168.1.200"
