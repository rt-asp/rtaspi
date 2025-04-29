"""Tests for remote desktop device implementations."""

import pytest
import threading
import time
from unittest.mock import Mock, patch, MagicMock

from rtaspi.device_managers.remote_desktop import RDPDevice
from rtaspi.device_managers.remote_desktop.capture import WindowCapture
from rtaspi.constants.devices import (
    DEVICE_TYPE_REMOTE_DESKTOP,
    DEVICE_SUBTYPE_RDP,
    DEVICE_PROTOCOL_RDP,
    CAPABILITY_VIDEO,
    CAPABILITY_KEYBOARD,
    CAPABILITY_MOUSE,
)


@pytest.fixture
def rdp_config():
    """Create test RDP device configuration."""
    return {
        "id": "test-rdp",
        "name": "Test RDP Device",
        "type": DEVICE_TYPE_REMOTE_DESKTOP,
        "subtype": DEVICE_SUBTYPE_RDP,
        "protocol": DEVICE_PROTOCOL_RDP,
        "host": "test-server",
        "port": 3389,
        "username": "test-user",
        "password": "test-pass",
        "domain": "test-domain",
        "width": 1920,
        "height": 1080,
        "refresh_rate": 30,
        "capabilities": [CAPABILITY_VIDEO, CAPABILITY_KEYBOARD, CAPABILITY_MOUSE],
    }


@pytest.fixture
def rdp_device(rdp_config):
    """Create test RDP device instance."""
    return RDPDevice("test-rdp", rdp_config)


def test_rdp_device_init(rdp_device, rdp_config):
    """Test RDP device initialization."""
    assert rdp_device.device_id == rdp_config["id"]
    assert rdp_device.host == rdp_config["host"]
    assert rdp_device.port == rdp_config["port"]
    assert rdp_device.username == rdp_config["username"]
    assert rdp_device.password == rdp_config["password"]
    assert rdp_device.domain == rdp_config["domain"]
    assert rdp_device.width == rdp_config["width"]
    assert rdp_device.height == rdp_config["height"]
    assert rdp_device.refresh_rate == rdp_config["refresh_rate"]
    assert not rdp_device.is_connected


@patch("subprocess.Popen")
@patch.object(WindowCapture, "initialize")
@patch.object(WindowCapture, "find_window_by_name")
def test_rdp_device_connect(mock_find_window, mock_init, mock_popen, rdp_device):
    """Test RDP device connection."""
    # Mock successful process start and window capture
    mock_process = Mock()
    mock_process.poll.return_value = None
    mock_popen.return_value = mock_process
    mock_init.return_value = True
    mock_find_window.return_value = True

    # Test connection
    assert rdp_device.connect()
    assert rdp_device.is_connected
    assert rdp_device._process is not None

    # Verify FreeRDP command
    mock_popen.assert_called_once()
    cmd_args = mock_popen.call_args[0][0]
    assert "xfreerdp" in cmd_args
    assert f"/v:{rdp_device.host}" in cmd_args
    assert f"/u:{rdp_device.username}" in cmd_args
    assert f"/p:{rdp_device.password}" in cmd_args
    assert f"/w:{rdp_device.width}" in cmd_args
    assert f"/h:{rdp_device.height}" in cmd_args

    # Verify window capture initialization
    mock_init.assert_called_once()
    mock_find_window.assert_called_with("FreeRDP")


@patch("subprocess.Popen")
@patch.object(WindowCapture, "initialize")
def test_rdp_device_connect_failure(mock_init, mock_popen, rdp_device):
    """Test RDP device connection failure."""
    # Mock failed process start
    mock_process = Mock()
    mock_process.poll.return_value = 1
    mock_process.stderr.read.return_value = b"Connection failed"
    mock_popen.return_value = mock_process

    # Test connection
    assert not rdp_device.connect()
    assert not rdp_device.is_connected


@patch.object(WindowCapture, "cleanup")
def test_rdp_device_disconnect(mock_cleanup, rdp_device):
    """Test RDP device disconnection."""
    # Mock connected state
    rdp_device._process = Mock()
    rdp_device._connected = True
    rdp_device._capture_thread = Mock()
    rdp_device._window_capture = Mock()

    # Test disconnection
    rdp_device.disconnect()
    assert not rdp_device.is_connected
    assert rdp_device._process is None
    assert rdp_device._capture_thread is None
    mock_cleanup.assert_called_once()


@patch.object(WindowCapture, "capture_window")
def test_rdp_device_get_frame(mock_capture, rdp_device):
    """Test RDP device frame capture."""
    test_frame = b"test frame data"
    mock_capture.return_value = test_frame

    # Mock window capture initialization
    rdp_device._window_capture = MagicMock()
    rdp_device._window_capture.initialize.return_value = True
    rdp_device._window_capture.find_window_by_name.return_value = True
    rdp_device._window_capture.capture_window.return_value = test_frame

    # Start capture thread
    rdp_device._stop_capture.clear()
    rdp_device._capture_thread = threading.Thread(target=rdp_device._capture_frames)
    rdp_device._capture_thread.daemon = True
    rdp_device._capture_thread.start()

    # Give thread time to capture frame
    time.sleep(0.1)

    assert rdp_device.get_frame() == test_frame

    # Cleanup
    rdp_device._stop_capture.set()
    rdp_device._capture_thread.join()


def test_rdp_device_send_mouse_event(rdp_device):
    """Test RDP device mouse event handling."""
    # Mock connected state
    rdp_device._connected = True

    # Test mouse events
    rdp_device.send_mouse_event(100, 200, button=0, pressed=True)
    rdp_device.send_mouse_event(150, 250, button=1, pressed=False)

    # Test when disconnected
    rdp_device._connected = False
    rdp_device.send_mouse_event(100, 200)  # Should not raise exception


def test_rdp_device_send_key_event(rdp_device):
    """Test RDP device keyboard event handling."""
    # Mock connected state
    rdp_device._connected = True

    # Test key events
    rdp_device.send_key_event(65, pressed=True)  # 'A' key press
    rdp_device.send_key_event(65, pressed=False)  # 'A' key release

    # Test when disconnected
    rdp_device._connected = False
    rdp_device.send_key_event(65)  # Should not raise exception


def test_rdp_device_resolution(rdp_device):
    """Test RDP device resolution handling."""
    # Test get resolution
    width, height = rdp_device.get_resolution()
    assert width == rdp_device.width
    assert height == rdp_device.height

    # Test set resolution
    new_width, new_height = 1280, 720
    assert rdp_device.set_resolution(new_width, new_height)
    assert rdp_device.width == new_width
    assert rdp_device.height == new_height


def test_rdp_device_refresh_rate(rdp_device):
    """Test RDP device refresh rate handling."""
    # Test get refresh rate
    assert rdp_device.get_refresh_rate() == rdp_device.refresh_rate

    # Test set refresh rate
    new_rate = 60
    assert rdp_device.set_refresh_rate(new_rate)
    assert rdp_device.refresh_rate == new_rate

    # Test invalid refresh rate
    assert not rdp_device.set_refresh_rate(0)
    assert not rdp_device.set_refresh_rate(-1)
