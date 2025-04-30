"""
Tests for the network device module.
"""

import pytest
from rtaspi_devices.network import NetworkDevice
from rtaspi_devices.base.device import DeviceStatus


def test_device_initialization():
    """Test device initialization."""
    device = NetworkDevice(
        device_id="192.168.1.100:554",
        name="Test Camera",
        type="video",
        ip="192.168.1.100",
        port=554,
        protocol="rtsp"
    )
    assert device.device_id == "192.168.1.100:554"
    assert device.name == "Test Camera"
    assert device.type == "video"
    assert device.ip == "192.168.1.100"
    assert device.port == 554
    assert device.protocol == "rtsp"
    assert device.status == DeviceStatus.UNKNOWN
    assert device.streams == {}


def test_device_base_url():
    """Test device base URL generation."""
    # Without credentials
    device = NetworkDevice(
        device_id="192.168.1.100:554",
        name="Test Camera",
        type="video",
        ip="192.168.1.100",
        port=554,
        protocol="rtsp"
    )
    assert device.get_base_url() == "rtsp://192.168.1.100:554"

    # With username only
    device = NetworkDevice(
        device_id="192.168.1.100:554",
        name="Test Camera",
        type="video",
        ip="192.168.1.100",
        port=554,
        protocol="rtsp",
        username="admin"
    )
    assert device.get_base_url() == "rtsp://admin@192.168.1.100:554"

    # With username and password
    device = NetworkDevice(
        device_id="192.168.1.100:554",
        name="Test Camera",
        type="video",
        ip="192.168.1.100",
        port=554,
        protocol="rtsp",
        username="admin",
        password="secret"
    )
    assert device.get_base_url() == "rtsp://admin:secret@192.168.1.100:554"


def test_device_stream_management():
    """Test device stream management."""
    device = NetworkDevice(
        device_id="192.168.1.100:554",
        name="Test Camera",
        type="video",
        ip="192.168.1.100",
        port=554,
        protocol="rtsp"
    )

    # Add stream
    device.add_stream("main", "/stream1")
    assert device.streams == {"main": "/stream1"}
    assert device.get_stream_url("main") == "/stream1"

    # Add another stream
    device.add_stream("sub", "/stream2")
    assert device.streams == {"main": "/stream1", "sub": "/stream2"}
    assert device.get_stream_url("sub") == "/stream2"

    # Remove stream
    device.remove_stream("main")
    assert device.streams == {"sub": "/stream2"}
    assert device.get_stream_url("main") is None

    # Remove non-existent stream
    device.remove_stream("unknown")
    assert device.streams == {"sub": "/stream2"}


def test_device_to_dict():
    """Test device serialization."""
    device = NetworkDevice(
        device_id="192.168.1.100:554",
        name="Test Camera",
        type="video",
        ip="192.168.1.100",
        port=554,
        protocol="rtsp",
        username="admin",
        password="secret"
    )
    device.add_stream("main", "/stream1")
    device.status = DeviceStatus.ONLINE

    data = device.to_dict()
    assert data["id"] == "192.168.1.100:554"
    assert data["name"] == "Test Camera"
    assert data["type"] == "video"
    assert data["ip"] == "192.168.1.100"
    assert data["port"] == 554
    assert data["protocol"] == "rtsp"
    assert data["status"] == "online"
    assert data["streams"] == {"main": "/stream1"}
    # Ensure sensitive data is not included
    assert "username" not in data
    assert "password" not in data


def test_device_validation():
    """Test device validation."""
    # Invalid type
    with pytest.raises(ValueError):
        NetworkDevice(
            device_id="192.168.1.100:554",
            name="Test Camera",
            type="invalid",
            ip="192.168.1.100",
            port=554,
            protocol="rtsp"
        )

    # Invalid protocol
    with pytest.raises(ValueError):
        NetworkDevice(
            device_id="192.168.1.100:554",
            name="Test Camera",
            type="video",
            ip="192.168.1.100",
            port=554,
            protocol="invalid"
        )

    # Invalid port
    with pytest.raises(ValueError):
        NetworkDevice(
            device_id="192.168.1.100:554",
            name="Test Camera",
            type="video",
            ip="192.168.1.100",
            port=70000,
            protocol="rtsp"
        )

    # Invalid IP
    with pytest.raises(ValueError):
        NetworkDevice(
            device_id="invalid:554",
            name="Test Camera",
            type="video",
            ip="invalid",
            port=554,
            protocol="rtsp"
        )
