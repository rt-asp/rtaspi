"""
rtaspi - Real-Time Annotation and Stream Processing
WebRTC streaming module
"""

from .webrtc.server import WebRTCServer

# Re-export WebRTCServer for backward compatibility
__all__ = ["WebRTCServer"]
