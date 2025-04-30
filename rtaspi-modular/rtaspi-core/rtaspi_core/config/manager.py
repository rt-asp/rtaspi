"""Configuration management for RTASPI core module."""

import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union, TypeVar, Generic
from pydantic import BaseModel, Field, ValidationError
import yaml
from structlog import get_logger

T = TypeVar("T")

class ConfigLevel(BaseModel):
    """Configuration level settings."""
    path: str
    required: bool = False
    description: str = ""

class ConfigurationError(Exception):
    """Base class for configuration errors."""
    pass

class ConfigLoadError(ConfigurationError):
    """Error loading configuration file."""
    pass

class ConfigValidationError(ConfigurationError):
    """Error validating configuration."""
    pass

class ConfigSaveError(ConfigurationError):
    """Error saving configuration."""
    pass

class BaseConfig(BaseModel):
    """Base configuration model with common settings."""
    system: Dict[str, Any] = Field(
        default_factory=lambda: {
            "storage_path": "storage",
            "log_level": "INFO",
            "config_paths": {
                "global": "/etc/rtaspi/config.yaml",
                "user": "~/.config/rtaspi/config.yaml",
                "project": ".rtaspi/config.yaml",
            },
        }
    )
    enums: Dict[str, Dict[str, str]] = Field(default_factory=dict)

class ConfigManager(Generic[T]):
    """Enhanced configuration manager with type safety and validation."""

    def __init__(
        self,
        config_model: Optional[type[BaseModel]] = None,
        default_config: Optional[Dict[str, Any]] = None,
        env_map: Optional[Dict[str, str]] = None
    ):
        """Initialize configuration manager.
        
        Args:
            config_model: Optional Pydantic model for configuration validation
            default_config: Default configuration values
            env_map: Mapping of environment variables to config paths
        """
        self.logger = get_logger(__name__)
        self.config_model = config_model or BaseConfig
        self._default_config = default_config or {}
        self._env_map = env_map or {}
        
        self.config_levels = {
            "defaults": ConfigLevel(
                path="",
                required=True,
                description="Default configuration"
            ),
            "global": ConfigLevel(
                path=self._expand_path("/etc/rtaspi/config.yaml"),
                description="System-wide configuration"
            ),
            "user": ConfigLevel(
                path=self._expand_path("~/.config/rtaspi/config.yaml"),
                description="User-specific configuration"
            ),
            "project": ConfigLevel(
                path=".rtaspi/config.yaml",
                description="Project-level configuration"
            ),
        }
        
        self.config = self._load_hierarchical_config()

    def _expand_path(self, path: Union[str, Path]) -> str:
        """Expand user and environment variables in path."""
        return os.path.expanduser(os.path.expandvars(str(path)))

    def _load_yaml(self, path: Union[str, Path]) -> Dict[str, Any]:
        """Load YAML file with error handling."""
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            raise ConfigLoadError(f"Error loading {path}: {e}")

    def _validate_config(self, config: Dict[str, Any]) -> T:
        """Validate configuration against model."""
        try:
            return self.config_model.model_validate(config)
        except ValidationError as e:
            raise ConfigValidationError(f"Configuration validation failed: {e}")

    def _load_hierarchical_config(self) -> T:
        """Load configuration from all sources in order of precedence."""
        config = self._default_config.copy()

        # Load from files in order
        for level_name, level in self.config_levels.items():
            if level_name == "defaults":
                continue
                
            try:
                path = level.path
                if os.path.exists(path):
                    loaded_config = self._load_yaml(path)
                    self._update_dict(config, loaded_config)
                    self.logger.info(f"Loaded {level_name} configuration", path=path)
                elif level.required:
                    raise ConfigLoadError(f"Required config {level_name} not found at {path}")
            except Exception as e:
                self.logger.error(f"Error loading {level_name} configuration", 
                                error=str(e), path=level.path)
                if level.required:
                    raise

        # Apply environment variables
        self._apply_env_variables(config)

        # Validate final config
        return self._validate_config(config)

    def _apply_env_variables(self, config: Dict[str, Any]) -> None:
        """Apply environment variables to configuration."""
        for env_var, config_path in self._env_map.items():
            value = os.environ.get(env_var)
            if value is not None:
                try:
                    # Convert string value to appropriate type
                    if value.lower() in ("true", "false"):
                        value = value.lower() == "true"
                    elif value.isdigit():
                        value = int(value)
                    elif value.replace(".", "").isdigit() and value.count(".") == 1:
                        value = float(value)

                    self.set(config_path, value)
                except Exception as e:
                    self.logger.error(f"Error applying environment variable",
                                    env_var=env_var, error=str(e))

    def _update_dict(self, dest: Dict[str, Any], source: Dict[str, Any]) -> None:
        """Update destination dictionary with source values recursively."""
        for key, value in source.items():
            if key in dest and isinstance(dest[key], dict) and isinstance(value, dict):
                self._update_dict(dest[key], value)
            else:
                dest[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        value = self.config
        try:
            for part in key.split("."):
                value = getattr(value, part) if hasattr(value, part) else value[part]
            return value
        except (KeyError, AttributeError):
            return default

    def set(self, key: str, value: Any, level: str = "project") -> bool:
        """Set configuration value using dot notation."""
        if level not in self.config_levels:
            raise ValueError(f"Invalid configuration level: {level}")

        try:
            # Create a dictionary from the dot notation
            parts = key.split(".")
            current = self.config.dict()
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value

            # Validate the new configuration
            new_config = self._validate_config(self.config.dict())
            
            # If validation passes, update and save
            self.config = new_config
            return self.save_config(level)

        except Exception as e:
            self.logger.error("Error setting configuration value",
                            key=key, value=value, level=level, error=str(e))
            return False

    def save_config(self, level: str = "project") -> bool:
        """Save current configuration to specified level."""
        if level not in self.config_levels or level == "defaults":
            raise ValueError(f"Invalid configuration level: {level}")

        try:
            path = self.config_levels[level].path
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            
            with open(path, "w") as f:
                yaml.dump(self.config.dict(), f, default_flow_style=False)
                
            self.logger.info(f"Saved configuration", level=level, path=path)
            return True
            
        except Exception as e:
            raise ConfigSaveError(f"Error saving configuration to {path}: {e}")

    def load_config_file(self, path: Union[str, Path]) -> bool:
        """Load configuration from a specific file."""
        try:
            path = self._expand_path(path)
            if os.path.exists(path):
                loaded_config = self._load_yaml(path)
                new_config = self.config.dict()
                self._update_dict(new_config, loaded_config)
                
                # Validate and update
                self.config = self._validate_config(new_config)
                self.logger.info("Loaded configuration from file", path=path)
                return True
                
            return False
            
        except Exception as e:
            self.logger.error("Error loading configuration file",
                            path=path, error=str(e))
            return False
