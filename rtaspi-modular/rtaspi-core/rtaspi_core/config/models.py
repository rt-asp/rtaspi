"""Configuration models for RTASPI core module."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class SystemConfig(BaseModel):
    """System-wide configuration settings."""
    storage_path: str = "storage"
    log_level: str = "INFO"
    config_paths: Dict[str, str] = Field(
        default_factory=lambda: {
            "global": "/etc/rtaspi/config.yaml",
            "user": "~/.config/rtaspi/config.yaml",
            "project": ".rtaspi/config.yaml",
        }
    )

class WebRTCConfig(BaseModel):
    """WebRTC configuration settings."""
    port_start: int = 8080
    stun_server: str = "stun://stun.l.google.com:19302"
    turn_server: str = ""
    turn_username: str = ""
    turn_password: str = ""

class StreamingProtocolConfig(BaseModel):
    """Base streaming protocol configuration."""
    port_start: int
    enable_auth: bool = False
    auth_method: Optional[str] = None

class StreamingConfig(BaseModel):
    """Streaming configuration settings."""
    rtsp: StreamingProtocolConfig = Field(
        default_factory=lambda: StreamingProtocolConfig(
            port_start=8554,
            enable_auth=False,
            auth_method="basic"
        )
    )
    rtmp: StreamingProtocolConfig = Field(
        default_factory=lambda: StreamingProtocolConfig(
            port_start=1935,
            enable_auth=False
        )
    )
    webrtc: WebRTCConfig = Field(default_factory=WebRTCConfig)

class VideoConfig(BaseModel):
    """Video processing configuration."""
    default_resolution: str = "1280x720"
    default_fps: int = 30
    default_format: str = "h264"

class AudioConfig(BaseModel):
    """Audio processing configuration."""
    default_sample_rate: int = 44100
    default_channels: int = 2
    default_format: str = "aac"

class ProcessingConfig(BaseModel):
    """Media processing configuration."""
    video: VideoConfig = Field(default_factory=VideoConfig)
    audio: AudioConfig = Field(default_factory=AudioConfig)

class WebConfig(BaseModel):
    """Web interface configuration."""
    enable: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    enable_https: bool = False
    cert_path: str = ""
    key_path: str = ""
    enable_auth: bool = False
    auth_method: str = "basic"
    session_timeout: int = 3600

class LocalDevicesConfig(BaseModel):
    """Local devices configuration."""
    enable_video: bool = True
    enable_audio: bool = True
    auto_start: bool = False
    scan_interval: int = 60
    rtsp_port_start: int = 8554
    rtmp_port_start: int = 1935
    webrtc_port_start: int = 8080

class NetworkDevicesConfig(BaseModel):
    """Network devices configuration."""
    enable: bool = True
    scan_interval: int = 60
    discovery_enabled: bool = True
    discovery_methods: List[str] = Field(default_factory=lambda: ["onvif", "upnp", "mdns"])
    rtsp_port_start: int = 8654
    rtmp_port_start: int = 2935
    webrtc_port_start: int = 9080

class RTASPIConfig(BaseModel):
    """Complete RTASPI configuration model."""
    system: SystemConfig = Field(default_factory=SystemConfig)
    enums: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    local_devices: LocalDevicesConfig = Field(default_factory=LocalDevicesConfig)
    network_devices: NetworkDevicesConfig = Field(default_factory=NetworkDevicesConfig)
    streaming: StreamingConfig = Field(default_factory=StreamingConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    web: WebConfig = Field(default_factory=WebConfig)

    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            # Add custom encoders if needed
        }
