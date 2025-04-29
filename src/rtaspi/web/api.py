"""
rtaspi - Real-Time Annotation and Stream Processing
REST API implementation
"""

import logging
from aiohttp import web

from ..api import DeviceAPI, StreamAPI, PipelineAPI, ServerAPI
from .endpoints.devices import DeviceEndpoints
from .endpoints.streams import StreamEndpoints
from .endpoints.pipelines import PipelineEndpoints
from .endpoints.server import ServerEndpoints

logger = logging.getLogger(__name__)


class APIServer:
    """REST API server."""

    def __init__(self, app: web.Application):
        """
        Initialize the API server.

        Args:
            app: aiohttp Application instance
        """
        self.app = app

        # Initialize API instances
        self.device_api = DeviceAPI()
        self.stream_api = StreamAPI()
        self.pipeline_api = PipelineAPI()
        self.server_api = ServerAPI()

        # Initialize endpoint handlers
        self.device_endpoints = DeviceEndpoints(self.device_api)
        self.stream_endpoints = StreamEndpoints(self.stream_api)
        self.pipeline_endpoints = PipelineEndpoints(self.pipeline_api)
        self.server_endpoints = ServerEndpoints(self.server_api)

        # Configure routes
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Set up API routes."""
        # Set up routes for each endpoint group
        self.device_endpoints.setup_routes(self.app.router)
        self.stream_endpoints.setup_routes(self.app.router)
        self.pipeline_endpoints.setup_routes(self.app.router)
        self.server_endpoints.setup_routes(self.app.router)
