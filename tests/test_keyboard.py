"""Tests for virtual keyboard implementation."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import platform

from rtaspi.input.keyboard import VirtualKeyboard, LinuxKeyboard, WindowsKeyboard, MacOSKeyboard


@pytest.fixture
def keyboard():
    """Create test virtual keyboard."""
    return VirtualKeyboard()


def test_keyboard_backend_selection():
    """Test keyboard backend selection based on platform."""
    with patch('platform.system') as mock_system:
        # Test Linux
        mock_system.return_value = 'Linux'
        with patch('uinput.Device') as mock_device:
            keyboard = VirtualKeyboard()
            assert isinstance(keyboard._backend, LinuxKeyboard)

        # Test Windows
        mock_system.return_value = 'Windows'
        with patch('win32api'):
            keyboard = VirtualKeyboard()
            assert isinstance(keyboard._backend, WindowsKeyboard)

        # Test macOS
        mock_system.return_value = 'Darwin'
        with patch('Quartz.CGEventCreateKeyboardEvent'):
            keyboard = VirtualKeyboard()
            assert isinstance(keyboard._backend, MacOSKeyboard)

        # Test unsupported platform
        mock_system.return_value = 'Unknown'
        keyboard = VirtualKeyboard()
        assert keyboard._backend is None


def test_keyboard_initialization(keyboard):
    """Test keyboard initialization."""
    # Mock backend
    mock_backend = Mock()
    mock_backend.initialize.return_value = True
    keyboard._backend = mock_backend

    # Test initialization
    assert keyboard.initialize()
    assert keyboard._initialized
    mock_backend.initialize.assert_called_once()

    # Test initialization failure
    mock_backend.initialize.return_value = False
    keyboard._initialized = False
    assert not keyboard.initialize()
    assert not keyboard._initialized

    # Test initialization without backend
    keyboard._backend = None
    assert not keyboard.initialize()


def test_keyboard_cleanup(keyboard):
    """Test keyboard cleanup."""
    # Mock backend
    mock_backend = Mock()
    keyboard._backend = mock_backend
    keyboard._initialized = True

    # Test cleanup
    keyboard.cleanup()
    mock_backend.cleanup.assert_called_once()
    assert not keyboard._initialized

    # Test cleanup error
    mock_backend.cleanup.side_effect = Exception("Test error")
    keyboard._initialized = True
    keyboard.cleanup()  # Should log error but not raise
    assert not keyboard._initialized


def test_keyboard_type_text(keyboard):
    """Test text typing."""
    # Mock backend
    mock_backend = Mock()
    keyboard._backend = mock_backend
    keyboard._initialized = True

    # Test typing text
    keyboard.type_text("Hello")
    assert mock_backend.type_char.call_count == 5
    mock_backend.type_char.assert_any_call("H")
    mock_backend.type_char.assert_any_call("e")
    mock_backend.type_char.assert_any_call("l")
    mock_backend.type_char.assert_any_call("o")

    # Test typing with delay
    mock_backend.reset_mock()
    with patch('time.sleep') as mock_sleep:
        keyboard.type_text("Hi", delay=0.1)
        assert mock_backend.type_char.call_count == 2
        assert mock_sleep.call_count == 2
        mock_sleep.assert_called_with(0.1)

    # Test typing without initialization
    keyboard._initialized = False
    mock_backend.reset_mock()
    keyboard.type_text("Test")
    mock_backend.type_char.assert_not_called()


def test_keyboard_key_events(keyboard):
    """Test key press and release events."""
    # Mock backend
    mock_backend = Mock()
    keyboard._backend = mock_backend
    keyboard._initialized = True

    # Test key press
    keyboard.press_key('a')
    mock_backend.press_key.assert_called_once_with('a')
    assert not keyboard._modifiers

    # Test modifier key press
    keyboard.press_key('shift')
    mock_backend.press_key.assert_called_with('shift')
    assert 'shift' in keyboard._modifiers

    # Test key release
    keyboard.release_key('a')
    mock_backend.release_key.assert_called_with('a')
    assert 'shift' in keyboard._modifiers

    # Test modifier key release
    keyboard.release_key('shift')
    mock_backend.release_key.assert_called_with('shift')
    assert not keyboard._modifiers

    # Test key tap
    mock_backend.reset_mock()
    keyboard.tap_key('a')
    mock_backend.press_key.assert_called_once_with('a')
    mock_backend.release_key.assert_called_once_with('a')


def test_linux_keyboard():
    """Test Linux keyboard implementation."""
    with patch('uinput.Device') as mock_device:
        keyboard = LinuxKeyboard()
        
        # Test initialization
        assert keyboard.initialize()
        mock_device.assert_called_once()
        
        # Test key events
        keyboard._device = Mock()
        keyboard.type_char('a')
        keyboard._device.emit.assert_called()
        
        # Test cleanup
        keyboard.cleanup()
        keyboard._device.destroy.assert_called_once()


def test_windows_keyboard():
    """Test Windows keyboard implementation."""
    with patch('win32api.keybd_event') as mock_event:
        keyboard = WindowsKeyboard()
        
        # Test initialization
        assert keyboard.initialize()
        
        # Test key events
        keyboard.type_char('a')
        assert mock_event.call_count > 0
        
        # Test cleanup (no-op)
        keyboard.cleanup()


def test_macos_keyboard():
    """Test macOS keyboard implementation."""
    with patch('Quartz.CGEventCreateKeyboardEvent') as mock_event:
        keyboard = MacOSKeyboard()
        
        # Test initialization
        with patch('Quartz.kCGEventSourceStatePrivate'):
            assert keyboard.initialize()
        
        # Test key events
        with patch('Quartz.CGEventPost'):
            keyboard.type_char('a')
            assert mock_event.call_count > 0
        
        # Test cleanup (no-op)
        keyboard.cleanup()


def test_keyboard_error_handling(keyboard):
    """Test error handling."""
    # Mock backend with errors
    mock_backend = Mock()
    mock_backend.type_char.side_effect = Exception("Test error")
    mock_backend.press_key.side_effect = Exception("Test error")
    mock_backend.release_key.side_effect = Exception("Test error")
    keyboard._backend = mock_backend
    keyboard._initialized = True

    # Test error handling
    keyboard.type_text("test")  # Should log error but not raise
    keyboard.press_key('a')  # Should log error but not raise
    keyboard.release_key('a')  # Should log error but not raise


def test_keyboard_modifiers(keyboard):
    """Test modifier key tracking."""
    # Mock backend
    mock_backend = Mock()
    keyboard._backend = mock_backend
    keyboard._initialized = True

    # Test modifier tracking
    assert not keyboard.get_active_modifiers()

    keyboard.press_key('shift')
    assert 'shift' in keyboard.get_active_modifiers()

    keyboard.press_key('ctrl')
    assert 'ctrl' in keyboard.get_active_modifiers()
    assert len(keyboard.get_active_modifiers()) == 2

    keyboard.release_key('shift')
    assert 'ctrl' in keyboard.get_active_modifiers()
    assert 'shift' not in keyboard.get_active_modifiers()

    keyboard.release_key('ctrl')
    assert not keyboard.get_active_modifiers()
