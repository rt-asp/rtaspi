"""
Schema definitions for processing pipeline configurations.

This module provides Pydantic models for validating processing pipeline configurations,
including pipeline stages, connections, and execution settings.
"""
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field, validator, root_validator
from rtaspi.constants import FilterType


class PipelineStage(BaseModel):
    """Configuration for a pipeline processing stage."""
    
    name: str = Field(
        ...,
        description="Unique name for this stage"
    )
    type: str = Field(
        ...,
        description="Type of processing stage"
    )
    enabled: bool = Field(
        True,
        description="Whether this stage is enabled"
    )
    filters: List[FilterType] = Field(
        default_factory=list,
        description="Filters to apply in this stage"
    )
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Stage-specific parameters"
    )
    inputs: List[str] = Field(
        default_factory=list,
        description="Names of stages that feed into this stage"
    )
    outputs: List[str] = Field(
        default_factory=list,
        description="Names of stages that this stage feeds into"
    )
    
    @validator("type")
    def validate_type(cls, v):
        """Ensure stage type is valid."""
        valid_types = [
            "source",
            "filter",
            "transform",
            "merge",
            "split",
            "output"
        ]
        if v not in valid_types:
            raise ValueError(f"Stage type must be one of {valid_types}")
        return v


class ResourceLimits(BaseModel):
    """Resource limits for pipeline execution."""
    
    max_memory_mb: Optional[int] = Field(
        None,
        description="Maximum memory usage in megabytes"
    )
    max_cpu_percent: Optional[int] = Field(
        None,
        description="Maximum CPU usage percentage"
    )
    max_gpu_memory_mb: Optional[int] = Field(
        None,
        description="Maximum GPU memory usage in megabytes"
    )
    max_threads: Optional[int] = Field(
        None,
        description="Maximum number of threads to use"
    )
    
    @validator("max_cpu_percent")
    def validate_cpu_percent(cls, v):
        """Ensure CPU percentage is valid."""
        if v is not None and not 0 <= v <= 100:
            raise ValueError("CPU percentage must be between 0 and 100")
        return v


class ExecutionSettings(BaseModel):
    """Settings for pipeline execution."""
    
    parallel_execution: bool = Field(
        True,
        description="Whether stages can execute in parallel"
    )
    buffer_size: int = Field(
        1024,
        description="Size of inter-stage buffers"
    )
    timeout_ms: Optional[int] = Field(
        None,
        description="Stage execution timeout in milliseconds"
    )
    retry_count: int = Field(
        3,
        description="Number of times to retry failed stages"
    )
    retry_delay_ms: int = Field(
        1000,
        description="Delay between retries in milliseconds"
    )


class ErrorHandling(BaseModel):
    """Error handling configuration for the pipeline."""
    
    on_error: str = Field(
        "stop",
        description="Action to take on error (stop, continue, retry)"
    )
    error_outputs: List[str] = Field(
        default_factory=list,
        description="Stage names to output errors to"
    )
    log_errors: bool = Field(
        True,
        description="Whether to log errors"
    )
    
    @validator("on_error")
    def validate_on_error(cls, v):
        """Ensure error action is valid."""
        valid_actions = ["stop", "continue", "retry"]
        if v not in valid_actions:
            raise ValueError(f"Error action must be one of {valid_actions}")
        return v


class PipelineConfig(BaseModel):
    """Complete pipeline configuration schema."""
    
    name: str = Field(
        ...,
        description="Unique name to identify the pipeline"
    )
    enabled: bool = Field(
        True,
        description="Whether the pipeline is enabled"
    )
    description: Optional[str] = Field(
        None,
        description="Description of what the pipeline does"
    )
    stages: List[PipelineStage] = Field(
        ...,
        description="List of pipeline processing stages"
    )
    resource_limits: Optional[ResourceLimits] = Field(
        None,
        description="Resource usage limits"
    )
    execution_settings: ExecutionSettings = Field(
        default_factory=ExecutionSettings,
        description="Pipeline execution settings"
    )
    error_handling: ErrorHandling = Field(
        default_factory=ErrorHandling,
        description="Error handling configuration"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional pipeline metadata"
    )
    
    @root_validator
    def validate_pipeline(cls, values):
        """Validate the complete pipeline configuration."""
        if "stages" in values:
            stages = values["stages"]
            stage_names = set()
            
            # Check for duplicate stage names
            for stage in stages:
                if stage.name in stage_names:
                    raise ValueError(f"Duplicate stage name: {stage.name}")
                stage_names.add(stage.name)
            
            # Validate stage connections
            for stage in stages:
                # Check input connections
                for input_name in stage.inputs:
                    if input_name not in stage_names:
                        raise ValueError(
                            f"Stage {stage.name} references non-existent input stage: {input_name}"
                        )
                
                # Check output connections
                for output_name in stage.outputs:
                    if output_name not in stage_names:
                        raise ValueError(
                            f"Stage {stage.name} references non-existent output stage: {output_name}"
                        )
            
            # Check for cycles
            cls._check_for_cycles(stages)
        
        return values
    
    @classmethod
    def _check_for_cycles(cls, stages: List[PipelineStage]):
        """Check for cycles in the pipeline graph."""
        def visit(stage_name: str, visited: set, path: set) -> None:
            if stage_name in path:
                raise ValueError(f"Cycle detected in pipeline involving stage: {stage_name}")
            if stage_name in visited:
                return
            
            visited.add(stage_name)
            path.add(stage_name)
            
            stage = next(s for s in stages if s.name == stage_name)
            for output in stage.outputs:
                visit(output, visited, path)
            
            path.remove(stage_name)
        
        visited = set()
        for stage in stages:
            if stage.name not in visited:
                visit(stage.name, visited, set())


class PipelineStatus(BaseModel):
    """Current status of a pipeline."""
    
    running: bool = Field(
        False,
        description="Whether the pipeline is currently running"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if pipeline is in error state"
    )
    start_time: Optional[str] = Field(
        None,
        description="ISO timestamp when pipeline started"
    )
    stage_statuses: Dict[str, str] = Field(
        default_factory=dict,
        description="Status of each pipeline stage"
    )
    stats: Dict[str, Any] = Field(
        default_factory=dict,
        description="Pipeline-specific statistics"
    )
