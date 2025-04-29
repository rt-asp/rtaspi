"""
rtaspi package initialization.
"""

from ._version import __version__
from . import core
from . import device_managers
from . import streaming

__all__ = ["__version__", "core", "device_managers", "streaming"]
