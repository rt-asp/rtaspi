import os
import pytest
from unittest.mock import MagicMock, patch

from rtaspi.core.mcp import MCPBroker
from rtaspi.device_managers.network_devices import NetworkDevicesManager
from rtaspi.device_managers.utils.device import NetworkDevice


@pytest.fixture
def network_manager(test_config, mcp_broker):
    return NetworkDevicesManager(test_config, mcp_broker)


def test_network_manager_initialization(network_manager, test_config):
    assert isinstance(network_manager, NetworkDevicesManager)
    assert hasattr(network_manager, "mcp_broker")
    assert hasattr(network_manager, "devices")
    assert isinstance(network_manager.devices, dict)
    assert (
        network_manager.scan_interval == test_config["network_devices"]["scan_interval"]
    )
    assert set(network_manager.discovery_methods) == set(["onvif", "upnp", "mdns"])


def test_add_device_success(network_manager, mock_network_device):
    device_id = network_manager.add_device(
        name=mock_network_device.name,
        ip=mock_network_device.ip,
        port=mock_network_device.port,
        type=mock_network_device.type,
        protocol=mock_network_device.protocol,
        username="admin",
        password="admin",
        paths=["/stream1", "/stream2"],
    )

    assert device_id is not None
    assert device_id in network_manager.devices
    device = network_manager.devices[device_id]
    assert isinstance(device, NetworkDevice)
    assert device.name == mock_network_device.name
    assert device.ip == mock_network_device.ip
    assert device.port == mock_network_device.port
    assert device.type == mock_network_device.type
    assert device.protocol == mock_network_device.protocol
    assert device.username == "admin"
    assert device.password == "admin"
    assert len(device.streams) == 2


def test_add_device_invalid_data(network_manager):
    # Empty strings
    with pytest.raises(ValueError):
        network_manager.add_device(name="", ip="192.168.1.100")

    with pytest.raises(ValueError):
        network_manager.add_device(name="Test Camera", ip="")

    # Invalid IP address
    with pytest.raises(ValueError):
        network_manager.add_device(
            name="Test Camera", ip="invalid_ip", port=554, type="video", protocol="rtsp"
        )

    # Invalid port
    with pytest.raises(ValueError):
        network_manager.add_device(
            name="Test Camera",
            ip="192.168.1.100",
            port=-1,  # Invalid port
            type="video",
            protocol="rtsp",
        )

    # Invalid protocol
    with pytest.raises(ValueError):
        network_manager.add_device(
            name="Test Camera",
            ip="192.168.1.100",
            port=554,
            type="video",
            protocol="invalid",  # Invalid protocol
        )


def test_add_device_duplicate(network_manager):
    # Add first device
    device_data = {
        "name": "Test Camera",
        "ip": "192.168.1.100",
        "port": 554,
        "type": "video",
        "protocol": "rtsp",
    }
    network_manager.add_device(**device_data)

    # Try to add duplicate device
    with pytest.raises(ValueError):
        network_manager.add_device(**device_data)


def test_remove_device_success(network_manager):
    # First add a device
    device_id = network_manager.add_device(
        name="Test Camera", ip="192.168.1.100", port=554, type="video", protocol="rtsp"
    )

    # Then remove it
    success = network_manager.remove_device(device_id)

    assert success
    assert device_id not in network_manager.devices


def test_remove_device_nonexistent(network_manager):
    with pytest.raises(ValueError):
        network_manager.remove_device("nonexistent_id")


def test_update_device(network_manager):
    # First add a device
    device_id = network_manager.add_device(
        name="Test Camera", ip="192.168.1.100", port=554, type="video", protocol="rtsp"
    )

    # Update device
    success = network_manager.update_device(device_id, name="Updated Camera", port=8554)

    assert success
    device = network_manager.devices[device_id]
    assert device.name == "Updated Camera"
    assert device.port == 8554
    # Original values should remain unchanged
    assert device.ip == "192.168.1.100"
    assert device.type == "video"
    assert device.protocol == "rtsp"


def test_update_device_invalid(network_manager):
    # Try to update nonexistent device
    with pytest.raises(ValueError):
        network_manager.update_device("nonexistent_id", name="Updated Camera")


def test_discover_devices_success(network_manager):
    # Mock discovery modules
    mock_onvif_devices = [
        {
            "name": "ONVIF Camera",
            "ip": "192.168.1.101",
            "port": 80,
            "type": "video",
            "protocol": "rtsp",
            "paths": ["/onvif-media/media.amp"],
        }
    ]

    mock_upnp_devices = [
        {
            "name": "UPnP Camera",
            "ip": "192.168.1.102",
            "port": 80,
            "type": "video",
            "protocol": "rtsp",
        }
    ]

    mock_mdns_devices = [
        {
            "name": "mDNS Camera",
            "ip": "192.168.1.103",
            "port": 5353,
            "type": "video",
            "protocol": "rtsp",
        }
    ]

    network_manager.discovery_modules["onvif"].discover = MagicMock(
        return_value=mock_onvif_devices
    )
    network_manager.discovery_modules["upnp"].discover = MagicMock(
        return_value=mock_upnp_devices
    )
    network_manager.discovery_modules["mdns"].discover = MagicMock(
        return_value=mock_mdns_devices
    )

    # Run discovery
    network_manager._discover_devices()

    # Verify all discovery methods were called
    network_manager.discovery_modules["onvif"].discover.assert_called_once()
    network_manager.discovery_modules["upnp"].discover.assert_called_once()
    network_manager.discovery_modules["mdns"].discover.assert_called_once()

    # Verify devices were added
    assert len(network_manager.devices) == 3

    # Verify device details
    devices = list(network_manager.devices.values())
    protocols = [d.protocol for d in devices]
    assert all(p == "rtsp" for p in protocols)

    types = [d.type for d in devices]
    assert all(t == "video" for t in types)


