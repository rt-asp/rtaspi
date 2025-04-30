"""Tests for configuration models."""

import pytest
from pydantic import ValidationError

from rtaspi_core.config.models import (
    RTASPIConfig,
    SystemConfig,
    WebConfig,
    StreamingConfig,
    ProcessingConfig,
    LocalDevicesConfig,
    NetworkDevicesConfig,
)

def test_system_config_defaults():
    """Test SystemConfig default values."""
    config = SystemConfig()
    assert config.storage_path == "storage"
    assert config.log_level == "INFO"
    assert config.config_paths == {
        "global": "/etc/rtaspi/config.yaml",
        "user": "~/.config/rtaspi/config.yaml",
        "project": ".rtaspi/config.yaml",
    }

def test_web_config_defaults():
    """Test WebConfig default values."""
    config = WebConfig()
    assert config.enable is True
    assert config.host == "0.0.0.0"
    assert config.port == 8000
    assert config.enable_https is False
    assert config.cert_path == ""
    assert config.key_path == ""
    assert config.enable_auth is False
    assert config.auth_method == "basic"
    assert config.session_timeout == 3600

def test_streaming_config_defaults():
    """Test StreamingConfig default values."""
    config = StreamingConfig()
    assert config.rtsp.port_start == 8554
    assert config.rtmp.port_start == 1935
    assert config.webrtc.port_start == 8080
    assert config.webrtc.stun_server == "stun://stun.l.google.com:19302"

def test_processing_config_defaults():
    """Test ProcessingConfig default values."""
    config = ProcessingConfig()
    assert config.video.default_resolution == "1280x720"
    assert config.video.default_fps == 30
    assert config.video.default_format == "h264"
    assert config.audio.default_sample_rate == 44100
    assert config.audio.default_channels == 2
    assert config.audio.default_format == "aac"

def test_local_devices_config_defaults():
    """Test LocalDevicesConfig default values."""
    config = LocalDevicesConfig()
    assert config.enable_video is True
    assert config.enable_audio is True
    assert config.auto_start is False
    assert config.scan_interval == 60
    assert config.rtsp_port_start == 8554
    assert config.rtmp_port_start == 1935
    assert config.webrtc_port_start == 8080

def test_network_devices_config_defaults():
    """Test NetworkDevicesConfig default values."""
    config = NetworkDevicesConfig()
    assert config.enable is True
    assert config.scan_interval == 60
    assert config.discovery_enabled is True
    assert config.discovery_methods == ["onvif", "upnp", "mdns"]
    assert config.rtsp_port_start == 8654
    assert config.rtmp_port_start == 2935
    assert config.webrtc_port_start == 9080

def test_rtaspi_config_defaults():
    """Test RTASPIConfig default values."""
    config = RTASPIConfig()
    assert isinstance(config.system, SystemConfig)
    assert isinstance(config.web, WebConfig)
    assert isinstance(config.streaming, StreamingConfig)
    assert isinstance(config.processing, ProcessingConfig)
    assert isinstance(config.local_devices, LocalDevicesConfig)
    assert isinstance(config.network_devices, NetworkDevicesConfig)

def test_rtaspi_config_validation():
    """Test RTASPIConfig validation."""
    # Test invalid log level
    with pytest.raises(ValidationError):
        RTASPIConfig(system={"log_level": "INVALID"})

    # Test invalid port number
    with pytest.raises(ValidationError):
        RTASPIConfig(web={"port": -1})

    # Test invalid resolution format
    with pytest.raises(ValidationError):
        RTASPIConfig(processing={"video": {"default_resolution": "invalid"}})

def test_rtaspi_config_custom_values():
    """Test RTASPIConfig with custom values."""
    config = RTASPIConfig(
        system={
            "storage_path": "/custom/path",
            "log_level": "DEBUG",
        },
        web={
            "port": 9000,
            "host": "localhost",
            "enable_https": True,
            "cert_path": "/path/to/cert",
            "key_path": "/path/to/key",
        },
        streaming={
            "rtsp": {
                "port_start": 9554,
                "enable_auth": True,
            },
            "webrtc": {
                "stun_server": "stun://custom.server:19302",
            },
        },
    )

    assert config.system.storage_path == "/custom/path"
    assert config.system.log_level == "DEBUG"
    assert config.web.port == 9000
    assert config.web.host == "localhost"
    assert config.web.enable_https is True
    assert config.web.cert_path == "/path/to/cert"
    assert config.web.key_path == "/path/to/key"
    assert config.streaming.rtsp.port_start == 9554
    assert config.streaming.rtsp.enable_auth is True
    assert config.streaming.webrtc.stun_server == "stun://custom.server:19302"

def test_config_dict_conversion():
    """Test conversion to and from dictionary."""
    original_config = RTASPIConfig(
        system={"storage_path": "/custom/path"},
        web={"port": 9000},
    )

    # Convert to dict
    config_dict = original_config.dict()
    assert isinstance(config_dict, dict)
    assert config_dict["system"]["storage_path"] == "/custom/path"
    assert config_dict["web"]["port"] == 9000

    # Create new config from dict
    new_config = RTASPIConfig.model_validate(config_dict)
    assert new_config.system.storage_path == "/custom/path"
    assert new_config.web.port == 9000

def test_nested_config_validation():
    """Test validation of nested configuration."""
    with pytest.raises(ValidationError):
        RTASPIConfig(
            streaming={
                "rtsp": {
                    "port_start": "invalid",  # Should be int
                },
            }
        )

    with pytest.raises(ValidationError):
        RTASPIConfig(
            processing={
                "video": {
                    "default_fps": -1,  # Invalid FPS
                },
            }
        )

def test_config_immutability():
    """Test that config objects are immutable after creation."""
    config = RTASPIConfig()
    
    # Direct attribute modification should raise error
    with pytest.raises(Exception):
        config.system.log_level = "DEBUG"

    # Dictionary modification should create new instance
    modified = RTASPIConfig.model_validate({
        **config.dict(),
        "system": {"log_level": "DEBUG"},
    })
    assert modified.system.log_level == "DEBUG"
    assert config.system.log_level == "INFO"  # Original unchanged
