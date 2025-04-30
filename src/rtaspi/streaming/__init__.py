"""
Streaming package initialization.
"""

from .rtsp import RTSPServer
from .rtmp import RTMPServer
from .webrtc import WebRTCServer
from .utils import get_stream_url

# Lazy imports to avoid loading dependencies until needed
def get_stream_output():
    from .output import StreamOutput
    return StreamOutput

def get_audio_output():
    from .output import AudioOutput
    return AudioOutput

def get_file_output():
    from .output import FileOutput
    return FileOutput

__all__ = [
    "RTSPServer",
    "RTMPServer",
    "WebRTCServer",
    "get_stream_url",
    "get_stream_output",
    "get_audio_output",
    "get_file_output"
]
