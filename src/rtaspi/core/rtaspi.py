"""
Main RTASPI interface class.
"""

from typing import Dict, Any, Optional

from ..api.devices import DeviceAPI
from ..api.streams import StreamAPI
from ..api.pipelines import PipelineAPI
from .config import ConfigManager
from .mcp import MCPBroker


class RTASPI:
    """Main interface for RTASPI functionality."""

    def __init__(self):
        """Initialize RTASPI interface."""
        # Initialize core components
        self.config = ConfigManager()
        self.mcp_broker = MCPBroker()

        # Initialize APIs with dependencies
        self.devices = DeviceAPI(config=self.config.config, mcp_broker=self.mcp_broker)
        self.streams = StreamAPI(config=self.config.config, mcp_broker=self.mcp_broker)
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
