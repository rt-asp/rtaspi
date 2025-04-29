# CLI Guide

RTASPI provides a powerful command-line interface (CLI) for managing devices, streams, and pipelines. This guide covers all available commands and their usage.

## Installation

The CLI is automatically installed with RTASPI. You can verify the installation by running:

```bash
rtaspi --version
```

## Shell Completion

RTASPI supports shell completion for bash, zsh, and fish shells.

### Bash
```bash
source <(rtaspi completion bash)
# Add to ~/.bashrc for permanent installation
echo 'source <(rtaspi completion bash)' >> ~/.bashrc
```

### Zsh
```bash
source <(rtaspi completion zsh)
# Add to ~/.zshrc for permanent installation
echo 'source <(rtaspi completion zsh)' >> ~/.zshrc
```

### Fish
```bash
rtaspi completion fish > ~/.config/fish/completions/rtaspi.fish
```

## Global Options

- `--config, -c`: Path to configuration file (default: rtaspi.config.yaml)
- `--verbose, -v`: Enable verbose output
- `--quiet, -q`: Suppress output
- `--json`: Output in JSON format
- `--help, -h`: Show help message

## Commands

### System Management

#### Start RTASPI
```bash
rtaspi start [options]
```
Options:
- `--daemon`: Run in background
- `--log-file`: Path to log file
- `--pid-file`: Path to PID file

#### Stop RTASPI
```bash
rtaspi stop
```

#### Show System Status
```bash
rtaspi status
```

#### View Logs
```bash
rtaspi logs [options]
```
Options:
- `--level`: Log level (debug, info, warning, error)
- `--follow, -f`: Follow log output
- `--tail`: Number of lines to show
- `--since`: Show logs since timestamp

### Device Management

#### List Devices
```bash
rtaspi devices list [options]
```
Options:
- `--type`: Filter by device type (video, audio)
- `--status`: Filter by status (active, inactive)
- `--format`: Output format (table, json)

Example:
```bash
# List all video devices
rtaspi devices list --type video

# List active devices in JSON format
rtaspi devices list --status active --format json
```

#### Show Device Details
```bash
rtaspi devices show <device-id>
```

Example:
```bash
rtaspi devices show video0
```

#### Add Network Device
```bash
rtaspi devices add [options]
```
Options:
- `--type`: Device type (network)
- `--protocol`: Protocol (rtsp, onvif)
- `--address`: IP address
- `--port`: Port number
- `--username`: Username
- `--password`: Password

Example:
```bash
rtaspi devices add \
  --type network \
  --protocol rtsp \
  --address 192.168.1.100 \
  --port 554 \
  --username admin \
  --password secret
```

#### Update Device Settings
```bash
rtaspi devices update <device-id> [options]
```
Options:
- `--resolution`: Video resolution
- `--framerate`: Frame rate
- `--format`: Video format

Example:
```bash
rtaspi devices update video0 --resolution 1280x720 --framerate 30
```

#### Remove Device
```bash
rtaspi devices remove <device-id>
```

### Stream Management

#### List Streams
```bash
rtaspi streams list [options]
```
Options:
- `--protocol`: Filter by protocol (rtsp, rtmp, webrtc)
- `--status`: Filter by status (active, stopped)

#### Show Stream Details
```bash
rtaspi streams show <stream-id>
```

#### Start Stream
```bash
rtaspi streams start [options]
```
Options:
- `--device`: Device ID
- `--protocol`: Streaming protocol
- `--path`: Stream path
- `--video-codec`: Video codec
- `--video-bitrate`: Video bitrate
- `--audio-enabled`: Enable audio

Example:
```bash
rtaspi streams start \
  --device video0 \
  --protocol rtsp \
  --path /webcam \
  --video-codec h264 \
  --video-bitrate 2M
```

#### Stop Stream
```bash
rtaspi streams stop <stream-id>
```

### Pipeline Management

#### List Pipelines
```bash
rtaspi pipelines list
```

#### Show Pipeline Details
```bash
rtaspi pipelines show <pipeline-id>
```

#### Create Pipeline
```bash
rtaspi pipelines create [options]
```
Options:
- `--input`: Input stream ID
- `--config`: Pipeline configuration file

Example:
```bash
rtaspi pipelines create \
  --input webcam_stream \
  --config pipeline.yaml
```

#### Delete Pipeline
```bash
rtaspi pipelines delete <pipeline-id>
```

### Configuration Management

#### Show Current Configuration
```bash
rtaspi config show [section]
```

Example:
```bash
# Show all configuration
rtaspi config show

# Show specific section
rtaspi config show streaming
```

#### Update Configuration
```bash
rtaspi config set <key> <value>
```

Example:
```bash
rtaspi config set streaming.rtsp.port_start 8554
```

#### Validate Configuration
```bash
rtaspi config validate [file]
```

### Development Tools

#### Generate API Client
```bash
rtaspi dev generate-client [options]
```
Options:
- `--language`: Target language (python, javascript)
- `--output`: Output directory

#### Run Tests
```bash
rtaspi dev test [options]
```
Options:
- `--unit`: Run unit tests
- `--integration`: Run integration tests
- `--coverage`: Generate coverage report

#### Profile Performance
```bash
rtaspi dev profile [options]
```
Options:
- `--duration`: Profile duration
- `--output`: Output file

## Examples

### Basic Usage

1. Start RTASPI:
```bash
rtaspi start
```

2. List available devices:
```bash
rtaspi devices list
```

3. Start streaming from a webcam:
```bash
rtaspi streams start \
  --device video0 \
  --protocol rtsp \
  --path /webcam
```

### Advanced Usage

1. Create a motion detection pipeline:
```bash
rtaspi pipelines create \
  --input webcam_stream \
  --config - <<EOF
stages:
  - type: motion_detector
    sensitivity: 0.8
  - type: object_detector
    model: yolov3
output:
  - type: webhook
    url: http://localhost:8000/events
EOF
```

2. Monitor system status and logs:
```bash
# Show system status
rtaspi status

# Follow logs
rtaspi logs -f --level info
```

3. Manage multiple streams:
```bash
# Start multiple streams
rtaspi streams start --device video0 --protocol rtsp --path /cam1
rtaspi streams start --device video1 --protocol webrtc --path /cam2

# List active streams
rtaspi streams list --status active
```

## Best Practices

1. **Shell Completion**: Install shell completion for improved productivity

2. **JSON Output**: Use `--json` for scripting and automation:
```bash
rtaspi devices list --json | jq '.devices[].id'
```

3. **Configuration Management**:
- Keep configuration files under version control
- Use environment variables for sensitive information
- Regularly validate configuration files

4. **Logging**:
- Use appropriate log levels for different environments
- Rotate log files to manage disk space
- Monitor logs for errors and warnings

5. **Resource Management**:
- Monitor system resources with `rtaspi status`
- Clean up unused streams and pipelines
- Use appropriate video quality settings

6. **Security**:
- Use strong passwords for network devices
- Enable SSL for production deployments
- Regularly update RTASPI and dependencies
