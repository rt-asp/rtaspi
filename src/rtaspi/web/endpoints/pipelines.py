"""
rtaspi - Real-Time Annotation and Stream Processing
Pipeline API endpoints
"""

import logging
from typing import Optional
from aiohttp import web
from aiohttp.web import Request, Response

from ...api import PipelineAPI

logger = logging.getLogger(__name__)


class PipelineEndpoints:
    """Pipeline API endpoint handlers."""

    def __init__(self, pipeline_api: PipelineAPI):
        """
        Initialize pipeline endpoints.

        Args:
            pipeline_api (PipelineAPI): Pipeline API instance.
        """
        self.pipeline_api = pipeline_api

    def setup_routes(self, router: web.UrlDispatcher) -> None:
        """
        Set up pipeline API routes.

        Args:
            router (web.UrlDispatcher): URL router instance.
        """
        router.add_get("/api/pipelines", self.list_pipelines)
        router.add_post("/api/pipelines", self.create_pipeline)
        router.add_get("/api/pipelines/{name}", self.get_pipeline)
        router.add_put("/api/pipelines/{name}", self.update_pipeline)
        router.add_delete("/api/pipelines/{name}", self.remove_pipeline)
        router.add_get("/api/pipelines/{name}/status", self.pipeline_status)
        router.add_post("/api/pipelines/{name}/start", self.start_pipeline)
        router.add_post("/api/pipelines/{name}/stop", self.stop_pipeline)
        router.add_get("/api/pipelines/{name}/validate", self.validate_pipeline)

    async def list_pipelines(self, request: Request) -> Response:
        """
        List all pipelines.

        Args:
            request: HTTP request

        Returns:
            HTTP response with pipeline list
        """
        include_status = request.query.get("status", "true").lower() == "true"
        pipelines = self.pipeline_api.list_pipelines(include_status=include_status)
        return web.json_response(pipelines)

    async def create_pipeline(self, request: Request) -> Response:
        """
        Create a new pipeline.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        data = await request.json()
        self.pipeline_api.create_pipeline(**data)
        return web.Response(status=201)

    async def get_pipeline(self, request: Request) -> Response:
        """
        Get pipeline configuration.

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
        """
        Update pipeline configuration.

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
        """
        Remove a pipeline.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        name = request.match_info["name"]
        self.pipeline_api.remove_pipeline(name)
        return web.Response(status=204)

    async def pipeline_status(self, request: Request) -> Response:
        """
        Get pipeline status.

        Args:
            request: HTTP request

        Returns:
            HTTP response with pipeline status
        """
        name = request.match_info["name"]
        status = self.pipeline_api.get_pipeline_status(name)
        return web.json_response(status.dict())

    async def start_pipeline(self, request: Request) -> Response:
        """
        Start a pipeline.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        name = request.match_info["name"]
        self.pipeline_api.start_pipeline(name)
        return web.Response(status=200)

    async def stop_pipeline(self, request: Request) -> Response:
        """
        Stop a pipeline.

        Args:
            request: HTTP request

        Returns:
            HTTP response
        """
        name = request.match_info["name"]
        self.pipeline_api.stop_pipeline(name)
        return web.Response(status=200)

    async def validate_pipeline(self, request: Request) -> Response:
        """
        Validate pipeline configuration.

        Args:
            request: HTTP request

        Returns:
            HTTP response with validation errors
        """
        name = request.match_info["name"]
        errors = self.pipeline_api.validate_pipeline(name)
        return web.json_response({"errors": errors})
