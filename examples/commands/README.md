# Command Examples

This directory contains examples demonstrating RTASPI's command system and keyboard control capabilities.

## Examples

### 1. Keyboard Commands (`keyboard_commands.py`)
Shows how to:
- Define keyboard shortcuts
- Handle key combinations
- Create command bindings
- Process input events

### 2. Voice Commands (`voice_commands.py`)
Demonstrates:
- Speech command recognition
- Natural language processing
- Command mapping
- Response handling

### 3. Remote Control (`remote_control.py`)
Features:
- Network command handling
- Remote device control
- Command synchronization
- Event distribution

### 4. Command Scripting (`command_scripting.py`)
Implements:
- Command sequences
- Macro recording
- Script execution
- Error handling

## Configuration Files

### `keyboard_commands.json`
```json
{
  "global": {
    "ctrl+shift+r": {
      "action": "start_recording",
      "params": {
        "format": "mp4",
        "quality": "high"
      }
    },
    "ctrl+shift+s": {
      "action": "stop_recording",
      "params": {
        "save": true
      }
    }
  },
  "camera": {
    "ctrl+1": {
      "action": "switch_camera",
      "params": {
        "device": "camera1"
      }
    },
    "ctrl+2": {
      "action": "switch_camera",
      "params": {
        "device": "camera2"
      }
    }
  }
}
```

### `voice_commands.yaml`
```yaml
commands:
  - phrase: "start recording"
    action: start_recording
    params:
      format: mp4
      quality: high
    
  - phrase: "stop recording"
    action: stop_recording
    params:
      save: true

  - phrase: "switch to camera {number}"
    action: switch_camera
    params:
      device: "camera{number}"
```

## Requirements

- RTASPI with command extensions
- PyAutoGUI for keyboard control
- Speech recognition (optional)
- Network support (optional)

## Usage

1. Configure commands:
```bash
# Copy and edit configuration
cp keyboard_commands.json.example keyboard_commands.json
cp voice_commands.yaml.example voice_commands.yaml
```

2. Run examples:
```bash
# Keyboard commands
python keyboard_commands.py --config keyboard_commands.json

# Voice commands
python voice_commands.py --config voice_commands.yaml

# Remote control
python remote_control.py --host 192.168.1.100

# Command scripting
python command_scripting.py --script commands.txt
```

## Features

### Input Handling
- Keyboard events
- Voice recognition
- Remote commands
- Script parsing

### Command Processing
- Action mapping
- Parameter validation
- Error handling
- Event logging

### Command Types
- Direct actions
- Sequences
- Macros
- Scripts

### Integration
- Device control
- System commands
- Network distribution
- API integration

## Best Practices

1. Command Design
   - Use clear names
   - Document actions
   - Validate inputs
   - Handle errors

2. Input Handling
   - Check permissions
   - Validate commands
   - Handle timeouts
   - Log actions

3. Security
   - Validate sources
   - Check permissions
   - Sanitize inputs
   - Monitor usage

## Troubleshooting

Common issues and solutions:

1. Input Problems
   - Check permissions
   - Verify bindings
   - Test recognition
   - Update drivers

2. Command Issues
   - Validate syntax
   - Check mapping
   - Test actions
   - Monitor logs

3. Integration
   - Check connectivity
   - Verify permissions
   - Test endpoints
   - Monitor events

## Support

For command-related issues:
- Check documentation
- Join command system channel on Discord
- Submit detailed bug reports
- Share command configurations
