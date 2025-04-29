"""Virtual keyboard device implementation."""

import logging
import time
from typing import Dict, Optional, List
import platform

from ..core.logging import get_logger

logger = get_logger(__name__)

class VirtualKeyboard:
    """Virtual keyboard device for sending keystrokes."""

    def __init__(self):
        """Initialize virtual keyboard."""
        self._backend = self._get_backend()
        self._initialized = False
        self._modifiers = set()  # Currently held modifier keys

    def _get_backend(self):
        """Get appropriate keyboard backend for current platform."""
        system = platform.system().lower()
        
        if system == 'linux':
            try:
                import uinput
                return LinuxKeyboard()
            except ImportError:
                logger.error("Failed to import uinput. Install python-uinput package.")
                return None
                
        elif system == 'windows':
            try:
                import win32api
                import win32con
                return WindowsKeyboard()
            except ImportError:
                logger.error("Failed to import win32api. Install pywin32 package.")
                return None
                
        elif system == 'darwin':
            try:
                from Quartz import (
                    CGEventCreateKeyboardEvent,
                    CGEventPost,
                    kCGHIDEventTap,
                    kCGEventSourceStatePrivate
                )
                return MacOSKeyboard()
            except ImportError:
                logger.error("Failed to import Quartz. Install pyobjc-framework-Quartz package.")
                return None
                
        else:
            logger.error(f"Unsupported platform: {system}")
            return None

    def initialize(self) -> bool:
        """Initialize virtual keyboard device.
        
        Returns:
            bool: True if initialization successful
        """
        if self._initialized:
            return True

        if not self._backend:
            logger.error("No keyboard backend available")
            return False

        try:
            success = self._backend.initialize()
            if success:
                self._initialized = True
                logger.info("Virtual keyboard initialized")
            return success
        except Exception as e:
            logger.error(f"Failed to initialize virtual keyboard: {e}")
            return False

    def cleanup(self) -> None:
        """Clean up keyboard resources."""
        if self._initialized and self._backend:
            try:
                self._backend.cleanup()
                self._initialized = False
                logger.info("Virtual keyboard cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up virtual keyboard: {e}")

    def type_text(self, text: str, delay: float = 0.0) -> None:
        """Type text string.
        
        Args:
            text: Text to type
            delay: Delay between keystrokes in seconds
        """
        if not self._initialized:
            logger.error("Virtual keyboard not initialized")
            return

        try:
            for char in text:
                self._backend.type_char(char)
                if delay > 0:
                    time.sleep(delay)
        except Exception as e:
            logger.error(f"Error typing text: {e}")

    def press_key(self, key: str) -> None:
        """Press and hold key.
        
        Args:
            key: Key to press (e.g., 'a', 'shift', 'ctrl')
        """
        if not self._initialized:
            logger.error("Virtual keyboard not initialized")
            return

        try:
            if key.lower() in ['shift', 'ctrl', 'alt', 'meta']:
                self._modifiers.add(key.lower())
            self._backend.press_key(key)
        except Exception as e:
            logger.error(f"Error pressing key: {e}")

    def release_key(self, key: str) -> None:
        """Release held key.
        
        Args:
            key: Key to release
        """
        if not self._initialized:
            logger.error("Virtual keyboard not initialized")
            return

        try:
            if key.lower() in self._modifiers:
                self._modifiers.remove(key.lower())
            self._backend.release_key(key)
        except Exception as e:
            logger.error(f"Error releasing key: {e}")

    def tap_key(self, key: str) -> None:
        """Tap key (press and release).
        
        Args:
            key: Key to tap
        """
        self.press_key(key)
        self.release_key(key)

    def get_active_modifiers(self) -> List[str]:
        """Get list of currently held modifier keys.
        
        Returns:
            List[str]: List of modifier keys
        """
        return list(self._modifiers)


class LinuxKeyboard:
    """Linux virtual keyboard implementation using uinput."""

    def __init__(self):
        """Initialize Linux keyboard."""
        self._device = None
        self._key_mapping = self._create_key_mapping()

    def initialize(self) -> bool:
        """Initialize uinput device.
        
        Returns:
            bool: True if initialization successful
        """
        try:
            import uinput
            events = []
            for code in self._key_mapping.values():
                if isinstance(code, int):
                    events.append(code)
            self._device = uinput.Device(events)
            return True
        except Exception as e:
            logger.error(f"Failed to initialize uinput device: {e}")
            return False

    def cleanup(self) -> None:
        """Clean up uinput device."""
        if self._device:
            self._device.destroy()
            self._device = None

    def type_char(self, char: str) -> None:
        """Type single character.
        
        Args:
            char: Character to type
        """
        if not self._device:
            return

        key_code = self._key_mapping.get(char.lower())
        if key_code:
            if char.isupper():
                self._device.emit(self._key_mapping['shift'], 1)
            self._device.emit(key_code, 1)
            self._device.emit(key_code, 0)
            if char.isupper():
                self._device.emit(self._key_mapping['shift'], 0)

    def press_key(self, key: str) -> None:
        """Press key.
        
        Args:
            key: Key to press
        """
        if not self._device:
            return

        key_code = self._key_mapping.get(key.lower())
        if key_code:
            self._device.emit(key_code, 1)

    def release_key(self, key: str) -> None:
        """Release key.
        
        Args:
            key: Key to release
        """
        if not self._device:
            return

        key_code = self._key_mapping.get(key.lower())
        if key_code:
            self._device.emit(key_code, 0)

    def _create_key_mapping(self) -> Dict[str, int]:
        """Create mapping of characters to uinput key codes.
        
        Returns:
            Dict[str, int]: Character to key code mapping
        """
        try:
            import uinput
            return {
                'a': uinput.KEY_A,
                'b': uinput.KEY_B,
                # ... add all keys
                'shift': uinput.KEY_LEFTSHIFT,
                'ctrl': uinput.KEY_LEFTCTRL,
                'alt': uinput.KEY_LEFTALT,
                'meta': uinput.KEY_LEFTMETA
            }
        except ImportError:
            return {}


