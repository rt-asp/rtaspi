"""
defaults.py - Default configuration values for rtaspi
"""

DEFAULT_CONFIG = {
    "system": {
        "storage_path": "storage",
        "log_level": "INFO",
        "config_paths": {
            "global": "/etc/rtaspi/config.yaml",
            "user": "~/.config/rtaspi/config.yaml",
            "project": ".rtaspi/config.yaml"
        }
    },
    "local_devices": {
        "enable_video": True,
        "enable_audio": True,
        "auto_start": False,
        "scan_interval": 60,
        "rtsp_port_start": 8554,
        "rtmp_port_start": 1935,
        "webrtc_port_start": 8080
    },
    "network_devices": {
        "enable": True,
        "scan_interval": 60,
        "discovery_enabled": True,
        "discovery_methods": ["onvif", "upnp", "mdns"],
        "rtsp_port_start": 8654,
        "rtmp_port_start": 2935,
        "webrtc_port_start": 9080
    },
    "streaming": {
        "rtsp": {
            "port_start": 8554,
            "enable_auth": False,
            "auth_method": "basic"
        },
        "rtmp": {
            "port_start": 1935,
            "enable_auth": False
        },
        "webrtc": {
            "port_start": 8080,
            "stun_server": "stun://stun.l.google.com:19302",
            "turn_server": "",
            "turn_username": "",
            "turn_password": ""
        }
    },
    "processing": {
        "video": {
            "default_resolution": "1280x720",
            "default_fps": 30,
            "default_format": "h264"
        },
        "audio": {
            "default_sample_rate": 44100,
            "default_channels": 2,
            "default_format": "aac"
        }
    },
    "web": {
        "enable": True,
        "host": "0.0.0.0",
        "port": 8000,
        "enable_https": False,
        "cert_path": "",
        "key_path": "",
        "enable_auth": False,
        "auth_method": "basic",
        "session_timeout": 3600
    }
}

ENV_VARIABLE_MAP = {
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
    "RTASPI_TURN_PASSWORD": "streaming.webrtc.turn_password"
}
