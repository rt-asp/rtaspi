"""
enums.py - Configurable enumeration base class with hierarchical value loading
"""

import os
from enum import Enum
from typing import Any, Optional
from .config import ConfigManager


class ConfigurableEnum(Enum):
    """Base class for enums that support configuration hierarchy."""
    
    @classmethod
    def _generate_env_var(cls, name: str) -> str:
        """Generate environment variable name for enum value."""
        return f"RTASPI_{cls.__name__.upper()}_{name}"

    def get_value(self, config_manager: Optional[ConfigManager] = None) -> Any:
        """
        Get the enum value following the configuration hierarchy:
        1. Environment variable (RTASPI_{ENUM_CLASS}_{ENUM_NAME})
        2. Project config
        3. User config
        4. Global config
        5. Default enum value
        """
        # Check environment variable override
        env_var = self._generate_env_var(self.name)
        env_value = os.environ.get(env_var)
        if env_value is not None:
            return self._convert_value(env_value)

        # Check config hierarchy if config_manager provided
        if config_manager is not None:
            config_key = f"enums.{self.__class__.__name__}.{self.name}"
            config_value = config_manager.get(config_key)
            if config_value is not None:
                return self._convert_value(config_value)

        # Fallback to default enum value
        return self.value

    def _convert_value(self, value: Any) -> Any:
        """Convert string value to appropriate type based on enum's value type."""
        if isinstance(self.value, bool):
            return str(value).lower() == "true"
        elif isinstance(self.value, int):
            return int(value)
        elif isinstance(self.value, float):
            return float(value)
        return str(value)

    @property
    def CONSTANT_NAME(self) -> str:
        """Get the constant-style name for the enum value."""
        return self.name.upper()
