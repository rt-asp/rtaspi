"""
Central point for all constant definitions and enumerations used in the rtaspi library.

This module provides easy access to all enumerations through a clean interface:

from rtaspi.constants import FilterType, DeviceType, OutputType, ProtocolType

It also provides version information and metadata about the constants module.
"""

__version__ = "1.0.0"
__author__ = "RT-ASP Team"
__all__ = ["FilterType", "DeviceType", "OutputType", "ProtocolType"]

from .filters import FilterType
from .devices import DeviceType
from .outputs import OutputType
from .protocols import ProtocolType

# Version history:
# 1.0.0 - Initial release with core enumerations
#       - FilterType: Video and audio processing filters
#       - DeviceType: Local and network device types
#       - OutputType: Streaming, file, and event outputs
#       - ProtocolType: Communication and streaming protocols
