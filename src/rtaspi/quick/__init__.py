"""
Simplified API for junior developers.

This module provides a simplified interface for common tasks, making it easier
for junior developers to get started with the library. It abstracts away much
of the complexity while still providing access to the core functionality.

Example usage:

    from rtaspi.quick import start_camera, add_filter, add_output

    # Start a camera stream
    stream = start_camera(name="webcam")

    # Add some filters
    add_filter(stream, "GRAYSCALE")
    add_filter(stream, "EDGE_DETECTION")

    # Configure output
    add_output(stream, "RTSP", "rtsp://localhost:8554/webcam")
"""

__version__ = "1.0.0"
__author__ = "RT-ASP Team"
__all__ = [
    # Camera functions
    "start_camera",
    "stop_camera",
    "list_cameras",
    # Microphone functions
    "start_microphone",
    "stop_microphone",
    "list_microphones",
    # Stream functions
    "add_filter",
    "remove_filter",
    "add_output",
    "remove_output",
    # Configuration functions
    "save_config",
    "load_config",
]

from .camera import start_camera, stop_camera, list_cameras
from .microphone import start_microphone, stop_microphone, list_microphones
from .utils import (
    add_filter,
    remove_filter,
    add_output,
    remove_output,
    save_config,
    load_config,
)

# Version history:
# 1.0.0 - Initial release with simplified API
#       - Camera and microphone management
#       - Filter and output configuration
#       - Configuration file handling
