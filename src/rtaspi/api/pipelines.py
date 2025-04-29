"""
Pipeline management API facade.

This module provides a high-level interface for managing processing pipelines,
abstracting away the internal implementation details.
"""

from typing import Optional, Dict, List, Any, Union
import logging

from rtaspi.constants import FilterType
from rtaspi.schemas import (
    PipelineConfig,
    PipelineStatus,
    PipelineStage,
    ResourceLimits,
    ExecutionSettings,
    ErrorHandling,
)


class PipelineAPI:
    """High-level API for pipeline management."""

    def __init__(self):
        """Initialize the pipeline API."""
        self.logger = logging.getLogger(__name__)
        self.pipelines: Dict[str, PipelineConfig] = {}
        self.running_pipelines: Dict[str, bool] = {}

    def list_pipelines(self, include_status: bool = True) -> Dict[str, Dict[str, Any]]:
        """List all configured pipelines.

        Args:
            include_status: Whether to include pipeline status information

        Returns:
            Dictionary mapping pipeline names to their configurations
        """
        pipelines = {}

        for name, config in self.pipelines.items():
            # Convert to dict for modification
            pipeline_dict = config.dict()

            # Add status if requested
            if include_status:
                pipeline_dict["status"] = self.get_pipeline_status(name).dict()

            pipelines[name] = pipeline_dict

        return pipelines

    def get_pipeline(self, name: str) -> Optional[Dict[str, Any]]:
        """Get pipeline configuration by name.

        Args:
            name: Pipeline name

        Returns:
            Pipeline configuration if found, None otherwise
        """
        if name in self.pipelines:
            return self.pipelines[name].dict()
        return None

    def create_pipeline(
        self,
        name: str,
        description: Optional[str] = None,
        enabled: bool = True,
        parallel: bool = True,
        resource_limits: Optional[Dict[str, Any]] = None,
        error_handling: Optional[Dict[str, Any]] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Create a new pipeline.

        Args:
            name: Unique pipeline name
            description: Optional pipeline description
            enabled: Whether the pipeline is enabled
            parallel: Whether stages can execute in parallel
            resource_limits: Resource usage limits
            error_handling: Error handling configuration
            settings: Pipeline-specific settings
        """
        if name in self.pipelines:
            raise ValueError(f"Pipeline already exists: {name}")

        # Create pipeline config
        config = {
            "name": name,
            "description": description,
            "enabled": enabled,
            "stages": [],
            "execution_settings": {
                "parallel_execution": parallel,
            },
            "metadata": settings or {},
        }

        if resource_limits:
            config["resource_limits"] = resource_limits
        if error_handling:
            config["error_handling"] = error_handling

        # Validate config
        pipeline_config = PipelineConfig(**config)

        # Store pipeline
        self.pipelines[name] = pipeline_config

    def remove_pipeline(self, name: str) -> None:
        """Remove a pipeline.

        Args:
            name: Pipeline name
        """
        if name not in self.pipelines:
            raise ValueError(f"Pipeline not found: {name}")

        # Stop pipeline if running
        if self.get_pipeline_status(name).running:
            self.stop_pipeline(name)

        # Remove pipeline
        del self.pipelines[name]

    def update_pipeline(
        self,
        name: str,
        enabled: Optional[bool] = None,
        description: Optional[str] = None,
        parallel: Optional[bool] = None,
        resource_limits: Optional[Dict[str, Any]] = None,
        error_handling: Optional[Dict[str, Any]] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update pipeline configuration.

        Args:
            name: Pipeline name
            enabled: Whether the pipeline is enabled
            description: Pipeline description
            parallel: Whether stages can execute in parallel
            resource_limits: Resource usage limits
            error_handling: Error handling configuration
            settings: Pipeline-specific settings
        """
        if name not in self.pipelines:
            raise ValueError(f"Pipeline not found: {name}")

        pipeline = self.pipelines[name]
        config = pipeline.dict()

        # Update configuration
        if enabled is not None:
            config["enabled"] = enabled
        if description is not None:
            config["description"] = description
        if parallel is not None:
            config["execution_settings"]["parallel_execution"] = parallel
        if resource_limits is not None:
            config["resource_limits"] = resource_limits
        if error_handling is not None:
            config["error_handling"] = error_handling
        if settings is not None:
            config["metadata"] = {**config.get("metadata", {}), **settings}

        # Validate updated config
        pipeline_config = PipelineConfig(**config)

        # Store updated pipeline
        self.pipelines[name] = pipeline_config

    def get_pipeline_status(self, name: str) -> PipelineStatus:
        """Get pipeline status.

        Args:
            name: Pipeline name

        Returns:
            Current pipeline status
        """
        if name not in self.pipelines:
            raise ValueError(f"Pipeline not found: {name}")

        # Get pipeline status
        status = PipelineStatus()
        status.running = self.running_pipelines.get(name, False)

        return status

    def add_stage(
        self,
        pipeline_name: str,
        stage_name: str,
        stage_type: str,
        filters: Optional[List[FilterType]] = None,
        inputs: Optional[List[str]] = None,
        outputs: Optional[List[str]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a stage to a pipeline.

        Args:
            pipeline_name: Pipeline name
            stage_name: Unique stage name
            stage_type: Type of stage
            filters: List of filters to apply
            inputs: Names of input stages
            outputs: Names of output stages
            params: Stage-specific parameters
        """
        if pipeline_name not in self.pipelines:
            raise ValueError(f"Pipeline not found: {pipeline_name}")

        pipeline = self.pipelines[pipeline_name]
        stages = list(pipeline.stages)

        # Check for duplicate stage name
        if any(s.name == stage_name for s in stages):
            raise ValueError(f"Stage already exists: {stage_name}")

        # Create stage config
        stage_config = PipelineStage(
            name=stage_name,
            type=stage_type,
            enabled=True,
            filters=filters or [],
            inputs=inputs or [],
            outputs=outputs or [],
            params=params or {},
        )

        # Add stage
        stages.append(stage_config)

        # Update pipeline config
        config = pipeline.dict()
        config["stages"] = [s.dict() for s in stages]
        pipeline_config = PipelineConfig(**config)
        self.pipelines[pipeline_name] = pipeline_config

    def remove_stage(self, pipeline_name: str, stage_name: str) -> None:
        """Remove a stage from a pipeline.

        Args:
            pipeline_name: Pipeline name
            stage_name: Name of stage to remove
        """
        if pipeline_name not in self.pipelines:
            raise ValueError(f"Pipeline not found: {pipeline_name}")

        pipeline = self.pipelines[pipeline_name]
        stages = [s for s in pipeline.stages if s.name != stage_name]

        if len(stages) == len(pipeline.stages):
            raise ValueError(f"Stage not found: {stage_name}")

        # Update pipeline config
        config = pipeline.dict()
        config["stages"] = [s.dict() for s in stages]
        pipeline_config = PipelineConfig(**config)
        self.pipelines[pipeline_name] = pipeline_config

    def start_pipeline(self, name: str) -> None:
        """Start a pipeline.

        Args:
            name: Pipeline name
        """
        if name not in self.pipelines:
            raise ValueError(f"Pipeline not found: {name}")

        pipeline = self.pipelines[name]
        if not pipeline.enabled:
            raise ValueError(f"Pipeline is disabled: {name}")

        # TODO: Implement actual pipeline execution
        self.running_pipelines[name] = True
        self.logger.info(f"Started pipeline: {name}")

    def stop_pipeline(self, name: str) -> None:
        """Stop a pipeline.

        Args:
            name: Pipeline name
        """
        if name not in self.pipelines:
            raise ValueError(f"Pipeline not found: {name}")

        # TODO: Implement actual pipeline stopping
        self.running_pipelines[name] = False
        self.logger.info(f"Stopped pipeline: {name}")

    def validate_pipeline(self, name: str) -> List[str]:
        """Validate pipeline configuration.

        Args:
            name: Pipeline name

        Returns:
            List of validation errors, empty if valid
        """
        if name not in self.pipelines:
            raise ValueError(f"Pipeline not found: {name}")

        pipeline = self.pipelines[name]
        errors = []

        # Check stage connections
        stage_names = {s.name for s in pipeline.stages}
        for stage in pipeline.stages:
            # Check input connections
            for input_name in stage.inputs:
                if input_name not in stage_names:
                    errors.append(
                        f"Stage {stage.name} references non-existent input stage: {input_name}"
                    )

            # Check output connections
            for output_name in stage.outputs:
                if output_name not in stage_names:
                    errors.append(
                        f"Stage {stage.name} references non-existent output stage: {output_name}"
                    )

        # Check for cycles
        try:
            self._check_for_cycles(pipeline)
        except ValueError as e:
            errors.append(str(e))

        return errors

    def _check_for_cycles(self, pipeline: PipelineConfig) -> None:
        """Check for cycles in pipeline graph.

        Args:
            pipeline: Pipeline configuration

        Raises:
            ValueError: If cycle is detected
        """

        def visit(stage_name: str, visited: set, path: set) -> None:
            if stage_name in path:
                raise ValueError(
                    f"Cycle detected in pipeline involving stage: {stage_name}"
                )
            if stage_name in visited:
                return

            visited.add(stage_name)
            path.add(stage_name)

            stage = next(s for s in pipeline.stages if s.name == stage_name)
            for output in stage.outputs:
                visit(output, visited, path)

            path.remove(stage_name)

        visited = set()
        for stage in pipeline.stages:
            if stage.name not in visited:
                visit(stage.name, visited, set())
