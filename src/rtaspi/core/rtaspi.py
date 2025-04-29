"""
Main RTASPI interface class.
"""

from typing import Dict, Any, Optional

from ..api.devices import DeviceAPI
from ..api.streams import StreamAPI
from ..api.pipelines import PipelineAPI


class RTASPI:
    """Main interface for RTASPI functionality."""

    def __init__(self):
        """Initialize RTASPI interface."""
        self.devices = DeviceAPI()
        self.streams = StreamAPI()
        self.pipelines = PipelineAPI()

    def cleanup(self):
        """Clean up resources."""
        # Stop all streams
        for stream_id in self.streams.list():
            try:
                self.streams.stop(stream_id)
            except Exception:
                pass

        # Stop all pipelines
        for pipeline_id in self.pipelines.list():
            try:
                self.pipelines.stop(pipeline_id)
            except Exception:
                pass
