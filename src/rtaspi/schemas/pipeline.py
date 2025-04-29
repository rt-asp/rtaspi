"""
pipeline.py - Pipeline configuration schemas
"""

from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum


class PipelineType(str, Enum):
    """Pipeline types supported by rtaspi."""
    VIDEO = "video"
    AUDIO = "audio"
    MIXED = "mixed"
    DETECTION = "detection"
    ANALYSIS = "analysis"


class FilterType(str, Enum):
    """Supported filter types."""
    # Video filters
    RESIZE = "resize"
    CROP = "crop"
    ROTATE = "rotate"
    FLIP = "flip"
    BRIGHTNESS = "brightness"
    CONTRAST = "contrast"
    SATURATION = "saturation"
    HUE = "hue"
    DENOISE = "denoise"
    SHARPEN = "sharpen"
    BLUR = "blur"
    
    # Audio filters
    VOLUME = "volume"
    EQUALIZER = "equalizer"
    NOISE_REDUCTION = "noise_reduction"
    COMPRESSOR = "compressor"
    NORMALIZER = "normalizer"
    
    # Detection filters
    FACE_DETECTION = "face_detection"
    OBJECT_DETECTION = "object_detection"
    MOTION_DETECTION = "motion_detection"
    AUDIO_DETECTION = "audio_detection"
    
    # Analysis filters
    SCENE_ANALYSIS = "scene_analysis"
    AUDIO_ANALYSIS = "audio_analysis"
    METADATA_ANALYSIS = "metadata_analysis"


class FilterConfig(BaseModel):
    """Filter configuration."""
    type: FilterType
    enabled: bool = True
    parameters: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PipelineStage(BaseModel):
    """Pipeline stage configuration."""
    name: str
    enabled: bool = True
    filters: List[FilterConfig] = Field(default_factory=list)
    parallel: bool = False
    timeout: Optional[float] = None
    retry_count: int = 0
    error_handling: str = "stop"  # stop, skip, retry
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("timeout")
    def validate_timeout(cls, v, info):
        """Validate timeout is positive."""
        if v is not None and v <= 0:
            raise ValueError("Timeout must be positive")
        return v

    @field_validator("retry_count")
    def validate_retry_count(cls, v, info):
        """Validate retry count is non-negative."""
        if v < 0:
            raise ValueError("Retry count must be non-negative")
        return v

    @field_validator("error_handling")
    def validate_error_handling(cls, v, info):
        """Validate error handling strategy."""
        valid_strategies = {"stop", "skip", "retry"}
        if v not in valid_strategies:
            raise ValueError(f"Error handling must be one of: {valid_strategies}")
        return v


class ResourceLimits(BaseModel):
    """Resource limits configuration."""
    max_memory: Optional[int] = None  # in MB
    max_cpu: Optional[float] = None  # percentage (0-100)
    max_gpu: Optional[float] = None  # percentage (0-100)
    max_threads: Optional[int] = None
    priority: int = 0  # -20 to 19, lower is higher priority

    @field_validator("max_memory", "max_threads")
    def validate_positive(cls, v, info):
        """Validate numeric fields are positive."""
        if v is not None and v <= 0:
            raise ValueError("Resource limit must be positive")
        return v

    @field_validator("max_cpu", "max_gpu")
    def validate_percentage(cls, v, info):
        """Validate percentage is between 0 and 100."""
        if v is not None and (v < 0 or v > 100):
            raise ValueError("Percentage must be between 0 and 100")
        return v

    @field_validator("priority")
    def validate_priority(cls, v, info):
        """Validate priority is in valid range."""
        if v < -20 or v > 19:
            raise ValueError("Priority must be between -20 and 19")
        return v


class PipelineConfig(BaseModel):
    """Pipeline configuration schema."""
    id: str = Field(..., description="Unique pipeline identifier")
    name: str = Field(..., description="Human-readable pipeline name")
    type: PipelineType = Field(..., description="Type of pipeline")
    enabled: bool = True
    
    # Input configuration
    input_streams: List[str] = Field(..., description="List of input stream IDs")
    
    # Processing configuration
    stages: List[PipelineStage] = Field(..., description="Pipeline processing stages")
    
    # Output configuration
    output_streams: List[str] = Field(default_factory=list, description="List of output stream IDs")
    save_results: bool = False
    results_path: Optional[str] = None
    
    # Resource management
    resource_limits: ResourceLimits = Field(default_factory=ResourceLimits)
    
    # Error handling
    error_handling: str = "stop"  # stop, skip, retry
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Additional settings
    buffer_size: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("max_retries")
    def validate_max_retries(cls, v, info):
        """Validate max retries is non-negative."""
        if v < 0:
            raise ValueError("Max retries must be non-negative")
        return v

    @field_validator("retry_delay")
    def validate_retry_delay(cls, v, info):
        """Validate retry delay is positive."""
        if v <= 0:
            raise ValueError("Retry delay must be positive")
        return v

    @field_validator("buffer_size")
    def validate_buffer_size(cls, v, info):
        """Validate buffer size is positive."""
        if v is not None and v <= 0:
            raise ValueError("Buffer size must be positive")
        return v

    @model_validator(mode='after')
    def validate_pipeline(self) -> 'PipelineConfig':
        """Validate pipeline configuration."""
        if self.type and self.stages:
            # Validate filter types match pipeline type
            for stage in self.stages:
                for filter_config in stage.filters:
                    if self.type == PipelineType.VIDEO:
                        if filter_config.type.value.endswith(("_detection", "_analysis")):
                            continue
                        if not any(filter_config.type.value.startswith(prefix) 
                                 for prefix in ["resize", "crop", "rotate", "flip", 
                                              "brightness", "contrast", "saturation", 
                                              "hue", "denoise", "sharpen", "blur"]):
                            raise ValueError(f"Invalid filter type {filter_config.type} for video pipeline")
                    elif self.type == PipelineType.AUDIO:
                        if not any(filter_config.type.value.startswith(prefix) 
                                 for prefix in ["volume", "equalizer", "noise_reduction", 
                                              "compressor", "normalizer"]):
                            raise ValueError(f"Invalid filter type {filter_config.type} for audio pipeline")
        
        return self


class PipelineList(BaseModel):
    """List of pipeline configurations."""
    pipelines: List[PipelineConfig] = Field(default_factory=list)