class WindowsKeyboard:
    """Windows virtual keyboard implementation using win32api."""

    def __init__(self):
        """Initialize Windows keyboard."""
        self._key_mapping = self._create_key_mapping()

    def initialize(self) -> bool:
        """Initialize Windows keyboard.
        
        Returns:
            bool: True if initialization successful
        """
        try:
            import win32api
            return True
        except ImportError:
            return False

    def cleanup(self) -> None:
        """Clean up Windows keyboard."""
        pass  # No cleanup needed

    def type_char(self, char: str) -> None:
        """Type single character.
        
        Args:
            char: Character to type
        """
        try:
            import win32api
            import win32con
            vk, is_shift = self._key_mapping.get(char.lower(), (None, False))
            if vk:
                if char.isupper() or is_shift:
                    win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)
                win32api.keybd_event(vk, 0, 0, 0)
                win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
                if char.isupper() or is_shift:
                    win32api.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)
        except Exception as e:
            logger.error(f"Error typing character: {e}")

    def press_key(self, key: str) -> None:
        """Press key.
        
        Args:
            key: Key to press
        """
        try:
            import win32api
            vk, _ = self._key_mapping.get(key.lower(), (None, False))
            if vk:
                win32api.keybd_event(vk, 0, 0, 0)
        except Exception as e:
            logger.error(f"Error pressing key: {e}")

    def release_key(self, key: str) -> None:
        """Release key.
        
        Args:
            key: Key to release
        """
        try:
            import win32api
            import win32con
            vk, _ = self._key_mapping.get(key.lower(), (None, False))
            if vk:
                win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
        except Exception as e:
            logger.error(f"Error releasing key: {e}")

    def _create_key_mapping(self) -> Dict[str, tuple]:
        """Create mapping of characters to virtual key codes.
        
        Returns:
            Dict[str, tuple]: Character to (key code, shift required) mapping
        """
        try:
            import win32con
            return {
                'a': (win32con.VK_A, False),
                'b': (win32con.VK_B, False),
                # ... add all keys
                'shift': (win32con.VK_SHIFT, False),
                'ctrl': (win32con.VK_CONTROL, False),
                'alt': (win32con.VK_MENU, False),
                'meta': (win32con.VK_LWIN, False)
            }
        except ImportError:
            return {}


class MacOSKeyboard:
    """macOS virtual keyboard implementation using Quartz."""

    def __init__(self):
        """Initialize macOS keyboard."""
        self._key_mapping = self._create_key_mapping()

    def initialize(self) -> bool:
        """Initialize macOS keyboard.
        
        Returns:
            bool: True if initialization successful
        """
        try:
            from Quartz import kCGEventSourceStatePrivate
            return True
        except ImportError:
            return False

    def cleanup(self) -> None:
        """Clean up macOS keyboard."""
        pass  # No cleanup needed

    def type_char(self, char: str) -> None:
        """Type single character.
        
        Args:
            char: Character to type
        """
        try:
            from Quartz import CGEventCreateKeyboardEvent, CGEventPost, kCGHIDEventTap
            key_code = self._key_mapping.get(char.lower())
            if key_code:
                event = CGEventCreateKeyboardEvent(None, key_code, True)
                CGEventPost(kCGHIDEventTap, event)
                event = CGEventCreateKeyboardEvent(None, key_code, False)
                CGEventPost(kCGHIDEventTap, event)
        except Exception as e:
            logger.error(f"Error typing character: {e}")

    def press_key(self, key: str) -> None:
        """Press key.
        
        Args:
            key: Key to press
        """
        try:
            from Quartz import CGEventCreateKeyboardEvent, CGEventPost, kCGHIDEventTap
            key_code = self._key_mapping.get(key.lower())
            if key_code:
                event = CGEventCreateKeyboardEvent(None, key_code, True)
                CGEventPost(kCGHIDEventTap, event)
        except Exception as e:
            logger.error(f"Error pressing key: {e}")

    def release_key(self, key: str) -> None:
        """Release key.
        
        Args:
            key: Key to release
        """
        try:
            from Quartz import CGEventCreateKeyboardEvent, CGEventPost, kCGHIDEventTap
            key_code = self._key_mapping.get(key.lower())
            if key_code:
                event = CGEventCreateKeyboardEvent(None, key_code, False)
                CGEventPost(kCGHIDEventTap, event)
        except Exception as e:
            logger.error(f"Error releasing key: {e}")

    def _create_key_mapping(self) -> Dict[str, int]:
        """Create mapping of characters to macOS key codes.
        
        Returns:
            Dict[str, int]: Character to key code mapping
        """
        # macOS key codes
        return {
            'a': 0x00,
            'b': 0x0B,
            # ... add all keys
            'shift': 0x38,
            'ctrl': 0x3B,
            'alt': 0x3A,
            'meta': 0x37
        }
