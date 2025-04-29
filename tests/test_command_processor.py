"""Tests for command processor."""

import pytest
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock

from rtaspi.input.command_processor import CommandProcessor
from rtaspi.input.keyboard import VirtualKeyboard


@pytest.fixture
def processor():
    """Create test command processor."""
    with patch('rtaspi.input.keyboard.VirtualKeyboard') as mock_keyboard:
        # Mock keyboard initialization
        mock_keyboard.return_value.initialize.return_value = True
        processor = CommandProcessor()
        processor.initialize()
        yield processor
        processor.cleanup()


def test_processor_init():
    """Test processor initialization."""
    # Test with mock keyboard
    mock_keyboard = Mock()
    mock_keyboard.initialize.return_value = True
    processor = CommandProcessor(keyboard=mock_keyboard)
    
    assert processor.initialize()
    assert processor._initialized
    mock_keyboard.initialize.assert_called_once()
    
    # Test initialization failure
    mock_keyboard.initialize.return_value = False
    processor._initialized = False
    assert not processor.initialize()
    assert not processor._initialized


def test_processor_cleanup(processor):
    """Test processor cleanup."""
    processor.cleanup()
    assert not processor._initialized
    processor.keyboard.cleanup.assert_called_once()


def test_default_commands(processor):
    """Test default command loading."""
    commands = processor.get_commands()
    assert len(commands) >= 6  # At least 6 default commands
    
    # Verify command patterns
    patterns = [cmd['pattern'] for cmd in commands]
    assert "type {text}" in patterns
    assert "press {key}" in patterns
    assert "release {key}" in patterns
    assert "tap {key}" in patterns
    assert "repeat" in patterns
    assert "set {name} to {value}" in patterns


def test_command_processing(processor):
    """Test command processing."""
    # Test type command
    assert processor.process_command("type hello")
    processor.keyboard.type_text.assert_called_once_with("hello")

    # Test press command
    assert processor.process_command("press shift")
    processor.keyboard.press_key.assert_called_once_with("shift")

    # Test release command
    assert processor.process_command("release shift")
    processor.keyboard.release_key.assert_called_once_with("shift")

    # Test tap command
    assert processor.process_command("tap a")
    processor.keyboard.tap_key.assert_called_once_with("a")

    # Test non-existent command
    assert not processor.process_command("invalid command")


def test_command_variables(processor):
    """Test variable handling."""
    # Set variable
    processor.process_command("set name to test")
    assert processor.get_variable("name") == "test"

    # Use variable in command
    processor.keyboard.reset_mock()
    assert processor.process_command("type $name")
    processor.keyboard.type_text.assert_called_once_with("test")

    # Clear variables
    processor.clear_variables()
    assert processor.get_variable("name") is None


def test_command_repeat(processor):
    """Test command repetition."""
    # Execute command
    assert processor.process_command("type test")
    processor.keyboard.type_text.assert_called_once_with("test")

    # Repeat command
    processor.keyboard.reset_mock()
    assert processor.process_command("repeat")
    processor.keyboard.type_text.assert_called_once_with("test")

    # Try repeat without previous command
    processor._last_command = None
    assert not processor.process_command("repeat")


def test_load_commands_from_file(processor):
    """Test loading commands from file."""
    # Create test command file
    commands = [
        {
            "pattern": "custom {param}",
            "description": "Custom command",
            "action": "self.keyboard.type_text(m['param'])"
        }
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as f:
        json.dump(commands, f)
        f.flush()
        
        # Load commands
        assert processor.load_commands_from_file(f.name)
        
        # Test custom command
        processor.keyboard.reset_mock()
        assert processor.process_command("custom test")
        processor.keyboard.type_text.assert_called_once_with("test")


def test_add_command(processor):
    """Test adding custom commands."""
    # Add custom command
    action = Mock()
    processor.add_command(
        "custom {param}",
        lambda m: action(m['param']),
        "Custom command"
    )

    # Test command
    assert processor.process_command("custom test")
    action.assert_called_once_with("test")

    # Verify command was added
    commands = processor.get_commands()
    assert any(cmd['pattern'] == "custom {param}" for cmd in commands)


def test_clear_commands(processor):
    """Test clearing commands."""
    # Clear commands
    processor.clear_commands()
    assert not processor.get_commands()

    # Commands should not work
    assert not processor.process_command("type test")
    processor.keyboard.type_text.assert_not_called()


def test_error_handling(processor):
    """Test error handling."""
    # Test keyboard error
    processor.keyboard.type_text.side_effect = Exception("Test error")
    assert not processor.process_command("type test")  # Should return False but not raise

    # Test invalid command pattern
    with pytest.raises(Exception):
        processor.add_command("{", lambda m: None)  # Invalid regex

    # Test command without initialization
    processor._initialized = False
    assert not processor.process_command("type test")


def test_regex_matching(processor):
    """Test command pattern regex matching."""
    # Add command with complex pattern
    action = Mock()
    processor.add_command(
        "do {action} {count} times",
        lambda m: action(m['action'], int(m['count'])),
        "Do action multiple times"
    )

    # Test matching
    assert processor.process_command("do jump 3 times")
    action.assert_called_once_with("jump", 3)

    # Test non-matching
    assert not processor.process_command("do jump times")  # Missing count
    assert not processor.process_command("do 3 jump times")  # Wrong order


def test_variable_scoping(processor):
    """Test variable scoping and replacement."""
    # Set multiple variables
    processor.process_command("set var1 to hello")
    processor.process_command("set var2 to world")

    # Use multiple variables
    processor.keyboard.reset_mock()
    assert processor.process_command("type $var1 $var2")
    processor.keyboard.type_text.assert_called_once_with("hello world")

    # Test variable overwriting
    processor.process_command("set var1 to hi")
    processor.keyboard.reset_mock()
    assert processor.process_command("type $var1 $var2")
    processor.keyboard.type_text.assert_called_once_with("hi world")


def test_command_descriptions(processor):
    """Test command descriptions."""
    # Add commands with descriptions
    processor.add_command("cmd1", lambda m: None, "First command")
    processor.add_command("cmd2", lambda m: None, "Second command")

    # Get commands
    commands = processor.get_commands()
    descriptions = {cmd['pattern']: cmd['description'] for cmd in commands}

    # Verify descriptions
    assert descriptions["cmd1"] == "First command"
    assert descriptions["cmd2"] == "Second command"
