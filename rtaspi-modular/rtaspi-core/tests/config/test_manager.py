"""Tests for the configuration management system."""

import os
import tempfile
from pathlib import Path
import pytest
from pydantic import ValidationError

from rtaspi_core.config import (
    ConfigManager,
    RTASPIConfig,
    ConfigLoadError,
    ConfigValidationError,
    create_config_manager,
)

@pytest.fixture
def temp_config_file():
    """Create a temporary configuration file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
system:
  storage_path: "/tmp/rtaspi"
  log_level: "DEBUG"
web:
  port: 8080
  host: "localhost"
""")
        path = f.name
    yield path
    os.unlink(path)

@pytest.fixture
def config_manager():
    """Create a configuration manager instance."""
    return create_config_manager()

def test_config_manager_initialization():
    """Test basic initialization of ConfigManager."""
    manager = create_config_manager()
    assert isinstance(manager.config, RTASPIConfig)
    assert manager.config.system.log_level == "INFO"  # Default value

def test_load_config_file(config_manager, temp_config_file):
    """Test loading configuration from file."""
    assert config_manager.load_config_file(temp_config_file)
    assert config_manager.config.system.storage_path == "/tmp/rtaspi"
    assert config_manager.config.system.log_level == "DEBUG"
    assert config_manager.config.web.port == 8080
    assert config_manager.config.web.host == "localhost"

def test_get_config_value(config_manager, temp_config_file):
    """Test getting configuration values."""
    config_manager.load_config_file(temp_config_file)
    assert config_manager.get("system.storage_path") == "/tmp/rtaspi"
    assert config_manager.get("web.port") == 8080
    assert config_manager.get("nonexistent.key", "default") == "default"

def test_set_config_value(config_manager):
    """Test setting configuration values."""
    assert config_manager.set("system.log_level", "DEBUG")
    assert config_manager.get("system.log_level") == "DEBUG"

def test_environment_variables(config_manager, monkeypatch):
    """Test environment variable integration."""
    monkeypatch.setenv("RTASPI_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("RTASPI_WEB_PORT", "9000")
    
    # Create new manager to pick up environment variables
    manager = create_config_manager()
    assert manager.config.system.log_level == "DEBUG"
    assert manager.config.web.port == 9000

def test_invalid_config_file(config_manager):
    """Test handling of invalid configuration file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("invalid: yaml: content")
        path = f.name

    try:
        with pytest.raises(ConfigLoadError):
            config_manager.load_config_file(path)
    finally:
        os.unlink(path)

def test_validation_error():
    """Test configuration validation."""
    with pytest.raises(ConfigValidationError):
        ConfigManager(
            config_model=RTASPIConfig,
            default_config={"system": {"log_level": 123}}  # Invalid type for log_level
        )

def test_save_config(config_manager, temp_config_file):
    """Test saving configuration to file."""
    # Load initial config
    config_manager.load_config_file(temp_config_file)
    
    # Modify and save to new file
    new_file = Path(temp_config_file).parent / "new_config.yaml"
    config_manager.set("system.log_level", "DEBUG")
    config_manager.config_levels["project"].path = str(new_file)
    
    try:
        assert config_manager.save_config("project")
        assert new_file.exists()
        
        # Load the saved config in a new manager to verify
        new_manager = create_config_manager()
        new_manager.load_config_file(str(new_file))
        assert new_manager.config.system.log_level == "DEBUG"
    finally:
        if new_file.exists():
            new_file.unlink()

def test_hierarchical_config(temp_config_file):
    """Test hierarchical configuration loading."""
    # Create a global config
    global_config = """
system:
  log_level: "INFO"
web:
  port: 8000
"""
    # Create a user config
    user_config = """
web:
  port: 8080
"""
    # Create a project config
    project_config = """
system:
  log_level: "DEBUG"
"""

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create config files
        global_path = Path(temp_dir) / "global.yaml"
        user_path = Path(temp_dir) / "user.yaml"
        project_path = Path(temp_dir) / "project.yaml"

        global_path.write_text(global_config)
        user_path.write_text(user_config)
        project_path.write_text(project_config)

        # Create manager with custom paths
        manager = ConfigManager(
            config_model=RTASPIConfig,
            default_config={},
            env_map={}
        )
        manager.config_levels["global"].path = str(global_path)
        manager.config_levels["user"].path = str(user_path)
        manager.config_levels["project"].path = str(project_path)

        # Reload config
        manager.config = manager._load_hierarchical_config()

        # Verify hierarchy (project overrides user overrides global)
        assert manager.config.system.log_level == "DEBUG"  # From project
        assert manager.config.web.port == 8080  # From user

def test_config_model_customization():
    """Test using a custom configuration model."""
    from pydantic import BaseModel, Field

    class CustomConfig(BaseModel):
        """Custom configuration model."""
        app_name: str = "custom"
        debug: bool = False

    manager = ConfigManager(
        config_model=CustomConfig,
        default_config={"app_name": "test", "debug": True}
    )

    assert manager.config.app_name == "test"
    assert manager.config.debug is True
