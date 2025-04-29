"""Command processor for converting speech to input actions."""

import logging
import re
from typing import Dict, List, Optional, Callable, Any
import json
import os

from ..core.logging import get_logger
from .keyboard import VirtualKeyboard

logger = get_logger(__name__)


class CommandProcessor:
    """Process speech commands and convert to input actions."""

    def __init__(self, keyboard: Optional[VirtualKeyboard] = None):
        """Initialize command processor.

        Args:
            keyboard: Virtual keyboard instance or None to create new one
        """
        self.keyboard = keyboard or VirtualKeyboard()
        self._commands: Dict[str, Dict[str, Any]] = {}
        self._variables: Dict[str, str] = {}
        self._last_command: Optional[str] = None
        self._initialized = False

    def initialize(self) -> bool:
        """Initialize command processor.

        Returns:
            bool: True if initialization successful
        """
        if self._initialized:
            return True

        try:
            # Initialize keyboard
            if not self.keyboard.initialize():
                logger.error("Failed to initialize keyboard")
                return False

            # Load default commands
            self.load_default_commands()

            self._initialized = True
            logger.info("Command processor initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize command processor: {e}")
            return False

    def cleanup(self) -> None:
        """Clean up resources."""
        if self._initialized:
            try:
                self.keyboard.cleanup()
                self._initialized = False
                logger.info("Command processor cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up command processor: {e}")

    def load_default_commands(self) -> None:
        """Load default command definitions."""
        self.add_command(
            "type {text}",
            lambda m: self.keyboard.type_text(m["text"]),
            "Type the specified text",
        )

        self.add_command(
            "press {key}",
            lambda m: self.keyboard.press_key(m["key"]),
            "Press and hold a key",
        )

        self.add_command(
            "release {key}",
            lambda m: self.keyboard.release_key(m["key"]),
            "Release a held key",
        )

        self.add_command(
            "tap {key}", lambda m: self.keyboard.tap_key(m["key"]), "Tap a key once"
        )

        self.add_command(
            "repeat", lambda _: self.repeat_last_command(), "Repeat the last command"
        )

        self.add_command(
            "set {name} to {value}",
            lambda m: self.set_variable(m["name"], m["value"]),
            "Set a variable value",
        )

    def load_commands_from_file(self, path: str) -> bool:
        """Load commands from JSON file.

        Args:
            path: Path to JSON command file

        Returns:
            bool: True if commands loaded successfully
        """
        try:
            with open(path, "r") as f:
                commands = json.load(f)

            for cmd in commands:
                pattern = cmd["pattern"]
                description = cmd.get("description", "")
                action_code = cmd["action"]
                # Create lambda from action code string
                action = eval(f"lambda m: {action_code}")
                self.add_command(pattern, action, description)

            logger.info(f"Loaded {len(commands)} commands from {path}")
            return True

        except Exception as e:
            logger.error(f"Failed to load commands from {path}: {e}")
            return False

    def add_command(
        self,
        pattern: str,
        action: Callable[[Dict[str, str]], None],
        description: str = "",
    ) -> None:
        """Add command pattern and action.

        Args:
            pattern: Command pattern with {param} placeholders
            action: Function to call with matched parameters
            description: Command description
        """
        # Convert pattern to regex
        regex = pattern
        for param in re.findall(r"\{(\w+)\}", pattern):
            regex = regex.replace(f"{{{param}}}", f"(?P<{param}>[^\\s]+)")
        regex = f"^{regex}$"

        self._commands[pattern] = {
            "regex": re.compile(regex),
            "action": action,
            "description": description,
        }
        logger.debug(f"Added command: {pattern}")

    def process_command(self, text: str) -> bool:
        """Process command text.

        Args:
            text: Command text to process

        Returns:
            bool: True if command was processed
        """
        if not self._initialized:
            logger.error("Command processor not initialized")
            return False

        try:
            # Replace variables
            for name, value in self._variables.items():
                text = text.replace(f"${name}", value)

            # Try each command pattern
            for pattern, cmd in self._commands.items():
                match = cmd["regex"].match(text)
                if match:
                    # Store for repeat
                    self._last_command = text
                    # Execute action with matched params
                    cmd["action"](match.groupdict())
                    return True

            logger.warning(f"No matching command: {text}")
            return False

        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return False

    def repeat_last_command(self) -> bool:
        """Repeat last executed command.

        Returns:
            bool: True if command was repeated
        """
        if not self._last_command:
            logger.warning("No command to repeat")
            return False
        return self.process_command(self._last_command)

    def set_variable(self, name: str, value: str) -> None:
        """Set variable value.

        Args:
            name: Variable name
            value: Variable value
        """
        self._variables[name] = value
        logger.debug(f"Set variable {name} = {value}")

    def get_variable(self, name: str) -> Optional[str]:
        """Get variable value.

        Args:
            name: Variable name

        Returns:
            Optional[str]: Variable value if set
        """
        return self._variables.get(name)

    def get_commands(self) -> List[Dict[str, str]]:
        """Get list of available commands.

        Returns:
            List[Dict[str, str]]: List of command patterns and descriptions
        """
        return [
            {"pattern": pattern, "description": cmd["description"]}
            for pattern, cmd in self._commands.items()
        ]

    def clear_commands(self) -> None:
        """Clear all commands."""
        self._commands.clear()
        logger.debug("Cleared all commands")

    def clear_variables(self) -> None:
        """Clear all variables."""
        self._variables.clear()
        logger.debug("Cleared all variables")
