"""
stream.py - Stream configuration schemas
"""

from typing import List, Optional, Union, Dict
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum


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


class StreamConfig(BaseModel):
    """Stream configuration schema."""

    id: str = Field(..., description="Unique stream identifier")
    name: str = Field(..., description="Human-readable stream name")
    type: StreamType = Field(..., description="Type of stream")
    enabled: bool = True

    # Source configuration
    source_device: str = Field(..., description="Source device identifier")
    source_format: Optional[StreamFormat] = None

    # Processing settings
    enable_preprocessing: bool = False
    preprocessing_filters: List[dict] = Field(default_factory=list)
    enable_postprocessing: bool = False
    postprocessing_filters: List[dict] = Field(default_factory=list)

    # Output configuration
    outputs: List[StreamOutput] = Field(default_factory=list)

    # Additional settings
    buffer_size: Optional[int] = None
    reconnect_delay: int = 5
    max_reconnect_attempts: int = 3
    metadata: dict = Field(default_factory=dict)

    @field_validator("buffer_size", "reconnect_delay", "max_reconnect_attempts")
    def validate_positive(cls, v, info):
        """Validate numeric fields are positive."""
        if v is not None and v <= 0:
            raise ValueError(f"{info.field_name} must be positive")
        return v

    @model_validator(mode="after")
    def validate_stream_type(self) -> "StreamConfig":
        """Validate stream type matches source device and formats."""
        if self.type and self.source_format:
            video_formats = {
                StreamFormat.H264,
                StreamFormat.H265,
                StreamFormat.VP8,
                StreamFormat.VP9,
                StreamFormat.MJPEG,
                StreamFormat.RAW,
            }
            audio_formats = {
                StreamFormat.AAC,
                StreamFormat.MP3,
                StreamFormat.OPUS,
                StreamFormat.PCM,
                StreamFormat.VORBIS,
            }

            if self.type == StreamType.VIDEO and self.source_format in audio_formats:
                raise ValueError("Video stream cannot use audio format")
            elif self.type == StreamType.AUDIO and self.source_format in video_formats:
                raise ValueError("Audio stream cannot use video format")

        return self


class StreamList(BaseModel):
    """List of stream configurations."""

    streams: List[StreamConfig] = Field(default_factory=list)
