"""
rtaspi - Real-Time Annotation and Stream Processing
Platform-specific device scanners
"""

import platform
from .linux_scanner import LinuxDeviceScanner
from .macos_scanner import MacOSDeviceScanner
from .windows_scanner import WindowsDeviceScanner


def get_platform_scanner():
    """
    Returns the appropriate device scanner for the current platform.

    Returns:
        DeviceScanner: Platform-specific device scanner instance.
    """
    system = platform.system().lower()

    if system == "linux":
        return LinuxDeviceScanner()
    elif system == "darwin":  # macOS
        return MacOSDeviceScanner()
    elif system == "windows":
        return WindowsDeviceScanner()
    else:
        raise NotImplementedError(f"Platform {system} is not supported")
