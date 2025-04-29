"""Remote desktop protocol support for rtaspi."""

from .rdp import RDPDevice
from .base import RemoteDesktopDevice

__all__ = ['RDPDevice', 'RemoteDesktopDevice']
