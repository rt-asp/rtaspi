"""
config.py - Configuration management for rtaspi
"""

import os
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from .defaults import DEFAULT_CONFIG, ENV_VARIABLE_MAP

logger = logging.getLogger("Config")


class ConfigManager:
    """Manages hierarchical configuration system."""

    def __init__(self):
        """Initialize the configuration manager with hierarchical config support."""
        self.config_levels = {
            "defaults": DEFAULT_CONFIG,
            "global": self._expand_path("/etc/rtaspi/config.yaml"),
            "user": self._expand_path("~/.config/rtaspi/config.yaml"),
            "project": ".rtaspi/config.yaml"
        }
        self.config = self._load_hierarchical_config()

    def _expand_path(self, path: str) -> str:
        """Expand user and environment variables in path."""
        return os.path.expanduser(os.path.expandvars(path))

    def _load_hierarchical_config(self) -> Dict[str, Any]:
        """Load configuration from all sources in order of precedence."""
        config = DEFAULT_CONFIG.copy()

        # Load from files in order
        for level, path in self.config_levels.items():
            if level == "defaults":
                continue
            try:
                if os.path.exists(path):
                    with open(path, "r") as f:
                        loaded_config = yaml.safe_load(f)
                        if loaded_config:
                            self._update_dict(config, loaded_config)
                            logger.info(f"Loaded {level} configuration from {path}")
            except Exception as e:
                logger.error(f"Error loading {level} configuration from {path}: {e}")

        # Apply environment variables last (highest precedence)
        self._apply_env_variables(config)

        return config

    def _apply_env_variables(self, config: Dict[str, Any]) -> None:
        """Apply environment variables to configuration."""
        for env_var, config_path in ENV_VARIABLE_MAP.items():
            value = os.environ.get(env_var)
            if value is not None:
                try:
                    # Convert string value to appropriate type
                    if value.lower() in ('true', 'false'):
                        value = value.lower() == 'true'
                    elif value.isdigit():
                        value = int(value)
                    elif value.replace('.', '').isdigit() and value.count('.') == 1:
                        value = float(value)

                    self.set(config_path, value, "env")
                except Exception as e:
                    logger.error(f"Error applying environment variable {env_var}: {e}")

    def save_config(self, level: str = "project") -> bool:
        """
        Save current configuration to specified level.

        Args:
            level (str): Configuration level to save to ('global', 'user', or 'project')

        Returns:
            bool: True if saved successfully, False otherwise
        """
        if level not in self.config_levels or level == "defaults":
            logger.error(f"Invalid configuration level: {level}")
            return False

        path = self.config_levels[level]
        try:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, "w") as f:
                yaml.dump(self.config, f, default_flow_style=False)
            logger.info(f"Saved configuration to {level} level at {path}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration to {path}: {e}")
            return False

    def get_config(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get configuration value with dot notation.

        Args:
            section (str): Configuration section
            key (str): Configuration key
            default: Default value if not found

        Returns:
            Configuration value or default if not found
        """
        return self.get(f"{section}.{key}", default)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.

        Args:
            key (str): Configuration key with dot notation
            default: Default value if not found

        Returns:
            Configuration value or default if not found
        """
        value = self.config
        for part in key.split("."):
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
        return value

    def set_config(self, section: str, key: str, value: Any, level: str = "project") -> bool:
        """
        Set configuration value with section and key.

        Args:
            section (str): Configuration section
            key (str): Configuration key
            value: Value to set
            level (str): Configuration level to save to

        Returns:
            bool: True if set successfully, False otherwise
        """
        return self.set(f"{section}.{key}", value, level)

    def set(self, key: str, value: Any, level: str = "project") -> bool:
        """
        Set configuration value using dot notation.

        Args:
            key (str): Configuration key with dot notation
            value: Value to set
            level (str): Configuration level to save to

        Returns:
            bool: True if set successfully, False otherwise
        """
        if level not in self.config_levels:
            logger.error(f"Invalid configuration level: {level}")
            return False

        try:
            parts = key.split(".")
            current = self.config

            # Navigate to the correct nesting level
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]

            # Set the value
            current[parts[-1]] = value

            # Save to the specified configuration level
            return self.save_config(level)

        except Exception as e:
            logger.error(f"Error setting configuration value: {e}")
            return False

    def _update_dict(self, dest: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        Update destination dictionary with source values recursively.

        Args:
            dest (dict): Destination dictionary
            source (dict): Source dictionary
        """
        for key, value in source.items():
            if key in dest and isinstance(dest[key], dict) and isinstance(value, dict):
                self._update_dict(dest[key], value)
            else:
                dest[key] = value

    def load_config_file(self, path: str) -> bool:
        """
        Load configuration from a specific file.

        Args:
            path (str): Path to configuration file

        Returns:
            bool: True if loaded successfully, False otherwise
        """
        try:
            if os.path.exists(path):
                with open(path, "r") as f:
                    loaded_config = yaml.safe_load(f)
                    if loaded_config:
                        self._update_dict(self.config, loaded_config)
                        logger.info(f"Loaded configuration from {path}")
                        return True
            return False
        except Exception as e:
            logger.error(f"Error loading configuration from {path}: {e}")
            return False