def test_discover_devices_with_errors(network_manager):
    # Mock discovery modules with one raising an error
    network_manager.discovery_modules["onvif"].discover = MagicMock(
        side_effect=Exception("ONVIF Error")
    )
    network_manager.discovery_modules["upnp"].discover = MagicMock(
        return_value=[
            {
                "name": "UPnP Camera",
                "ip": "192.168.1.102",
                "port": 80,
                "type": "video",
                "protocol": "rtsp",
            }
        ]
    )
    network_manager.discovery_modules["mdns"].discover = MagicMock(return_value=[])

    # Run discovery
    network_manager._discover_devices()

    # Verify all methods were called despite error
    network_manager.discovery_modules["onvif"].discover.assert_called_once()
    network_manager.discovery_modules["upnp"].discover.assert_called_once()
    network_manager.discovery_modules["mdns"].discover.assert_called_once()

    # Verify only working device was added
    assert len(network_manager.devices) == 1


def test_discover_devices_empty(network_manager):
    # Mock all discovery modules to return empty lists
    for module in network_manager.discovery_modules.values():
        module.discover = MagicMock(return_value=[])

    # Run discovery
    network_manager._discover_devices()

    # Verify no devices were added
    assert len(network_manager.devices) == 0


def test_handle_command_valid(network_manager):
    # Test scan command
    with patch.object(network_manager, "_scan_devices") as mock_scan:
        network_manager._handle_command("command/network_devices/scan", {})
        mock_scan.assert_called_once()

    # Test add command
    device_data = {
        "name": "Test Camera",
        "ip": "192.168.1.100",
        "port": 554,
        "type": "video",
        "protocol": "rtsp",
    }
    network_manager._handle_command("command/network_devices/add", device_data)
    assert len(network_manager.devices) == 1

    # Get first device_id
    device_id = list(network_manager.devices.keys())[0]

    # Test update command
    update_data = {"device_id": device_id, "name": "Updated Camera"}
    network_manager._handle_command("command/network_devices/update", update_data)
    assert network_manager.devices[device_id].name == "Updated Camera"

    # Test remove command
    remove_data = {"device_id": device_id}
    network_manager._handle_command("command/network_devices/remove", remove_data)
    assert len(network_manager.devices) == 0


def test_handle_command_invalid(network_manager):
    # Test invalid command type
    with pytest.raises(ValueError):
        network_manager._handle_command("command/network_devices/invalid", {})

    # Test add command with invalid data
    with pytest.raises(ValueError):
        network_manager._handle_command("command/network_devices/add", {})

    # Test add command with empty strings
    with pytest.raises(ValueError):
        network_manager._handle_command(
            "command/network_devices/add", {"name": "", "ip": "192.168.1.100"}
        )

    with pytest.raises(ValueError):
        network_manager._handle_command(
            "command/network_devices/add", {"name": "Test Camera", "ip": ""}
        )

    # Test update command with nonexistent device
    with pytest.raises(ValueError):
        network_manager._handle_command(
            "command/network_devices/update", {"device_id": "nonexistent"}
        )

    # Test remove command with missing device_id
    with pytest.raises(ValueError):
        network_manager._handle_command("command/network_devices/remove", {})

    # Test remove command with nonexistent device
    with pytest.raises(ValueError):
        network_manager._handle_command(
            "command/network_devices/remove", {"device_id": "nonexistent"}
        )


def test_save_and_load_state(network_manager, temp_dir):
    # Add some devices
    network_manager.add_device(
        name="Camera 1", ip="192.168.1.100", port=554, type="video", protocol="rtsp"
    )
    network_manager.add_device(
        name="Camera 2", ip="192.168.1.101", port=80, type="video", protocol="rtsp"
    )

    # Save state
    state_file = os.path.join(temp_dir, "network_devices.json")
    network_manager.save_state(state_file)

    # Create new manager and load state
    new_manager = NetworkDevicesManager(
        network_manager.config, network_manager.mcp_broker
    )
    new_manager.load_state(state_file)

    # Verify devices were restored
    assert len(new_manager.devices) == 2
    for device_id, device in network_manager.devices.items():
        assert device_id in new_manager.devices
        loaded_device = new_manager.devices[device_id]
        assert loaded_device.name == device.name
        assert loaded_device.ip == device.ip
        assert loaded_device.port == device.port
        assert loaded_device.type == device.type
        assert loaded_device.protocol == device.protocol
