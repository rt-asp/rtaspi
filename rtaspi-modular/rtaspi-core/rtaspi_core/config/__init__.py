"""Configuration management for RTASPI core module."""

from typing import Dict, Any, Optional

from .manager import ConfigManager, ConfigurationError, ConfigLoadError, ConfigValidationError, ConfigSaveError
from .models import (
    RTASPIConfig,
    SystemConfig,
    StreamingConfig,
    ProcessingConfig,
    WebConfig,
    LocalDevicesConfig,
    NetworkDevicesConfig,
)

# Default configuration with protocol types
DEFAULT_CONFIG: Dict[str, Any] = {
    "enums": {
        "ProtocolType": {
            "HTTP": "http",
            "HTTPS": "https",
            "RTSP": "rtsp",
            "RTMP": "rtmp",
            "RTMPS": "rtmps",
            "WEBRTC": "webrtc",
            "HLS": "hls",
            "MPEG_DASH": "dash",
            "SRT": "srt",
            "ONVIF": "onvif",
            "UPNP": "upnp",
            "MDNS": "mdns",
            "SSDP": "ssdp",
            "WS_DISCOVERY": "ws-discovery",
            "SSH": "ssh",
            "TELNET": "telnet",
            "FTP": "ftp",
            "SFTP": "sftp",
            "MQTT": "mqtt",
            "WEBSOCKET": "ws",
            "WEBSOCKET_SECURE": "wss",
            "BASIC_AUTH": "basic",
            "DIGEST_AUTH": "digest",
            "OAUTH2": "oauth2",
            "JWT": "jwt"
        }
    }
}

# Environment variable mappings
ENV_VARIABLE_MAP: Dict[str, str] = {
    "RTASPI_STORAGE_PATH": "system.storage_path",
    "RTASPI_LOG_LEVEL": "system.log_level",
    "RTASPI_WEB_PORT": "web.port",
    "RTASPI_WEB_HOST": "web.host",
    "RTASPI_ENABLE_HTTPS": "web.enable_https",
    "RTASPI_CERT_PATH": "web.cert_path",
    "RTASPI_KEY_PATH": "web.key_path",
    "RTASPI_STUN_SERVER": "streaming.webrtc.stun_server",
    "RTASPI_TURN_SERVER": "streaming.webrtc.turn_server",
    "RTASPI_TURN_USERNAME": "streaming.webrtc.turn_username",
    "RTASPI_TURN_PASSWORD": "streaming.webrtc.turn_password",
}

def create_config_manager(
    config_model: Optional[type[RTASPIConfig]] = None,
    default_config: Optional[Dict[str, Any]] = None,
    env_map: Optional[Dict[str, str]] = None
) -> ConfigManager[RTASPIConfig]:
    """Create a new configuration manager instance.
    
    Args:
        config_model: Optional custom configuration model
        default_config: Optional custom default configuration
        env_map: Optional custom environment variable mappings
        
    Returns:
        ConfigManager instance
    """
    return ConfigManager(
        config_model=config_model or RTASPIConfig,
        default_config=default_config or DEFAULT_CONFIG,
        env_map=env_map or ENV_VARIABLE_MAP
    )

# Default configuration manager instance
config_manager = create_config_manager()

__all__ = [
    "ConfigManager",
    "ConfigurationError",
    "ConfigLoadError",
    "ConfigValidationError",
    "ConfigSaveError",
    "RTASPIConfig",
    "SystemConfig",
    "StreamingConfig",
    "ProcessingConfig",
    "WebConfig",
    "LocalDevicesConfig",
    "NetworkDevicesConfig",
    "create_config_manager",
    "config_manager",
]
