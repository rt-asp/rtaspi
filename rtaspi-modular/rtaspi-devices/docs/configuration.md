# RTASPI Devices Configuration Guide

This guide explains how to configure the RTASPI Devices module for different use cases.

## Configuration File Structure

The module uses YAML configuration files with the following structure:

```yaml
rtaspi_devices:
  # Global settings
  system:
    storage_path: "/var/lib/rtaspi/devices"
    log_level: "INFO"
    scan_interval: 60  # seconds
    
  # Device type configurations
  devices:
    local:
      enabled: true
      auto_connect: true
      drivers:
        - v4l2
        - alsa
      
    network:
      enabled: true
      discovery:
        enabled: true
        scan_ranges:
          - "192.168.1.0/24"
          - "10.0.0.0/24"
        protocols:
          - rtsp
          - onvif
      authentication:
        timeout: 30
        retries: 3
        
    industrial:
      enabled: true
      modbus:
        enabled: true
        timeout: 5000
        retry_count: 3
      opcua:
        enabled: true
        security_mode: "SignAndEncrypt"
        
    remote_desktop:
      enabled: true
      vnc:
        enabled: true
        preferred_encoding: "tight"
      rdp:
        enabled: true
        security_level: "high"
        
  # Stream configuration
  streaming:
    formats:
      - h264
      - mjpeg
      - raw
    default_format: "h264"
    port_range:
      start: 8000
      end: 9000
    
  # Protocol settings
  protocols:
    rtsp:
      transport: "tcp"
      timeout: 30
    rtmp:
      chunk_size: 4096
    http:
      port: 8080
      ssl: true
    
  # Event system configuration
  events:
    max_listeners: 100
    buffer_size: 1000
    
  # State management
  state:
    save_interval: 300  # seconds
    backup_count: 5
    
  # Security settings
  security:
    encryption:
      enabled: true
      algorithm: "AES-256"
    authentication:
      required: true
      token_expiry: 3600  # seconds
```

## Configuration Sections

### System Settings

Global system configuration:

```yaml
system:
  storage_path: "/var/lib/rtaspi/devices"  # Base storage path
  log_level: "INFO"                        # Logging level
  scan_interval: 60                        # Device scan interval
```

### Device Configuration

#### Local Devices

Configuration for physically connected devices:

```yaml
devices:
  local:
    enabled: true                # Enable local device support
    auto_connect: true          # Auto-connect on discovery
    drivers:                    # Enabled drivers
      - v4l2                    # Video4Linux2 driver
      - alsa                    # ALSA audio driver
    formats:                    # Supported formats
      - raw                     # Raw format
      - mjpeg                   # Motion JPEG
    resolutions:                # Supported resolutions
      - "1280x720"
      - "1920x1080"
```

#### Network Devices

Configuration for IP-based devices:

```yaml
devices:
  network:
    enabled: true
    discovery:
      enabled: true
      scan_ranges:              # Network ranges to scan
        - "192.168.1.0/24"
        - "10.0.0.0/24"
      protocols:               # Supported protocols
        - rtsp
        - onvif
    authentication:
      timeout: 30
      retries: 3
```

#### Industrial Devices

Configuration for industrial protocol devices:

```yaml
devices:
  industrial:
    enabled: true
    modbus:
      enabled: true
      timeout: 5000            # Connection timeout
      retry_count: 3          # Connection retries
    opcua:
      enabled: true
      security_mode: "SignAndEncrypt"
```

#### Remote Desktop

Configuration for remote desktop connections:

```yaml
devices:
  remote_desktop:
    enabled: true
    vnc:
      enabled: true
      preferred_encoding: "tight"
    rdp:
      enabled: true
      security_level: "high"
```

### Streaming Configuration

Media streaming settings:

```yaml
streaming:
  formats:                    # Supported formats
    - h264
    - mjpeg
    - raw
  default_format: "h264"     # Default format
  port_range:                # Port range for streams
    start: 8000
    end: 9000
```

### Protocol Settings

Protocol-specific configuration:

```yaml
protocols:
  rtsp:
    transport: "tcp"         # Transport protocol
    timeout: 30             # Connection timeout
  rtmp:
    chunk_size: 4096        # Chunk size for streaming
  http:
    port: 8080             # HTTP server port
    ssl: true              # Enable SSL/TLS
```

### Event System

Event handling configuration:

```yaml
events:
  max_listeners: 100        # Maximum event listeners
  buffer_size: 1000        # Event buffer size
```

### State Management

State persistence settings:

```yaml
state:
  save_interval: 300       # State save interval
  backup_count: 5         # Number of backups to keep
```

### Security Settings

Security configuration:

```yaml
security:
  encryption:
    enabled: true
    algorithm: "AES-256"   # Encryption algorithm
  authentication:
    required: true
    token_expiry: 3600    # Token expiry time
```

## Environment Variables

The module supports configuration through environment variables:

```bash
# System settings
export RTASPI_STORAGE_PATH="/custom/storage/path"
export RTASPI_LOG_LEVEL="DEBUG"

# Network settings
export RTASPI_NETWORK_SCAN_RANGES="192.168.1.0/24,10.0.0.0/24"
export RTASPI_NETWORK_PROTOCOLS="rtsp,onvif"

# Security settings
export RTASPI_SECURITY_KEY="your-secret-key"
export RTASPI_AUTH_REQUIRED="true"
```

## Configuration Loading

The module loads configuration in the following order:

1. Default configuration
2. Configuration file
3. Environment variables

Example:

```python
from rtaspi_devices.config import Config

# Load configuration
config = Config.load("config.yaml")

# Override with environment
config.update_from_env()

# Create manager with config
manager = DeviceManager(config)
```

## Configuration Validation

The module validates configuration using JSON Schema:

```python
from rtaspi_devices.config import validate_config

# Validate configuration
try:
    validate_config(config)
except ValidationError as e:
    print(f"Invalid configuration: {e}")
```

## Best Practices

1. **Security**
   - Always enable encryption for sensitive data
   - Use strong authentication mechanisms
   - Regularly rotate security tokens

2. **Performance**
   - Adjust scan intervals based on network size
   - Configure appropriate buffer sizes
   - Set reasonable timeouts

3. **Reliability**
   - Enable state persistence
   - Configure adequate retry mechanisms
   - Set up proper error handling

4. **Resource Management**
   - Configure appropriate port ranges
   - Set reasonable buffer sizes
   - Monitor resource usage
