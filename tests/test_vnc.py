"""Tests for VNC device implementation."""

import pytest
import threading
import time
from unittest.mock import Mock, patch, MagicMock

from rtaspi.device_managers.remote_desktop import VNCDevice
from rtaspi.device_managers.remote_desktop.vnc import (
    ENCODING_TIGHT,
    ENCODING_RAW,
    ENCODING_ZLIB,
    AUTH_VNC,
    AUTH_NONE,
)
from rtaspi.device_managers.remote_desktop.capture import WindowCapture
from rtaspi.constants.devices import (
    DEVICE_TYPE_REMOTE_DESKTOP,
    DEVICE_SUBTYPE_VNC,
    DEVICE_PROTOCOL_VNC,
    CAPABILITY_VIDEO,
    CAPABILITY_KEYBOARD,
    CAPABILITY_MOUSE,
)


@pytest.fixture
def vnc_config():
    """Create test VNC device configuration."""
    return {
        "id": "test-vnc",
        "name": "Test VNC Device",
        "type": DEVICE_TYPE_REMOTE_DESKTOP,
        "subtype": DEVICE_SUBTYPE_VNC,
        "protocol": DEVICE_PROTOCOL_VNC,
        "host": "test-server",
        "port": 5900,
        "username": "test-user",
        "password": "test-pass",
        "width": 1920,
        "height": 1080,
        "refresh_rate": 30,
        "encoding": ENCODING_TIGHT,
        "quality": 8,
        "compression": 6,
        "capabilities": [CAPABILITY_VIDEO, CAPABILITY_KEYBOARD, CAPABILITY_MOUSE],
    }


@pytest.fixture
def vnc_device(vnc_config):
    """Create test VNC device instance."""
    return VNCDevice("test-vnc", vnc_config)


def test_vnc_device_init(vnc_device, vnc_config):
    """Test VNC device initialization."""
    assert vnc_device.device_id == vnc_config["id"]
    assert vnc_device.host == vnc_config["host"]
    assert vnc_device.port == vnc_config["port"]
    assert vnc_device.username == vnc_config["username"]
    assert vnc_device.password == vnc_config["password"]
    assert vnc_device.width == vnc_config["width"]
    assert vnc_device.height == vnc_config["height"]
    assert vnc_device.refresh_rate == vnc_config["refresh_rate"]
    assert vnc_device.encoding == vnc_config["encoding"]
    assert vnc_device.quality == vnc_config["quality"]
    assert vnc_device.compression == vnc_config["compression"]
    assert not vnc_device.is_connected


@patch("subprocess.Popen")
@patch.object(WindowCapture, "initialize")
@patch.object(WindowCapture, "find_window_by_name")
def test_vnc_device_connect(mock_find_window, mock_init, mock_popen, vnc_device):
    """Test VNC device connection."""
    # Mock successful process start and window capture
    mock_process = Mock()
    mock_process.poll.return_value = None
    mock_popen.return_value = mock_process
    mock_init.return_value = True
    mock_find_window.return_value = True

    # Test connection
    assert vnc_device.connect()
    assert vnc_device.is_connected
    assert vnc_device._process is not None

    # Verify vncviewer command
    mock_popen.assert_called_once()
    cmd_args = mock_popen.call_args[0][0]
    assert "vncviewer" in cmd_args
    assert f"{vnc_device.host}:{vnc_device.port}" in cmd_args
    assert f"-passwd={vnc_device.password}" in cmd_args
    assert f"-encodings={vnc_device.encoding}" in cmd_args
    assert f"-quality={vnc_device.quality}" in cmd_args
    assert f"-compresslevel={vnc_device.compression}" in cmd_args
    assert f"-geometry={vnc_device.width}x{vnc_device.height}" in cmd_args

    # Verify window capture initialization
    mock_init.assert_called_once()
    mock_find_window.assert_called_with("TightVNC")


@patch("subprocess.Popen")
@patch.object(WindowCapture, "initialize")
def test_vnc_device_connect_failure(mock_init, mock_popen, vnc_device):
    """Test VNC device connection failure."""
    # Mock failed process start
    mock_process = Mock()
    mock_process.poll.return_value = 1
    mock_process.stderr.read.return_value = b"Connection failed"
    mock_popen.return_value = mock_process

    # Test connection
    assert not vnc_device.connect()
    assert not vnc_device.is_connected


