"""
RTASPI Devices Module

This module provides device management functionality for the RTASPI system,
including support for local and network devices.
"""

from .base import (
    Device,
    LocalDevice,
    DeviceStatus,
    DeviceManager,
)
from .network import NetworkDevice
from .local import LocalDeviceManager
from .protocols import (
    ProtocolStatus,
    DeviceProtocol,
    StreamingProtocol,
    ControlProtocol,
)
from .discovery import DeviceScanner

__version__ = "0.2.0"

__all__ = [
    # Base classes
    'Device',
    'LocalDevice',
    'NetworkDevice',
    'DeviceStatus',
    'DeviceManager',
    
    # Local device management
    'LocalDeviceManager',
    
    # Protocol interfaces
    'ProtocolStatus',
    'DeviceProtocol',
    'StreamingProtocol',
    'ControlProtocol',
    
    # Device discovery
    'DeviceScanner',
]
