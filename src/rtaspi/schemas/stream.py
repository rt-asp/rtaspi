"""
stream.py - Stream configuration schemas
"""

from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum
from datetime import datetime


class StreamType(str, Enum):
    """Stream types supported by rtaspi."""

    VIDEO = "video"
    AUDIO = "audio"
    MIXED = "mixed"


class StreamProtocol(str, Enum):
    """Supported streaming protocols."""

    RTSP = "rtsp"
    RTMP = "rtmp"
    WEBRTC = "webrtc"
    FILE = "file"
    HTTP = "http"
    HLS = "hls"
    DASH = "dash"


class StreamFormat(str, Enum):
    """Supported stream formats."""

    # Video formats
    H264 = "h264"
    H265 = "h265"
    VP8 = "vp8"
    VP9 = "vp9"
    MJPEG = "mjpeg"
    RAW = "raw"

    # Audio formats
    AAC = "aac"
    MP3 = "mp3"
    OPUS = "opus"
    PCM = "pcm"
    VORBIS = "vorbis"


class StreamQuality(BaseModel):
    """Stream quality configuration."""

    resolution: Optional[str] = None
    framerate: Optional[int] = None
    bitrate: Optional[int] = None
    keyframe_interval: Optional[int] = None
    audio_bitrate: Optional[int] = None
    audio_channels: Optional[int] = None
    audio_sample_rate: Optional[int] = None

    @field_validator("resolution")
    def validate_resolution(cls, v):
        """Validate resolution format."""
        if v is not None:
            try:
                width, height = map(int, v.split("x"))
                if width <= 0 or height <= 0:
                    raise ValueError
                return v
            except (ValueError, AttributeError):
                raise ValueError("Resolution must be in format 'WIDTHxHEIGHT'")
        return v

    @field_validator(
        "framerate",
        "bitrate",
        "keyframe_interval",
        "audio_bitrate",
        "audio_channels",
        "audio_sample_rate",
    )
    def validate_positive(cls, v, info):
        """Validate numeric fields are positive."""
        if v is not None and v <= 0:
            raise ValueError(f"{info.field_name} must be positive")
        return v


class StreamAuth(BaseModel):
    """Stream authentication configuration."""

    enabled: bool = False
    method: str = "basic"  # basic, digest, token
    username: Optional[str] = None
    password: Optional[str] = None
    token: Optional[str] = None


class StreamOutput(BaseModel):
    """Stream output configuration."""

    protocol: StreamProtocol
    path: str
    format: StreamFormat
    quality: StreamQuality = Field(default_factory=StreamQuality)
    auth: StreamAuth = Field(default_factory=StreamAuth)
    options: Dict[str, Union[str, int, bool, float]] = Field(default_factory=dict)


class StreamSource(BaseModel):
    """Stream source configuration."""

    device_name: str = Field(..., description="Source device name")
    stream_type: StreamType = Field(..., description="Type of stream")
    enabled: bool = True
    format: Optional[StreamFormat] = None
    settings: Dict[str, Any] = Field(default_factory=dict)


class StreamFilter(BaseModel):
    """Stream filter configuration."""

    type: str = Field(..., description="Filter type")
    enabled: bool = True
    order: int = Field(0, description="Filter execution order")
    params: Dict[str, Any] = Field(default_factory=dict)


class StreamStatus(BaseModel):
    """Stream status information."""

    active: bool = Field(False, description="Whether stream is active")
    error: Optional[str] = Field(None, description="Last error message if any")
    start_time: Optional[datetime] = Field(None, description="Stream start time")
    duration: Optional[float] = Field(None, description="Stream duration in seconds")
    stats: Dict[str, Any] = Field(default_factory=dict, description="Stream statistics")


class StreamConfig(BaseModel):
    """Stream configuration schema."""

    name: str = Field(..., description="Stream name")
    enabled: bool = True
    source: StreamSource
    filters: List[StreamFilter] = Field(default_factory=list)
    outputs: List[StreamOutput] = Field(default_factory=list)
    settings: Dict[str, Any] = Field(default_factory=dict)


class StreamList(BaseModel):
    """List of stream configurations."""

    streams: List[StreamConfig] = Field(default_factory=list)
