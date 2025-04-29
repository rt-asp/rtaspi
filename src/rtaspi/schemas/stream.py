"""
Schema definitions for stream configurations.

This module provides Pydantic models for validating stream configurations,
including stream sources, outputs, and processing pipelines.
"""

from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field, validator
from rtaspi.constants import OutputType, FilterType


class StreamSource(BaseModel):
    """Configuration for a stream source."""

    device_name: str = Field(..., description="Name of the source device")
    stream_type: str = Field(..., description="Type of stream (video, audio, or both)")
    enabled: bool = Field(True, description="Whether this source is enabled")
    settings: Dict[str, Any] = Field(
        default_factory=dict, description="Source-specific settings"
    )

    @validator("stream_type")
    def validate_stream_type(cls, v):
        """Ensure stream type is valid."""
        valid_types = ["video", "audio", "both"]
        if v not in valid_types:
            raise ValueError(f"Stream type must be one of {valid_types}")
        return v


class StreamFilter(BaseModel):
    """Configuration for a stream filter."""

    type: FilterType = Field(..., description="Type of filter to apply")
    enabled: bool = Field(True, description="Whether this filter is enabled")
    params: Dict[str, Any] = Field(
        default_factory=dict, description="Filter-specific parameters"
    )
    order: int = Field(0, description="Order in which to apply the filter")


class StreamOutput(BaseModel):
    """Configuration for a stream output."""

    type: OutputType = Field(..., description="Type of output")
    enabled: bool = Field(True, description="Whether this output is enabled")
    name: str = Field(..., description="Unique name for this output")
    settings: Dict[str, Any] = Field(
        default_factory=dict, description="Output-specific settings"
    )

    @validator("settings")
    def validate_settings(cls, v, values):
        """Ensure required settings are present based on output type."""
        output_type = values.get("type")
        if output_type:
            if output_type.is_file_output():
                if "path" not in v:
                    raise ValueError("File outputs require 'path' setting")
            elif output_type.is_streaming_output():
                if "url" not in v:
                    raise ValueError("Streaming outputs require 'url' setting")
        return v


class StreamEncoding(BaseModel):
    """Configuration for stream encoding."""

    video_codec: Optional[str] = Field(
        None, description="Video codec to use (e.g., H264, VP8)"
    )
    audio_codec: Optional[str] = Field(
        None, description="Audio codec to use (e.g., AAC, OPUS)"
    )
    video_bitrate: Optional[str] = Field(
        None, description="Video bitrate (e.g., 2M, 5000K)"
    )
    audio_bitrate: Optional[str] = Field(
        None, description="Audio bitrate (e.g., 128K, 256K)"
    )
    framerate: Optional[int] = Field(None, description="Target framerate")
    keyframe_interval: Optional[int] = Field(
        None, description="Keyframe interval in seconds"
    )
    resolution: Optional[str] = Field(
        None, description="Output resolution (e.g., 1920x1080)"
    )


class StreamConfig(BaseModel):
    """Complete stream configuration schema."""

    name: str = Field(..., description="Unique name to identify the stream")
    enabled: bool = Field(True, description="Whether the stream is enabled")
    source: StreamSource = Field(..., description="Stream source configuration")
    filters: List[StreamFilter] = Field(
        default_factory=list, description="List of filters to apply"
    )
    outputs: List[StreamOutput] = Field(
        default_factory=list, description="List of stream outputs"
    )
    encoding: Optional[StreamEncoding] = Field(
        None, description="Stream encoding configuration"
    )
    settings: Dict[str, Any] = Field(
        default_factory=dict, description="Stream-specific settings"
    )

    @validator("filters")
    def validate_filters(cls, v, values):
        """Ensure filters are compatible with stream type."""
        source = values.get("source")
        if source and v:
            stream_type = source.stream_type
            for filter_config in v:
                filter_type = filter_config.type
                if stream_type == "video" and not filter_type.is_video_filter():
                    raise ValueError(f"Filter {filter_type} is not a video filter")
                elif stream_type == "audio" and not filter_type.is_audio_filter():
                    raise ValueError(f"Filter {filter_type} is not an audio filter")
        return sorted(v, key=lambda x: x.order)

    @validator("outputs")
    def validate_outputs(cls, v, values):
        """Ensure outputs are compatible with stream type."""
        source = values.get("source")
        if source and v:
            stream_type = source.stream_type
            for output in v:
                if stream_type == "video" and not output.type.supports_video():
                    raise ValueError(f"Output {output.type} does not support video")
                elif stream_type == "audio" and not output.type.supports_audio():
                    raise ValueError(f"Output {output.type} does not support audio")
        return v


class StreamStatus(BaseModel):
    """Current status of a stream."""

    active: bool = Field(False, description="Whether the stream is currently active")
    error: Optional[str] = Field(
        None, description="Error message if stream is in error state"
    )
    start_time: Optional[str] = Field(
        None, description="ISO timestamp when stream started"
    )
    duration: Optional[int] = Field(None, description="Stream duration in seconds")
    stats: Dict[str, Any] = Field(
        default_factory=dict, description="Stream-specific statistics"
    )
