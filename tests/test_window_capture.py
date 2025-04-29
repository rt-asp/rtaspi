"""Tests for X11 window capture utility."""

import pytest
from unittest.mock import Mock, patch, MagicMock

import Xlib
from Xlib import X, display
from Xlib.ext import composite
import numpy as np

from rtaspi.device_managers.remote_desktop.capture import WindowCapture


@pytest.fixture
def window_capture():
    """Create test window capture instance."""
    return WindowCapture()


@patch("Xlib.display.Display")
def test_window_capture_initialize(mock_display, window_capture):
    """Test window capture initialization."""
    # Mock X11 display and composite extension
    mock_display_instance = Mock()
    mock_display_instance.has_extension.return_value = True
    mock_display_instance.screen.return_value.root = Mock()
    mock_display.return_value = mock_display_instance

    # Test initialization
    assert window_capture.initialize()
    assert window_capture._display is not None
    assert window_capture._composite_initialized

    # Verify composite extension check
    mock_display_instance.has_extension.assert_called_once_with("Composite")


@patch("Xlib.display.Display")
def test_window_capture_initialize_no_composite(mock_display, window_capture):
    """Test window capture initialization without composite extension."""
    # Mock X11 display without composite extension
    mock_display_instance = Mock()
    mock_display_instance.has_extension.return_value = False
    mock_display.return_value = mock_display_instance

    # Test initialization
    assert not window_capture.initialize()
    assert not window_capture._composite_initialized


@patch("Xlib.display.Display")
def test_window_capture_find_window(mock_display, window_capture):
    """Test window search functionality."""
    # Mock X11 display and window list
    mock_display_instance = Mock()
    mock_root = Mock()
    mock_window = Mock()
    mock_window.get_wm_name.return_value = "Test Window"
    mock_window.get_geometry.return_value = Mock(width=1920, height=1080)

    mock_root.get_full_property.return_value.value = [1]  # Window ID
    mock_display_instance.screen.return_value.root = mock_root
    mock_display_instance.create_resource_object.return_value = mock_window
    mock_display_instance.intern_atom.return_value = "_NET_CLIENT_LIST"
    mock_display.return_value = mock_display_instance

    # Initialize window capture
    window_capture._display = mock_display_instance

    # Test window search
    assert window_capture.find_window_by_name("Test")
    assert window_capture._window is not None
    assert window_capture._window_geometry is not None


@patch("Xlib.display.Display")
def test_window_capture_find_window_not_found(mock_display, window_capture):
    """Test window search when window not found."""
    # Mock X11 display with no matching windows
    mock_display_instance = Mock()
    mock_root = Mock()
    mock_window = Mock()
    mock_window.get_wm_name.return_value = "Other Window"

    mock_root.get_full_property.return_value.value = [1]  # Window ID
    mock_display_instance.screen.return_value.root = mock_root
    mock_display_instance.create_resource_object.return_value = mock_window
    mock_display_instance.intern_atom.return_value = "_NET_CLIENT_LIST"
    mock_display.return_value = mock_display_instance

    # Initialize window capture
    window_capture._display = mock_display_instance

    # Test window search
    assert not window_capture.find_window_by_name("Test")
    assert window_capture._window is None
    assert window_capture._window_geometry is None


@patch("cv2.imencode")
def test_window_capture_get_frame(mock_imencode, window_capture):
    """Test frame capture functionality."""
    # Mock window and image data
    mock_window = Mock()
    mock_geometry = Mock(width=100, height=100)
    mock_image = Mock()
    mock_image.data = np.zeros((100, 100, 4), dtype=np.uint8)

    window_capture._window = mock_window
    window_capture._window_geometry = mock_geometry
    window_capture._window.get_image.return_value = mock_image

    # Mock image encoding
    mock_imencode.return_value = (True, np.array([1, 2, 3]))

    # Test frame capture
    frame = window_capture.capture_window()
    assert frame is not None
    assert isinstance(frame, bytes)

    # Verify image capture and encoding
    window_capture._window.get_image.assert_called_once()
    mock_imencode.assert_called_once()


def test_window_capture_get_frame_no_window(window_capture):
    """Test frame capture without window."""
    assert window_capture.capture_window() is None


def test_window_capture_cleanup(window_capture):
    """Test cleanup functionality."""
    # Mock display
    mock_display = Mock()
    window_capture._display = mock_display
    window_capture._window = Mock()
    window_capture._window_geometry = Mock()
    window_capture._composite_initialized = True

    # Test cleanup
    window_capture.cleanup()

    # Verify cleanup
    mock_display.close.assert_called_once()
    assert window_capture._display is None
    assert window_capture._window is None
    assert window_capture._window_geometry is None
    assert not window_capture._composite_initialized


def test_window_capture_get_window_size(window_capture):
    """Test window size retrieval."""
    # Test without window
    assert window_capture.get_window_size() is None

    # Test with window
    mock_geometry = Mock(width=1920, height=1080)
    window_capture._window_geometry = mock_geometry
    size = window_capture.get_window_size()
    assert size == (1920, 1080)
