"""
rtaspi - Real-Time Annotation and Stream Processing
Stream API endpoints
"""

import logging
from typing import Optional
from aiohttp import web
from aiohttp.web import Request, Response

from ...api import StreamAPI

logger = logging.getLogger(__name__)


class StreamEndpoints:
    """Stream API endpoint handlers."""

    def __init__(self, stream_api: StreamAPI):
        """
        Initialize stream endpoints.

        Args:
            stream_api (StreamAPI): Stream API instance.
        """
        self.stream_api = stream_api

    def setup_routes(self, router: web.UrlDispatcher) -> None:
        """
        Set up stream API routes.

        Args:
            router (web.UrlDispatcher): URL router instance.
        """
        router.add_get("/api/streams", self.list_streams)
        router.add_post("/api/streams", self.create_stream)
        router.add_get("/api/streams/{name}", self.get_stream)
        router.add_put("/api/streams/{name}", self.update_stream)
        router.add_delete("/api/streams/{name}", self.remove_stream)
        router.add_get("/api/streams/{name}/status", self.stream_status)
        router.add_post("/api/streams/{name}/start", self.start_stream)
        router.add_post("/api/streams/{name}/stop", self.stop_stream)
        router.add_post("/api/streams/{name}/restart", self.restart_stream)

    async def list_streams(self, request: Request) -> Response:
        """
        List all streams.

        Args:
            request: HTTP request

        Returns:
            HTTP response with stream list
        """
        device = request.query.get("device")
        stream_type = request.query.get("type")
        include_status = request.query.get("status", "true").lower() == "true"

        streams = self.stream_api.list_streams(
            device=device, stream_type=stream_type, include_status=include_status
        )
        return web.json_response(streams)

    async def create_stream(self, request: Request) -> Response:
        """
        Create a new stream.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        data = await request.json()
        self.stream_api.create_stream(**data)
        return web.Response(status=201)

    async def get_stream(self, request: Request) -> Response:
        """
        Get stream configuration.

        Args:
            request: HTTP request

        Returns:
            HTTP response with stream configuration
        """
        name = request.match_info["name"]
        stream = self.stream_api.get_stream(name)
        if not stream:
            raise web.HTTPNotFound(text=f"Stream not found: {name}")
        return web.json_response(stream)

    async def update_stream(self, request: Request) -> Response:
        """
        Update stream configuration.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        name = request.match_info["name"]
        data = await request.json()
        self.stream_api.update_stream(name, **data)
        return web.Response(status=200)

    async def remove_stream(self, request: Request) -> Response:
        """
        Remove a stream.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        name = request.match_info["name"]
        self.stream_api.remove_stream(name)
        return web.Response(status=204)

    async def stream_status(self, request: Request) -> Response:
        """
        Get stream status.

        Args:
            request: HTTP request

        Returns:
            HTTP response with stream status
        """
        name = request.match_info["name"]
        status = self.stream_api.get_stream_status(name)
        return web.json_response(status.dict())

    async def start_stream(self, request: Request) -> Response:
        """
        Start a stream.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        name = request.match_info["name"]
        self.stream_api.start_stream(name)
        return web.Response(status=200)

    async def stop_stream(self, request: Request) -> Response:
        """
        Stop a stream.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        name = request.match_info["name"]
        self.stream_api.stop_stream(name)
        return web.Response(status=200)

    async def restart_stream(self, request: Request) -> Response:
        """
        Restart a stream.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        name = request.match_info["name"]
        self.stream_api.restart_stream(name)
        return web.Response(status=200)