@patch.object(WindowCapture, "cleanup")
def test_vnc_device_disconnect(mock_cleanup, vnc_device):
    """Test VNC device disconnection."""
    # Mock connected state
    vnc_device._process = Mock()
    vnc_device._connected = True
    vnc_device._capture_thread = Mock()
    vnc_device._window_capture = Mock()

    # Test disconnection
    vnc_device.disconnect()
    assert not vnc_device.is_connected
    assert vnc_device._process is None
    assert vnc_device._capture_thread is None
    mock_cleanup.assert_called_once()


@patch.object(WindowCapture, "capture_window")
def test_vnc_device_get_frame(mock_capture, vnc_device):
    """Test VNC device frame capture."""
    test_frame = b"test frame data"
    mock_capture.return_value = test_frame

    # Mock window capture initialization
    vnc_device._window_capture = MagicMock()
    vnc_device._window_capture.initialize.return_value = True
    vnc_device._window_capture.find_window_by_name.return_value = True
    vnc_device._window_capture.capture_window.return_value = test_frame

    # Start capture thread
    vnc_device._stop_capture.clear()
    vnc_device._capture_thread = threading.Thread(target=vnc_device._capture_frames)
    vnc_device._capture_thread.daemon = True
    vnc_device._capture_thread.start()

    # Give thread time to capture frame
    time.sleep(0.1)

    assert vnc_device.get_frame() == test_frame

    # Cleanup
    vnc_device._stop_capture.set()
    vnc_device._capture_thread.join()


def test_vnc_device_send_mouse_event(vnc_device):
    """Test VNC device mouse event handling."""
    # Mock connected state
    vnc_device._connected = True

    # Test mouse events
    vnc_device.send_mouse_event(100, 200, button=0, pressed=True)
    vnc_device.send_mouse_event(150, 250, button=1, pressed=False)

    # Test when disconnected
    vnc_device._connected = False
    vnc_device.send_mouse_event(100, 200)  # Should not raise exception


def test_vnc_device_send_key_event(vnc_device):
    """Test VNC device keyboard event handling."""
    # Mock connected state
    vnc_device._connected = True

    # Test key events
    vnc_device.send_key_event(65, pressed=True)  # 'A' key press
    vnc_device.send_key_event(65, pressed=False)  # 'A' key release

    # Test when disconnected
    vnc_device._connected = False
    vnc_device.send_key_event(65)  # Should not raise exception


def test_vnc_device_resolution(vnc_device):
    """Test VNC device resolution handling."""
    # Test get resolution
    width, height = vnc_device.get_resolution()
    assert width == vnc_device.width
    assert height == vnc_device.height

    # Test set resolution
    new_width, new_height = 1280, 720
    assert vnc_device.set_resolution(new_width, new_height)
    assert vnc_device.width == new_width
    assert vnc_device.height == new_height


def test_vnc_device_refresh_rate(vnc_device):
    """Test VNC device refresh rate handling."""
    # Test get refresh rate
    assert vnc_device.get_refresh_rate() == vnc_device.refresh_rate

    # Test set refresh rate
    new_rate = 60
    assert vnc_device.set_refresh_rate(new_rate)
    assert vnc_device.refresh_rate == new_rate

    # Test invalid refresh rate
    assert not vnc_device.set_refresh_rate(0)
    assert not vnc_device.set_refresh_rate(-1)


def test_vnc_device_encoding(vnc_device):
    """Test VNC encoding settings."""
    # Test set encoding
    assert vnc_device.set_encoding(ENCODING_RAW)
    assert vnc_device.encoding == ENCODING_RAW

    assert vnc_device.set_encoding(ENCODING_ZLIB)
    assert vnc_device.encoding == ENCODING_ZLIB


def test_vnc_device_quality(vnc_device):
    """Test VNC quality settings."""
    # Test set quality
    assert vnc_device.set_quality(5)
    assert vnc_device.quality == 5

    # Test invalid quality
    assert not vnc_device.set_quality(-1)
    assert not vnc_device.set_quality(10)


def test_vnc_device_compression(vnc_device):
    """Test VNC compression settings."""
    # Test set compression
    assert vnc_device.set_compression(3)
    assert vnc_device.compression == 3

    # Test invalid compression
    assert not vnc_device.set_compression(-1)
    assert not vnc_device.set_compression(10)
