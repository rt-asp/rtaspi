"""
Public API for the rtaspi library.

This module provides high-level facades for managing devices, streams,
pipelines, and the web server. These facades encapsulate the internal
implementation details and provide a clean, stable API for users.

Example usage:

    from rtaspi.api import DeviceAPI, StreamAPI, PipelineAPI, ServerAPI

    # Manage devices
    device_api = DeviceAPI()
    devices = device_api.list_devices()
    device_api.add_device(name="camera1", type="USB_CAMERA")

    # Manage streams
    stream_api = StreamAPI()
    stream_api.create_stream(name="stream1", device="camera1", type="video")
    stream_api.start_stream("stream1")

    # Manage pipelines
    pipeline_api = PipelineAPI()
    pipeline_api.create_pipeline(name="pipeline1", stages=[...])
    pipeline_api.start_pipeline("pipeline1")

    # Manage server
    server_api = ServerAPI()
    server_api.start(host="localhost", port=8080)
"""

__version__ = "1.0.0"
__author__ = "RT-ASP Team"
__all__ = ["DeviceAPI", "StreamAPI", "PipelineAPI", "ServerAPI"]

from .devices import DeviceAPI
from .streams import StreamAPI
from .pipelines import PipelineAPI
from .server import ServerAPI

# Version history:
# 1.0.0 - Initial release with core API facades
#       - DeviceAPI: Device management
#       - StreamAPI: Stream management
#       - PipelineAPI: Pipeline management
#       - ServerAPI: Server management
