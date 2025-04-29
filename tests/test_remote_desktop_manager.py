"""Tests for remote desktop manager."""

import pytest
import socket
import threading
import time
from unittest.mock import Mock, patch, MagicMock

from rtaspi.device_managers.remote_desktop.manager import RemoteDesktopManager
from rtaspi.device_managers.remote_desktop import RDPDevice, VNCDevice
from rtaspi.constants.devices import (
    DEVICE_TYPE_REMOTE_DESKTOP,
    DEVICE_SUBTYPE_RDP,
    DEVICE_SUBTYPE_VNC,
    DEVICE_PROTOCOL_RDP,
    DEVICE_PROTOCOL_VNC,
)


@pytest.fixture
def manager():
    """Create test remote desktop manager."""
    return RemoteDesktopManager()


@pytest.fixture
def rdp_config():
    """Create test RDP device configuration."""
    return {
        "id": "test-rdp",
        "name": "Test RDP Device",
        "type": DEVICE_TYPE_REMOTE_DESKTOP,
        "subtype": DEVICE_SUBTYPE_RDP,
        "protocol": DEVICE_PROTOCOL_RDP,
        "host": "192.168.1.100",
        "port": 3389,
    }


@pytest.fixture
def vnc_config():
    """Create test VNC device configuration."""
    return {
        "id": "test-vnc",
        "name": "Test VNC Device",
        "type": DEVICE_TYPE_REMOTE_DESKTOP,
        "subtype": DEVICE_SUBTYPE_VNC,
        "protocol": DEVICE_PROTOCOL_VNC,
        "host": "192.168.1.101",
        "port": 5900,
    }


def test_manager_init(manager):
    """Test manager initialization."""
    assert isinstance(manager, RemoteDesktopManager)
    assert not manager._devices
    assert not manager._discovery_thread
    assert not manager._stop_discovery.is_set()


def test_manager_add_device(manager, rdp_config, vnc_config):
    """Test adding devices manually."""
    # Add RDP device
    device = manager.add_device(rdp_config)
    assert device is not None
    assert isinstance(device, RDPDevice)
    assert device.device_id == rdp_config["id"]
    assert len(manager.get_devices()) == 1

    # Add VNC device
    device = manager.add_device(vnc_config)
    assert device is not None
    assert isinstance(device, VNCDevice)
    assert device.device_id == vnc_config["id"]
    assert len(manager.get_devices()) == 2

    # Try to add duplicate device
    device = manager.add_device(rdp_config)
    assert device is None
    assert len(manager.get_devices()) == 2

    # Try to add device with invalid type
    invalid_config = rdp_config.copy()
    invalid_config["id"] = "invalid"
    invalid_config["subtype"] = "invalid"
    device = manager.add_device(invalid_config)
    assert device is None
    assert len(manager.get_devices()) == 2


def test_manager_get_device(manager, rdp_config):
    """Test getting devices."""
    # Add device
    device = manager.add_device(rdp_config)
    assert device is not None

    # Get device
    retrieved = manager.get_device(rdp_config["id"])
    assert retrieved is device

    # Get non-existent device
    assert manager.get_device("non-existent") is None


def test_manager_remove_device(manager, rdp_config):
    """Test removing devices."""
    # Add device
    device = manager.add_device(rdp_config)
    assert device is not None

    # Remove device
    assert manager.remove_device(rdp_config["id"])
    assert not manager.get_devices()

    # Try to remove non-existent device
    assert not manager.remove_device("non-existent")


@patch("socket.socket")
def test_manager_discovery(mock_socket, manager):
    """Test device discovery."""
    # Mock socket for local network detection
    mock_sock = MagicMock()
    mock_sock.getsockname.return_value = ("192.168.1.2", 0)
    mock_socket.return_value = mock_sock

    # Mock port checking
    def mock_connect_ex(addr):
        host, port = addr
        if host == "192.168.1.100" and port == 3389:
            return 0  # RDP port open
        if host == "192.168.1.101" and port == 5900:
            return 0  # VNC port open
        return 1  # Port closed

    mock_sock.connect_ex = mock_connect_ex

    # Start discovery
    manager.start_discovery(["192.168.1.0/24"])
    time.sleep(1)  # Give discovery thread time to run

    # Stop discovery
    manager.stop_discovery()

    # Verify discovered devices
    devices = manager.get_devices()
    assert len(devices) == 2

    rdp_device = manager.get_device("rdp-192.168.1.100")
    assert rdp_device is not None
    assert isinstance(rdp_device, RDPDevice)
    assert rdp_device.host == "192.168.1.100"
    assert rdp_device.port == 3389

    vnc_device = manager.get_device("vnc-192.168.1.101")
    assert vnc_device is not None
    assert isinstance(vnc_device, VNCDevice)
    assert vnc_device.host == "192.168.1.101"
    assert vnc_device.port == 5900


def test_manager_cleanup(manager, rdp_config, vnc_config):
    """Test manager cleanup."""
    # Add devices
    rdp_device = manager.add_device(rdp_config)
    vnc_device = manager.add_device(vnc_config)
    assert rdp_device is not None
    assert vnc_device is not None

    # Mock connected state
    rdp_device._connected = True
    vnc_device._connected = True

    # Start discovery
    manager.start_discovery()
    assert manager._discovery_thread is not None

    # Clean up
    manager.cleanup()

    # Verify cleanup
    assert not manager.get_devices()
    assert not manager._discovery_thread
    assert not rdp_device.is_connected
    assert not vnc_device.is_connected


def test_manager_discovery_already_running(manager):
    """Test starting discovery when already running."""
    # Start discovery
    manager.start_discovery()
    assert manager._discovery_thread is not None

    # Try to start again
    manager.start_discovery()
    # Should log warning but not crash

    # Clean up
    manager.stop_discovery()


@patch("socket.socket")
def test_manager_discovery_network_error(mock_socket, manager):
    """Test device discovery with network error."""
    # Mock socket error
    mock_sock = MagicMock()
    mock_sock.getsockname.side_effect = Exception("Network error")
    mock_socket.return_value = mock_sock

    # Start discovery without networks
    manager.start_discovery()
    time.sleep(1)  # Give discovery thread time to run

    # Stop discovery
    manager.stop_discovery()

    # Verify no devices discovered
    assert not manager.get_devices()


def test_manager_remove_connected_device(manager, rdp_config):
    """Test removing connected device."""
    # Add device
    device = manager.add_device(rdp_config)
    assert device is not None

    # Mock connected state
    device._connected = True

    # Remove device
    assert manager.remove_device(rdp_config["id"])
    assert not manager.get_devices()
    assert not device.is_connected
