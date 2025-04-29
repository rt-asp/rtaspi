# Speech-to-Text and Input Device Integration

This document describes the speech recognition and input device integration features in rtaspi.

## Speech Recognition

The speech recognition module uses OpenAI's Whisper model for local speech-to-text processing. It supports multiple languages and includes audio preprocessing for better recognition accuracy.

### Features

- Real-time speech recognition using Whisper
- Support for multiple languages
- Audio preprocessing with noise reduction and normalization
- Configurable model size (tiny, base, small, medium, large)
- CUDA acceleration when available

### Usage

```python
from rtaspi.processing.speech.recognition import SpeechRecognizer

# Initialize recognizer
recognizer = SpeechRecognizer(
    model_name="base",  # Model size
    language="en",      # Language code or None for auto-detect
    device="cuda"       # Use "cpu" if CUDA not available
)

# Start recognition
recognizer.start()

# Set callbacks
recognizer.set_on_transcription(lambda text: print(f"Recognized: {text}"))
recognizer.set_on_error(lambda error: print(f"Error: {error}"))

# Process audio
recognizer.process_audio(audio_data, sample_rate)

# Stop recognition
recognizer.stop()
```

## Virtual Keyboard

The virtual keyboard module provides cross-platform keyboard input simulation. It supports all standard keyboard operations and works on Linux (uinput), Windows (Win32), and macOS (Quartz).

### Features

- Cross-platform keyboard simulation
- Text typing with configurable delay
- Key press, release, and tap operations
- Modifier key tracking
- Error handling and logging

### Usage

```python
from rtaspi.input.keyboard import VirtualKeyboard

# Initialize keyboard
keyboard = VirtualKeyboard()
keyboard.initialize()

# Type text
keyboard.type_text("Hello, world!", delay=0.1)

# Key operations
keyboard.press_key("shift")
keyboard.tap_key("a")  # Types "A"
keyboard.release_key("shift")

# Cleanup
keyboard.cleanup()
```

## Command Processor

The command processor converts speech recognition results into keyboard actions using a flexible command pattern system.

### Features

- Pattern-based command matching
- Variable support for dynamic commands
- Command history and repeat functionality
- Custom command loading from JSON files
- Error handling and logging

### Usage

```python
from rtaspi.input.command_processor import CommandProcessor

# Initialize processor
processor = CommandProcessor()
processor.initialize()

# Load custom commands
processor.load_commands_from_file("commands/keyboard_commands.json")

# Process commands
processor.process_command("type Hello, world!")
processor.process_command("press shift 3 times")
processor.process_command("type slowly carefully typed text")

# Use variables
processor.process_command("set name to John")
processor.process_command("type Hello, $name!")

# Cleanup
processor.cleanup()
```

### Custom Commands

Custom commands can be defined in JSON files. Each command has:
- `pattern`: Command pattern with {param} placeholders
- `description`: Command description
- `action`: Python code to execute (as string)

Example command file:
```json
{
    "commands": [
        {
            "pattern": "type slowly {text}",
            "description": "Type text with delay",
            "action": "self.keyboard.type_text(m['text'], delay=0.1)"
        }
    ]
}
```

See `examples/commands/keyboard_commands.json` for more examples.

## Integration Example

Here's how to combine speech recognition with command processing:

```python
from rtaspi.processing.speech.recognition import SpeechRecognizer
from rtaspi.input.command_processor import CommandProcessor

# Initialize components
recognizer = SpeechRecognizer()
processor = CommandProcessor()

recognizer.initialize()
processor.initialize()

# Load custom commands
processor.load_commands_from_file("commands/keyboard_commands.json")

# Connect recognition to command processing
def on_speech(text):
    print(f"Recognized: {text}")
    processor.process_command(text)

recognizer.set_on_transcription(on_speech)

# Start recognition
recognizer.start()

# ... application code ...

# Cleanup
recognizer.stop()
processor.cleanup()
```

## Platform-Specific Notes

### Linux
- Requires `python-uinput` package
- User needs permissions to use uinput device
- Add user to input group: `sudo usermod -a -G input $USER`

### Windows
- Requires `pywin32` package
- May need elevated privileges for some operations

### macOS
- Requires `pyobjc-framework-Quartz` package
- May need accessibility permissions

## Error Handling

All components include comprehensive error handling and logging:
- Speech recognition errors are reported through the error callback
- Keyboard errors are logged but don't crash the application
- Command processing errors are logged and return False

## Performance Considerations

- Speech recognition performance depends on:
  - Chosen model size
  - Available hardware (CPU/GPU)
  - Audio quality and noise level
- Keyboard simulation may have platform-specific timing constraints
- Command processing is lightweight but should handle errors gracefully

## Future Improvements

Planned improvements include:
- Additional speech recognition backends
- More sophisticated audio preprocessing
- Extended command pattern matching
- Mouse control integration
- Gesture recognition support
