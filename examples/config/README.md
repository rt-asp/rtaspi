# Configuration Examples

This directory contains examples demonstrating RTASPI's configuration system and capabilities.

## Examples

### 1. Project Configuration (`project_config.yaml`)
Shows how to:
- Set up project-level settings
- Configure environment variables
- Define project structure
- Set development options

### 2. User Configuration (`user_config.yaml`)
Demonstrates:
- User-specific settings
- Personal preferences
- Local overrides
- Development tools

### 3. RTASPI Configuration (`rtaspi_config.yaml`)
Features:
- Global system settings
- Default configurations
- Feature toggles
- System paths

## Configuration Hierarchy

RTASPI uses a hierarchical configuration system:

1. Default Configuration (built-in)
2. Global Configuration (`/etc/rtaspi/config.yaml`)
3. User Configuration (`~/.config/rtaspi/config.yaml`)
4. Project Configuration (`.rtaspi/config.yaml`)
5. Environment Variables
6. Command Line Arguments

Later levels override earlier ones.

## Configuration Files

### `project_config.yaml`
```yaml
project:
  name: my_camera_system
  version: 1.0.0
  description: Camera monitoring system

paths:
  data: data/
  models: models/
  output: output/
  logs: logs/

devices:
  cameras:
    - name: front_door
      type: rtsp
      url: rtsp://192.168.1.100/stream1
    - name: backyard
      type: local
      device: /dev/video0

processing:
  detection:
    model: yolov5s
    confidence: 0.6
  recording:
    format: mp4
    quality: high
```

### `user_config.yaml`
```yaml
development:
  debug: true
  hot_reload: true
  log_level: debug

preferences:
  theme: dark
  language: en
  timezone: Europe/Berlin

tools:
  editor: vscode
  terminal: gnome-terminal
  browser: firefox
```

## Usage

1. Set up configuration:
```bash
# Copy example configurations
cp project_config.yaml.example .rtaspi/config.yaml
cp user_config.yaml.example ~/.config/rtaspi/config.yaml
```

2. Environment variables:
```bash
# Set environment variables
export RTASPI_LOG_LEVEL=debug
export RTASPI_DATA_DIR=/path/to/data
```

3. Command line:
```bash
# Override with command line arguments
rtaspi --config custom_config.yaml --log-level debug
```

## Features

### Configuration System
- Hierarchical override
- Environment variables
- Command line arguments
- Hot reload support

### Value Types
- Simple values
- Lists/arrays
- Nested objects
- Environment variables
- File paths

### Validation
- Schema validation
- Type checking
- Required fields
- Default values

### Security
- Secrets management
- Credential handling
- Path validation
- Access control

## Best Practices

1. Project Setup
   - Use version control
   - Document changes
   - Validate configs
   - Use templates

2. Security
   - Protect secrets
   - Use env vars
   - Validate input
   - Check permissions

3. Development
   - Use defaults
   - Document options
   - Test changes
   - Version configs

## Troubleshooting

Common issues and solutions:

1. Loading Issues
   - Check file paths
   - Verify permissions
   - Validate syntax
   - Check hierarchy

2. Override Problems
   - Check precedence
   - Verify sources
   - Debug values
   - Test changes

3. Validation Errors
   - Check schemas
   - Verify types
   - Test required fields
   - Validate formats

## Support

For configuration-related issues:
- Check documentation
- Join config channel on Discord
- Submit detailed bug reports
- Share configuration templates
