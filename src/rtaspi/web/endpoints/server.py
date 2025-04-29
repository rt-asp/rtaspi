"""
rtaspi - Real-Time Annotation and Stream Processing
Server API endpoints
"""

import logging
from typing import Optional
from aiohttp import web
from aiohttp.web import Request, Response

from ...api import ServerAPI

logger = logging.getLogger(__name__)


class ServerEndpoints:
    """Server API endpoint handlers."""

    def __init__(self, server_api: ServerAPI):
        """
        Initialize server endpoints.

        Args:
            server_api (ServerAPI): Server API instance.
        """
        self.server_api = server_api

    def setup_routes(self, router: web.UrlDispatcher) -> None:
        """
        Set up server API routes.

        Args:
            router (web.UrlDispatcher): URL router instance.
        """
        router.add_get("/api/server/status", self.server_status)
        router.add_get("/api/server/config", self.server_config)
        router.add_post("/api/server/admin", self.create_admin)
        router.add_post(
            "/api/server/admin/{username}/reset-password", self.reset_password
        )
        router.add_get("/api/server/tokens", self.list_tokens)
        router.add_post("/api/server/tokens", self.create_token)
        router.add_delete("/api/server/tokens/{token}", self.revoke_token)

        # Documentation routes
        router.add_get("/api/docs", self.docs_handler)
        router.add_get("/api/openapi.json", self.openapi_handler)

    async def server_status(self, request: Request) -> Response:
        """
        Get server status.

        Args:
            request: HTTP request

        Returns:
            HTTP response with server status
        """
        status = self.server_api.get_status()
        return web.json_response(status)

    async def server_config(self, request: Request) -> Response:
        """
        Get server configuration.

        Args:
            request: HTTP request

        Returns:
            HTTP response with server configuration
        """
        config = self.server_api.get_config()
        return web.json_response(config)

    async def create_admin(self, request: Request) -> Response:
        """
        Create admin user.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        data = await request.json()
        self.server_api.create_admin(**data)
        return web.Response(status=201)

    async def reset_password(self, request: Request) -> Response:
        """
        Reset admin user password.

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
        """
        List API tokens.

        Args:
            request: HTTP request

        Returns:
            HTTP response with token list
        """
        tokens = self.server_api.list_api_tokens()
        return web.json_response(tokens)

    async def create_token(self, request: Request) -> Response:
        """
        Create new API token.

        Args:
            request: HTTP request

        Returns:
            HTTP response with token information
        """
        data = await request.json()
        token = self.server_api.create_token(**data)
        return web.json_response(token, status=201)

    async def revoke_token(self, request: Request) -> Response:
        """
        Revoke API token.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        token = request.match_info["token"]
        self.server_api.revoke_token(token)
        return web.Response(status=204)

    async def docs_handler(self, request: Request) -> Response:
        """
        Handle OpenAPI documentation page request.

        Args:
            request: HTTP request

        Returns:
            HTTP response with documentation page
        """
        # TODO: Implement Swagger UI page
        return web.Response(text="API Documentation")

    async def openapi_handler(self, request: Request) -> Response:
        """
        Handle OpenAPI specification request.

        Args:
            request: HTTP request

        Returns:
            HTTP response with OpenAPI specification
        """
        spec = self.server_api.generate_openapi_doc()
        return web.json_response(spec)
