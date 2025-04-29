"""
device.py - Device configuration schemas
"""

from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class DeviceType(str, Enum):
    """Device types supported by rtaspi."""
    CAMERA = "camera"
    MICROPHONE = "microphone"
    VIRTUAL_CAMERA = "virtual_camera"
    VIRTUAL_MICROPHONE = "virtual_microphone"


class DeviceProtocol(str, Enum):
    """Supported device protocols."""
    V4L2 = "v4l2"  # Linux video devices
    ALSA = "alsa"  # Linux audio devices
    DSHOW = "dshow"  # Windows DirectShow
    AVFOUNDATION = "avfoundation"  # macOS AVFoundation
    RTSP = "rtsp"  # Network RTSP devices
    ONVIF = "onvif"  # Network ONVIF devices
    VIRTUAL = "virtual"  # Virtual devices


class DeviceAuth(BaseModel):
    """Device authentication configuration."""
    username: Optional[str] = None
    password: Optional[str] = None
    token: Optional[str] = None
    method: str = "basic"  # basic, digest, token


class DeviceCapabilities(BaseModel):
    """Device capabilities configuration."""
    video: bool = False
    audio: bool = False
    ptz: bool = False
    infrared: bool = False
    motion_detection: bool = False
    audio_detection: bool = False
    formats: List[str] = Field(default_factory=list)
    resolutions: List[str] = Field(default_factory=list)
    framerates: List[int] = Field(default_factory=list)
    audio_formats: List[str] = Field(default_factory=list)
    audio_rates: List[int] = Field(default_factory=list)
    audio_channels: List[int] = Field(default_factory=list)


class DeviceConfig(BaseModel):
    """Device configuration schema."""
    id: str = Field(..., description="Unique device identifier")
    name: str = Field(..., description="Human-readable device name")
    type: DeviceType = Field(..., description="Type of device")
    protocol: DeviceProtocol = Field(..., description="Device protocol")
    enabled: bool = True
    path: Optional[str] = Field(None, description="Device path or URL")
    index: Optional[int] = Field(None, description="Device index for local devices")
    
    # Authentication
    auth: Optional[DeviceAuth] = None
    
    # Capabilities and settings
    capabilities: DeviceCapabilities = Field(default_factory=DeviceCapabilities)
    preferred_format: Optional[str] = None
    preferred_resolution: Optional[str] = None
    preferred_framerate: Optional[int] = None
    preferred_audio_format: Optional[str] = None
    preferred_audio_rate: Optional[int] = None
    preferred_audio_channels: Optional[int] = None
    
    # Network device specific
    host: Optional[str] = None
    port: Optional[int] = None
    discovery_info: Optional[dict] = None
    
    # Virtual device specific
    source_device: Optional[str] = None
    virtual_type: Optional[str] = None
    
    # Additional settings
    settings: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)

    @field_validator("preferred_resolution")
    def validate_resolution(cls, v, info):
        """Validate resolution format (e.g., '1920x1080')."""
        if v is not None:
            try:
                width, height = map(int, v.split("x"))
                if width <= 0 or height <= 0:
                    raise ValueError
                return v
            except (ValueError, AttributeError):
                raise ValueError("Resolution must be in format 'WIDTHxHEIGHT'")
        return v

    @field_validator("preferred_framerate")
    def validate_framerate(cls, v, info):
        """Validate framerate is positive."""
        if v is not None and v <= 0:
            raise ValueError("Framerate must be positive")
        return v

    @field_validator("preferred_audio_rate")
    def validate_audio_rate(cls, v, info):
        """Validate audio sample rate is positive."""
        if v is not None and v <= 0:
            raise ValueError("Audio sample rate must be positive")
        return v

    @field_validator("preferred_audio_channels")
    def validate_audio_channels(cls, v, info):
        """Validate audio channels is positive."""
        if v is not None and v <= 0:
            raise ValueError("Audio channels must be positive")
        return v


class DeviceList(BaseModel):
    """List of device configurations."""
    devices: List[DeviceConfig] = Field(default_factory=list)
