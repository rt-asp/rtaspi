"""
REST API implementation.

This module provides the REST API endpoints and OpenAPI documentation.
"""
import json
import logging
from typing import Dict, Any, List
from aiohttp import web
from aiohttp.web import Request, Response

from rtaspi.api import DeviceAPI, StreamAPI, PipelineAPI, ServerAPI


class APIServer:
    """REST API server."""

    def __init__(self, app: web.Application):
        """Initialize the API server.

        Args:
            app: aiohttp Application instance
        """
        self.logger = logging.getLogger(__name__)
        self.app = app
        self.device_api = DeviceAPI()
        self.stream_api = StreamAPI()
        self.pipeline_api = PipelineAPI()
        self.server_api = ServerAPI()

        # Configure routes
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Set up API routes."""
        # Device endpoints
        self.app.router.add_get("/api/devices", self.list_devices)
        self.app.router.add_post("/api/devices", self.add_device)
        self.app.router.add_get("/api/devices/{name}", self.get_device)
        self.app.router.add_put("/api/devices/{name}", self.update_device)
        self.app.router.add_delete("/api/devices/{name}", self.remove_device)
        self.app.router.add_get("/api/devices/{name}/status", self.device_status)
        self.app.router.add_get("/api/devices/{name}/capabilities", self.device_capabilities)
        self.app.router.add_get("/api/devices/discover", self.discover_devices)

        # Stream endpoints
        self.app.router.add_get("/api/streams", self.list_streams)
        self.app.router.add_post("/api/streams", self.create_stream)
        self.app.router.add_get("/api/streams/{name}", self.get_stream)
        self.app.router.add_put("/api/streams/{name}", self.update_stream)
        self.app.router.add_delete("/api/streams/{name}", self.remove_stream)
        self.app.router.add_get("/api/streams/{name}/status", self.stream_status)
        self.app.router.add_post("/api/streams/{name}/start", self.start_stream)
        self.app.router.add_post("/api/streams/{name}/stop", self.stop_stream)
        self.app.router.add_post("/api/streams/{name}/restart", self.restart_stream)

        # Pipeline endpoints
        self.app.router.add_get("/api/pipelines", self.list_pipelines)
        self.app.router.add_post("/api/pipelines", self.create_pipeline)
        self.app.router.add_get("/api/pipelines/{name}", self.get_pipeline)
        self.app.router.add_put("/api/pipelines/{name}", self.update_pipeline)
        self.app.router.add_delete("/api/pipelines/{name}", self.remove_pipeline)
        self.app.router.add_get("/api/pipelines/{name}/status", self.pipeline_status)
        self.app.router.add_post("/api/pipelines/{name}/start", self.start_pipeline)
        self.app.router.add_post("/api/pipelines/{name}/stop", self.stop_pipeline)
        self.app.router.add_get("/api/pipelines/{name}/validate", self.validate_pipeline)

        # Server endpoints
        self.app.router.add_get("/api/server/status", self.server_status)
        self.app.router.add_get("/api/server/config", self.server_config)
        self.app.router.add_post("/api/server/admin", self.create_admin)
        self.app.router.add_post("/api/server/admin/{username}/reset-password", self.reset_password)
        self.app.router.add_get("/api/server/tokens", self.list_tokens)
        self.app.router.add_post("/api/server/tokens", self.create_token)
        self.app.router.add_delete("/api/server/tokens/{token}", self.revoke_token)

    async def docs_handler(self, request: Request) -> Response:
        """Handle OpenAPI documentation page request.

        Args:
            request: HTTP request

        Returns:
            HTTP response with documentation page
        """
        # TODO: Implement Swagger UI page
        return web.Response(text="API Documentation")

    async def openapi_handler(self, request: Request) -> Response:
        """Handle OpenAPI specification request.

        Args:
            request: HTTP request

        Returns:
            HTTP response with OpenAPI specification
        """
        spec = self.server_api.generate_openapi_doc()
        return web.json_response(spec)

    # Device endpoints

    async def list_devices(self, request: Request) -> Response:
        """List all devices.

        Args:
            request: HTTP request

        Returns:
            HTTP response with device list
        """
        device_type = request.query.get("type")
        include_status = request.query.get("status", "true").lower() == "true"

        devices = self.device_api.list_devices(
            device_type=device_type,
            include_status=include_status
        )
        return web.json_response(devices)

    async def add_device(self, request: Request) -> Response:
        """Add a new device.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        data = await request.json()
        self.device_api.add_device(**data)
        return web.Response(status=201)

    async def get_device(self, request: Request) -> Response:
        """Get device configuration.

        Args:
            request: HTTP request

        Returns:
            HTTP response with device configuration
        """
        name = request.match_info["name"]
        device = self.device_api.get_device(name)
        if not device:
            raise web.HTTPNotFound(text=f"Device not found: {name}")
        return web.json_response(device)

    async def update_device(self, request: Request) -> Response:
        """Update device configuration.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        name = request.match_info["name"]
        data = await request.json()
        self.device_api.update_device(name, **data)
        return web.Response(status=200)

    async def remove_device(self, request: Request) -> Response:
        """Remove a device.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        name = request.match_info["name"]
        self.device_api.remove_device(name)
        return web.Response(status=204)

    async def device_status(self, request: Request) -> Response:
        """Get device status.

        Args:
            request: HTTP request

        Returns:
            HTTP response with device status
        """
        name = request.match_info["name"]
        status = self.device_api.get_device_status(name)
        return web.json_response(status.dict())

    async def device_capabilities(self, request: Request) -> Response:
        """Get device capabilities.

        Args:
            request: HTTP request

        Returns:
            HTTP response with device capabilities
        """
        name = request.match_info["name"]
        capabilities = self.device_api.scan_device_capabilities(name)
        return web.json_response(capabilities)

    async def discover_devices(self, request: Request) -> Response:
        """Discover available devices.

        Args:
            request: HTTP request

        Returns:
            HTTP response with discovered devices
        """
        device_type = request.query.get("type")
        timeout = float(request.query.get("timeout", "5.0"))

        devices = self.device_api.discover_devices(
            device_type=device_type,
            timeout=timeout
        )
        return web.json_response(devices)

    # Stream endpoints

    async def list_streams(self, request: Request) -> Response:
        """List all streams.

        Args:
            request: HTTP request

        Returns:
            HTTP response with stream list
        """
        device = request.query.get("device")
        stream_type = request.query.get("type")
        include_status = request.query.get("status", "true").lower() == "true"

        streams = self.stream_api.list_streams(
            device=device,
            stream_type=stream_type,
            include_status=include_status
        )
        return web.json_response(streams)

    async def create_stream(self, request: Request) -> Response:
        """Create a new stream.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        data = await request.json()
        self.stream_api.create_stream(**data)
        return web.Response(status=201)

    async def get_stream(self, request: Request) -> Response:
        """Get stream configuration.

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
        """Update stream configuration.

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
        """Remove a stream.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        name = request.match_info["name"]
        self.stream_api.remove_stream(name)
        return web.Response(status=204)

    async def stream_status(self, request: Request) -> Response:
        """Get stream status.

        Args:
            request: HTTP request

        Returns:
            HTTP response with stream status
        """
        name = request.match_info["name"]
        status = self.stream_api.get_stream_status(name)
        return web.json_response(status.dict())

    async def start_stream(self, request: Request) -> Response:
        """Start a stream.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        name = request.match_info["name"]
        self.stream_api.start_stream(name)
        return web.Response(status=200)

    async def stop_stream(self, request: Request) -> Response:
        """Stop a stream.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        name = request.match_info["name"]
        self.stream_api.stop_stream(name)
        return web.Response(status=200)

    async def restart_stream(self, request: Request) -> Response:
        """Restart a stream.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        name = request.match_info["name"]
        self.stream_api.restart_stream(name)
        return web.Response(status=200)

    # Pipeline endpoints

    async def list_pipelines(self, request: Request) -> Response:
        """List all pipelines.

        Args:
            request: HTTP request

        Returns:
            HTTP response with pipeline list
        """
        include_status = request.query.get("status", "true").lower() == "true"
        pipelines = self.pipeline_api.list_pipelines(include_status=include_status)
        return web.json_response(pipelines)

    async def create_pipeline(self, request: Request) -> Response:
        """Create a new pipeline.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        data = await request.json()
        self.pipeline_api.create_pipeline(**data)
        return web.Response(status=201)

    async def get_pipeline(self, request: Request) -> Response:
        """Get pipeline configuration.

        Args:
            request: HTTP request

        Returns:
            HTTP response with pipeline configuration
        """
        name = request.match_info["name"]
        pipeline = self.pipeline_api.get_pipeline(name)
        if not pipeline:
            raise web.HTTPNotFound(text=f"Pipeline not found: {name}")
        return web.json_response(pipeline)

    async def update_pipeline(self, request: Request) -> Response:
        """Update pipeline configuration.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        name = request.match_info["name"]
        data = await request.json()
        self.pipeline_api.update_pipeline(name, **data)
        return web.Response(status=200)

    async def remove_pipeline(self, request: Request) -> Response:
        """Remove a pipeline.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        name = request.match_info["name"]
        self.pipeline_api.remove_pipeline(name)
        return web.Response(status=204)

    async def pipeline_status(self, request: Request) -> Response:
        """Get pipeline status.

        Args:
            request: HTTP request

        Returns:
            HTTP response with pipeline status
        """
        name = request.match_info["name"]
        status = self.pipeline_api.get_pipeline_status(name)
        return web.json_response(status.dict())

    async def start_pipeline(self, request: Request) -> Response:
        """Start a pipeline.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        name = request.match_info["name"]
        self.pipeline_api.start_pipeline(name)
        return web.Response(status=200)

    async def stop_pipeline(self, request: Request) -> Response:
        """Stop a pipeline.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        name = request.match_info["name"]
        self.pipeline_api.stop_pipeline(name)
        return web.Response(status=200)

    async def validate_pipeline(self, request: Request) -> Response:
        """Validate pipeline configuration.

        Args:
            request: HTTP request

        Returns:
            HTTP response with validation errors
        """
        name = request.match_info["name"]
        errors = self.pipeline_api.validate_pipeline(name)
        return web.json_response({"errors": errors})

    # Server endpoints

    async def server_status(self, request: Request) -> Response:
        """Get server status.

        Args:
            request: HTTP request

        Returns:
            HTTP response with server status
        """
        status = self.server_api.get_status()
        return web.json_response(status)

    async def server_config(self, request: Request) -> Response:
        """Get server configuration.

        Args:
            request: HTTP request

        Returns:
            HTTP response with server configuration
        """
        config = self.server_api.get_config()
        return web.json_response(config)

    async def create_admin(self, request: Request) -> Response:
        """Create admin user.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        data = await request.json()
        self.server_api.create_admin(**data)
        return web.Response(status=201)

    async def reset_password(self, request: Request) -> Response:
        """Reset admin user password.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        username = request.match_info["username"]
        data = await request.json()
        self.server_api.reset_password(username, data["password"])
        return web.Response(status=200)

    async def list_tokens(self, request: Request) -> Response:
        """List API tokens.

        Args:
            request: HTTP request

        Returns:
            HTTP response with token list
        """
        tokens = self.server_api.list_api_tokens()
        return web.json_response(tokens)

    async def create_token(self, request: Request) -> Response:
        """Create new API token.

        Args:
            request: HTTP request

        Returns:
            HTTP response with token information
        """
        data = await request.json()
        token = self.server_api.create_token(**data)
        return web.json_response(token, status=201)

    async def revoke_token(self, request: Request) -> Response:
        """Revoke API token.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        token = request.match_info["token"]
        self.server_api.revoke_token(token)
        return web.Response(status=204)
