"""RTASPI Core - Fundamental functionality for the RTASPI system."""

from typing import Dict, Any

from .config import (
    ConfigManager,
    ConfigurationError,
    ConfigLoadError,
    ConfigValidationError,
    ConfigSaveError,
    RTASPIConfig,
    SystemConfig,
    StreamingConfig,
    ProcessingConfig,
    WebConfig,
    LocalDevicesConfig,
    NetworkDevicesConfig,
    create_config_manager,
    config_manager,
)

__version__ = "0.2.0"

# Initialize the default configuration manager
default_config_manager = config_manager

def get_config() -> RTASPIConfig:
    """Get the current configuration.
    
    Returns:
        Current configuration instance
    """
    return default_config_manager.config

def set_config_value(key: str, value: Any, level: str = "project") -> bool:
    """Set a configuration value.
    
    Args:
        key: Configuration key using dot notation
        value: Value to set
        level: Configuration level to save to
        
    Returns:
        True if successful, False otherwise
    """
    return default_config_manager.set(key, value, level)

def get_config_value(key: str, default: Any = None) -> Any:
    """Get a configuration value.
    
    Args:
        key: Configuration key using dot notation
        default: Default value if not found
        
    Returns:
        Configuration value or default if not found
    """
    return default_config_manager.get(key, default)

def load_config_file(path: str) -> bool:
    """Load configuration from a file.
    
    Args:
        path: Path to configuration file
        
    Returns:
        True if successful, False otherwise
    """
    return default_config_manager.load_config_file(path)

def save_config(level: str = "project") -> bool:
    """Save current configuration.
    
    Args:
        level: Configuration level to save to
        
    Returns:
        True if successful, False otherwise
    """
    return default_config_manager.save_config(level)

__all__ = [
    "__version__",
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
    "default_config_manager",
    "get_config",
    "set_config_value",
    "get_config_value",
    "load_config_file",
    "save_config",
]
