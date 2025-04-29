"""X11 window capture utilities for remote desktop implementations."""

import logging
import numpy as np
import cv2
from typing import Optional, Tuple
import platform

logger = logging.getLogger(__name__)

# Try to import Xlib, but don't fail if not available
try:
    import Xlib
    from Xlib import X, display, xobject
    from Xlib.ext import composite
    XLIB_AVAILABLE = True
except ImportError:
    logger.warning("Xlib not available - X11 window capture will be disabled")
    XLIB_AVAILABLE = False

class WindowCapture:
    """X11 window capture implementation."""

    def __init__(self):
        """Initialize window capture."""
        self._display = None
        self._window = None
        self._window_geometry = None
        self._composite_initialized = False
        
        # Check if we're on Linux and have Xlib
        self._capture_supported = platform.system() == 'Linux' and XLIB_AVAILABLE
        if not self._capture_supported:
            logger.warning("Window capture not supported on this platform")

    def initialize(self) -> bool:
        """Initialize display and composite extension.
        
        Returns:
            bool: True if initialization successful
        """
        if not self._capture_supported:
            return False
        try:
            # Connect to X server
            self._display = display.Display()
            
            # Check for composite extension
            if not self._display.has_extension('Composite'):
                logger.error("X server does not support Composite extension")
                return False
                
            # Initialize composite
            composite.composite_get_version(self._display)
            composite.composite_redirect_window(
                self._display.screen().root,
                composite.RedirectAutomatic
            )
            self._composite_initialized = True
            
            logger.info("X11 window capture initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize X11 window capture: {e}")
            self.cleanup()
            return False

    def find_window_by_name(self, name: str) -> bool:
        """Find window by name.
        
        Args:
            name: Window name to find
            
        Returns:
            bool: True if window found
        """
        if not self._capture_supported:
            return False
        try:
            root = self._display.screen().root
            window_ids = root.get_full_property(
                self._display.intern_atom('_NET_CLIENT_LIST'),
                X.AnyPropertyType
            ).value

            for window_id in window_ids:
                window = self._display.create_resource_object('window', window_id)
                try:
                    window_name = window.get_wm_name()
                    if window_name and name.lower() in window_name.lower():
                        self._window = window
                        self._window_geometry = window.get_geometry()
                        logger.info(f"Found window: {window_name}")
                        return True
                except Xlib.error.BadWindow:
                    continue

            logger.error(f"Window not found: {name}")
            return False

        except Exception as e:
            logger.error(f"Error finding window: {e}")
            return False

    def get_window_size(self) -> Optional[Tuple[int, int]]:
        """Get current window size.
        
        Returns:
            Optional[Tuple[int, int]]: Window width and height if available
        """
        if not self._capture_supported:
            return None
        if not self._window_geometry:
            return None
        return self._window_geometry.width, self._window_geometry.height

    def capture_window(self) -> Optional[bytes]:
        """Capture current window content.
        
        Returns:
            Optional[bytes]: JPEG encoded frame data if successful
        """
        if not self._capture_supported:
            return None
        if not self._window or not self._window_geometry:
            return None

        try:
            # Get window image
            image = self._window.get_image(
                0, 0,
                self._window_geometry.width,
                self._window_geometry.height,
                X.ZPixmap,
                0xffffffff
            )

            # Convert to numpy array
            data = np.frombuffer(image.data, dtype=np.uint8)
            data = data.reshape(
                self._window_geometry.height,
                self._window_geometry.width,
                4  # RGBA
            )

            # Convert RGBA to BGR
            frame = cv2.cvtColor(data, cv2.COLOR_RGBA2BGR)

            # Encode as JPEG
            success, encoded = cv2.imencode(
                '.jpg',
                frame,
                [cv2.IMWRITE_JPEG_QUALITY, 80]
            )
            
            if not success:
                logger.error("Failed to encode frame")
                return None

            return encoded.tobytes()

        except Xlib.error.BadWindow:
            logger.error("Window no longer valid")
            self._window = None
            self._window_geometry = None
            return None
            
        except Exception as e:
            logger.error(f"Error capturing window: {e}")
            return None

    def cleanup(self):
        """Clean up resources."""
        if not self._capture_supported:
            return
        try:
            if self._display:
                self._display.close()
                self._display = None
            self._window = None
            self._window_geometry = None
            self._composite_initialized = False
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
