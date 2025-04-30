"""Common test fixtures for RTASPI core tests."""

import os
import tempfile
from pathlib import Path
import pytest
import yaml

from rtaspi_core.config import (
    RTASPIConfig,
    create_config_manager,
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def temp_config_dir(temp_dir):
    """Create a temporary configuration directory structure."""
    config_dir = temp_dir / ".rtaspi"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir

@pytest.fixture
def sample_config_data():
    """Return sample configuration data."""
    return {
        "system": {
            "storage_path": "/tmp/rtaspi",
            "log_level": "DEBUG",
        },
        "web": {
            "port": 8080,
            "host": "localhost",
            "enable_https": True,
            "cert_path": "/path/to/cert",
            "key_path": "/path/to/key",
        },
        "streaming": {
            "rtsp": {
                "port_start": 9554,
                "enable_auth": True,
            },
            "webrtc": {
                "stun_server": "stun://custom.server:19302",
            },
        },
        "processing": {
            "video": {
                "default_resolution": "1920x1080",
                "default_fps": 60,
            },
            "audio": {
                "default_sample_rate": 48000,
            },
        },
    }

@pytest.fixture
def config_file(temp_config_dir, sample_config_data):
    """Create a temporary configuration file."""
    config_file = temp_config_dir / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(sample_config_data, f)
    return config_file

@pytest.fixture
def config_manager(temp_config_dir):
    """Create a configuration manager instance with temporary paths."""
    manager = create_config_manager()
    
    # Update config paths to use temporary directory
    manager.config_levels["project"].path = str(temp_config_dir / "config.yaml")
    manager.config_levels["user"].path = str(temp_config_dir / "user.yaml")
    manager.config_levels["global"].path = str(temp_config_dir / "global.yaml")
    
    return manager

@pytest.fixture
def hierarchical_config_files(temp_config_dir):
    """Create a set of hierarchical configuration files."""
    # Global config
    global_config = {
        "system": {"log_level": "INFO"},
        "web": {"port": 8000},
    }
    global_file = temp_config_dir / "global.yaml"
    with open(global_file, "w") as f:
        yaml.dump(global_config, f)

    # User config
    user_config = {
        "web": {"port": 8080},
        "streaming": {"rtsp": {"port_start": 9000}},
    }
    user_file = temp_config_dir / "user.yaml"
    with open(user_file, "w") as f:
        yaml.dump(user_config, f)

    # Project config
    project_config = {
        "system": {"log_level": "DEBUG"},
        "streaming": {"rtsp": {"enable_auth": True}},
    }
    project_file = temp_config_dir / "project.yaml"
    with open(project_file, "w") as f:
        yaml.dump(project_config, f)

    return {
        "global": global_file,
        "user": user_file,
        "project": project_file,
    }

@pytest.fixture
def env_vars():
    """Set up and tear down environment variables for testing."""
    # Store original environment
    original_env = {}
    test_vars = {
        "RTASPI_LOG_LEVEL": "DEBUG",
        "RTASPI_WEB_PORT": "9000",
        "RTASPI_STUN_SERVER": "stun://test.server:19302",
    }

    # Set test environment variables
    for key, value in test_vars.items():
        if key in os.environ:
            original_env[key] = os.environ[key]
        os.environ[key] = value

    yield test_vars

    # Restore original environment
    for key in test_vars:
        if key in original_env:
            os.environ[key] = original_env[key]
        else:
            del os.environ[key]

@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    return RTASPIConfig(
        system={
            "storage_path": "/mock/path",
            "log_level": "DEBUG",
        },
        web={
            "port": 9000,
            "host": "localhost",
        },
    )
