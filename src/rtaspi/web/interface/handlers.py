"""
rtaspi - Real-Time Annotation and Stream Processing
Web interface page handlers
"""

import logging
from aiohttp import web
from aiohttp.web import Request, Response

from ...api import DeviceAPI, StreamAPI, PipelineAPI, ServerAPI

logger = logging.getLogger(__name__)


class PageHandlers:
    """Web interface page handlers."""

    def __init__(
        self,
        template_engine,
        device_api: DeviceAPI,
        stream_api: StreamAPI,
        pipeline_api: PipelineAPI,
        server_api: ServerAPI,
    ):
        """
        Initialize page handlers.

        Args:
            template_engine: Jinja2 template engine.
            device_api (DeviceAPI): Device API instance.
            stream_api (StreamAPI): Stream API instance.
            pipeline_api (PipelineAPI): Pipeline API instance.
            server_api (ServerAPI): Server API instance.
        """
        self.env = template_engine
        self.device_api = device_api
        self.stream_api = stream_api
        self.pipeline_api = pipeline_api
        self.server_api = server_api

    def setup_routes(self, router: web.UrlDispatcher) -> None:
        """
        Set up page routes.

        Args:
            router (web.UrlDispatcher): URL router instance.
        """
        router.add_get("/", self.index_handler)
        router.add_get("/matrix", self.matrix_handler)
        router.add_get("/config", self.config_handler)

    async def index_handler(self, request: Request) -> Response:
        """
        Handle index page request.

        Args:
            request: HTTP request

        Returns:
            HTTP response with index page
        """
        # Get device statistics
        devices = self.device_api.list_devices()
        device_stats = {
            "total": len(devices),
            "online": sum(
                1 for d in devices.values() if d.get("status", {}).get("online", False)
            ),
            "cameras": sum(
                1 for d in devices.values() if "CAMERA" in d.get("type", "")
            ),
            "microphones": sum(
                1 for d in devices.values() if "MICROPHONE" in d.get("type", "")
            ),
        }

        # Get stream statistics
        streams = self.stream_api.list_streams()
        stream_stats = {
            "total": len(streams),
            "active": sum(
                1 for s in streams.values() if s.get("status", {}).get("active", False)
            ),
            "video": sum(
                1
                for s in streams.values()
                if s.get("source", {}).get("stream_type") in ["video", "both"]
            ),
            "audio": sum(
                1
                for s in streams.values()
                if s.get("source", {}).get("stream_type") in ["audio", "both"]
            ),
        }

        # Get pipeline statistics
        pipelines = self.pipeline_api.list_pipelines()
        pipeline_stats = {
            "total": len(pipelines),
            "running": sum(
                1
                for p in pipelines.values()
                if p.get("status", {}).get("running", False)
            ),
        }

        # Render template
        template = self.env.get_template("index.html")
        html = template.render(
            device_stats=device_stats,
            stream_stats=stream_stats,
            pipeline_stats=pipeline_stats,
        )

        return web.Response(text=html, content_type="text/html")

    async def matrix_handler(self, request: Request) -> Response:
        """
        Handle matrix view page request.

        Args:
            request: HTTP request

        Returns:
            HTTP response with matrix view page
        """
        # Get active streams
        streams = self.stream_api.list_streams()
        active_streams = {
            name: config
            for name, config in streams.items()
            if config.get("status", {}).get("active", False)
        }

        # Group streams by type
        video_streams = {}
        audio_streams = {}

        for name, config in active_streams.items():
            stream_type = config.get("source", {}).get("stream_type")
            if stream_type in ["video", "both"]:
                video_streams[name] = config
            if stream_type in ["audio", "both"]:
                audio_streams[name] = config

        # Render template
        template = self.env.get_template("matrix.html")
        html = template.render(video_streams=video_streams, audio_streams=audio_streams)

        return web.Response(text=html, content_type="text/html")

    async def config_handler(self, request: Request) -> Response:
        """
        Handle configuration page request.

        Args:
            request: HTTP request

        Returns:
            HTTP response with configuration page
        """
        # Get current configuration
        server_config = self.server_api.get_config()
        server_status = self.server_api.get_status()

        # Get API tokens
        tokens = self.server_api.list_api_tokens()

        # Render template
        template = self.env.get_template("config.html")
        html = template.render(
            config=server_config, status=server_status, tokens=tokens
        )

        return web.Response(text=html, content_type="text/html")
