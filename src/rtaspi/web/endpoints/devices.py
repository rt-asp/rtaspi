"""
rtaspi - Real-Time Annotation and Stream Processing
Device API endpoints
"""

import logging
from typing import Optional
from aiohttp import web
from aiohttp.web import Request, Response

from ...api import DeviceAPI

logger = logging.getLogger(__name__)


class DeviceEndpoints:
    """Device API endpoint handlers."""

    def __init__(self, device_api: DeviceAPI):
        """
        Initialize device endpoints.

        Args:
            device_api (DeviceAPI): Device API instance.
        """
        self.device_api = device_api

    def setup_routes(self, router: web.UrlDispatcher) -> None:
        """
        Set up device API routes.

        Args:
            router (web.UrlDispatcher): URL router instance.
        """
        router.add_get("/api/devices", self.list_devices)
        router.add_post("/api/devices", self.add_device)
        router.add_get("/api/devices/{name}", self.get_device)
        router.add_put("/api/devices/{name}", self.update_device)
        router.add_delete("/api/devices/{name}", self.remove_device)
        router.add_get("/api/devices/{name}/status", self.device_status)
        router.add_get("/api/devices/{name}/capabilities", self.device_capabilities)
        router.add_get("/api/devices/discover", self.discover_devices)

    async def list_devices(self, request: Request) -> Response:
        """
        List all devices.

        Args:
            request: HTTP request

        Returns:
            HTTP response with device list
        """
        device_type = request.query.get("type")
        include_status = request.query.get("status", "true").lower() == "true"

        devices = self.device_api.list_devices(
            device_type=device_type, include_status=include_status
        )
        return web.json_response(devices)

    async def add_device(self, request: Request) -> Response:
        """
        Add a new device.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        data = await request.json()
        self.device_api.add_device(**data)
        return web.Response(status=201)

    async def get_device(self, request: Request) -> Response:
        """
        Get device configuration.

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
        """
        Update device configuration.

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
        """
        Remove a device.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        name = request.match_info["name"]
        self.device_api.remove_device(name)
        return web.Response(status=204)

    async def device_status(self, request: Request) -> Response:
        """
        Get device status.

        Args:
            request: HTTP request

        Returns:
            HTTP response with device status
        """
        name = request.match_info["name"]
        status = self.device_api.get_device_status(name)
        return web.json_response(status.dict())

    async def device_capabilities(self, request: Request) -> Response:
        """
        Get device capabilities.

        Args:
            request: HTTP request

        Returns:
            HTTP response with device capabilities
        """
        name = request.match_info["name"]
        capabilities = self.device_api.scan_device_capabilities(name)
        return web.json_response(capabilities)

    async def discover_devices(self, request: Request) -> Response:
        """
        Discover available devices.

        Args:
            request: HTTP request

        Returns:
            HTTP response with discovered devices
        """
        device_type = request.query.get("type")
        timeout = float(request.query.get("timeout", "5.0"))

        devices = self.device_api.discover_devices(
            device_type=device_type, timeout=timeout
        )
        return web.json_response(devices)
