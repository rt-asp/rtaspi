# Configuration Guide

RTASPI uses YAML configuration files to manage its settings. This guide explains all available configuration options.

## Configuration Files

RTASPI uses several configuration files:

1. **rtaspi.config.yaml**: Main system configuration
2. **rtaspi.devices.yaml**: Device-specific settings
3. **rtaspi.streams.yaml**: Stream configurations
4. **rtaspi.pipeline.yaml**: Processing pipeline settings
5. **rtaspi.secrets.yaml**: Sensitive information (credentials, tokens)

## Main Configuration (rtaspi.config.yaml)

### System Settings
```yaml
system:
  # Base directory for storing temporary files, logs, etc.
  storage_path: "storage"
  
  # Logging level (DEBUG, INFO, WARNING, ERROR)
  log_level: "INFO"
  
  # Enable/disable system components
  components:
    web_interface: true
    api_server: true
    cli: true
```

### Local Device Settings
```yaml
local_devices:
  # Enable/disable device types
  enable_video: true
  enable_audio: true
  
  # Auto-start streams when devices are detected
  auto_start: false
  
  # Device scanning interval (seconds)
  scan_interval: 60
  
  # Starting ports for different protocols
  rtsp_port_start: 8554
  rtmp_port_start: 1935
  webrtc_port_start: 8080
  
  # Device-specific settings
  video_settings:
    default_resolution: "1280x720"
    default_framerate: 30
  
  audio_settings:
    default_sample_rate: 44100
    default_channels: 2
```

### Network Device Settings
```yaml
network_devices:
  # Enable network device support
  enable: true
  
  # Device scanning interval (seconds)
  scan_interval: 60
  
  # Discovery settings
  discovery:
    enabled: true
    methods:
      - "onvif"
      - "upnp"
      - "mdns"
    
  # Protocol port ranges
  rtsp_port_start: 8654
  rtmp_port_start: 2935
  webrtc_port_start: 9080
```

### Streaming Settings
```yaml
streaming:
  rtsp:
    # RTSP server settings
    port_start: 8554
    transport: ["tcp", "udp"]
    
  rtmp:
    # RTMP server settings
    port_start: 1935
    chunk_size: 4096
    
  webrtc:
    # WebRTC settings
    port_start: 8080
    stun_server: "stun://stun.l.google.com:19302"
    turn_server: ""
    turn_username: ""
    turn_password: ""
```

### Processing Settings
```yaml
processing:
  # Video processing settings
  video:
    enable_gpu: true
    default_codec: "h264"
    
  # Audio processing settings
  audio:
    enable_noise_reduction: true
    default_codec: "aac"
    
  # Pipeline settings
  pipeline:
    buffer_size: 10
    max_parallel: 4
```

### Web Interface Settings
```yaml
web:
  # HTTP server settings
  host: "0.0.0.0"
  port: 8080
  
  # Security settings
  ssl:
    enabled: false
    cert_file: ""
    key_file: ""
  
  # Authentication
  auth:
    enabled: true
    type: "basic"  # basic, jwt
```

### API Settings
```yaml
api:
  # API server settings
  host: "0.0.0.0"
  port: 8081
  
  # Security settings
  auth:
    enabled: true
    type: "jwt"
    token_expiry: 3600
```

## Device Configuration (rtaspi.devices.yaml)

### Local Device Example
```yaml
devices:
  local:
    - id: "video0"
      type: "video"
      path: "/dev/video0"
      name: "Webcam"
      settings:
        resolution: "1920x1080"
        framerate: 30
        format: "YUYV"
    
    - id: "audio0"
      type: "audio"
      path: "hw:0,0"
      name: "Microphone"
      settings:
        sample_rate: 48000
        channels: 2
        format: "S16LE"
```

### Network Device Example
```yaml
devices:
  network:
    - id: "ipcam1"
      type: "video"
      protocol: "rtsp"
      address: "192.168.1.100"
      port: 554
      path: "/stream1"
      username: "${IPCAM1_USER}"  # References secrets file
      password: "${IPCAM1_PASS}"
      settings:
        profile: "high"
```

## Stream Configuration (rtaspi.streams.yaml)

```yaml
streams:
  - id: "webcam_stream"
    device_id: "video0"
    protocol: "rtsp"
    path: "/webcam"
    settings:
      video:
        codec: "h264"
        bitrate: "2M"
      audio:
        enabled: false
    
  - id: "ipcam_proxy"
    device_id: "ipcam1"
    protocol: "webrtc"
    path: "/camera1"
    processing:
      - type: "resize"
        width: 1280
        height: 720
      - type: "object_detection"
        model: "yolov3"
```

## Pipeline Configuration (rtaspi.pipeline.yaml)

```yaml
pipelines:
  - id: "motion_detection"
    input:
      stream_id: "ipcam_proxy"
    stages:
      - type: "motion_detector"
        sensitivity: 0.8
        region: [0, 0, 1920, 1080]
      
      - type: "object_detector"
        model: "yolov3"
        confidence: 0.5
        
      - type: "event_trigger"
        conditions:
          - type: "motion"
            duration: 5
          - type: "object"
            classes: ["person", "car"]
    
    output:
      - type: "webhook"
        url: "http://localhost:8000/events"
      - type: "record"
        format: "mp4"
        duration: 30
```

## Secrets Configuration (rtaspi.secrets.yaml)

```yaml
secrets:
  # Device credentials
  IPCAM1_USER: "admin"
  IPCAM1_PASS: "password123"
  
  # API tokens
  API_SECRET_KEY: "your-secret-key"
  
  # External service credentials
  CLOUD_STORAGE_KEY: "your-storage-key"
```

## Enum Configuration

RTASPI supports configurable enumerations that can be overridden through the configuration hierarchy. This allows customizing enum values without modifying the code.

### Enum Configuration in YAML

```yaml
enums:
  # Device type overrides
  DeviceType:
    USB_CAMERA: "usb_cam"    # Override auto() value
    IP_CAMERA: "ip_cam"
    
  # Device protocol overrides
  DeviceProtocol:
    RTSP: "rtsp_stream"      # Override default "rtsp" value
    WEBRTC: "webrtc_peer"    # Override default "webrtc" value
```

### Environment Variable Overrides

Enum values can be overridden using environment variables following the pattern:
```bash
RTASPI_{ENUM_CLASS}_{ENUM_NAME}=value
```

Examples:
```bash
# Override DeviceType.USB_CAMERA value
export RTASPI_DEVICETYPE_USB_CAMERA=usb_cam

# Override DeviceProtocol.RTSP value
export RTASPI_DEVICEPROTOCOL_RTSP=rtsp_stream
```

### Configuration Hierarchy

Enum values are resolved in the following order:
1. Environment variables (RTASPI_{ENUM_CLASS}_{ENUM_NAME})
2. Project configuration (rtaspi.config.yaml)
3. User configuration (~/.config/rtaspi/config.yaml)
4. Global configuration (/etc/rtaspi/config.yaml)
5. Default enum value

### Usage in Code

```python
from rtaspi.constants.devices import DeviceType
from rtaspi.core.config import ConfigManager

config_manager = ConfigManager()

# Get value using the hierarchical system
camera_type = DeviceType.USB_CAMERA.get_value(config_manager)

# Get constant-style name
type_constant = DeviceType.USB_CAMERA.CONSTANT_NAME  # Returns "USB_CAMERA"
```

## Environment Variables

Configuration values can reference environment variables using `${VAR_NAME}` syntax. This is particularly useful for sensitive information:

```yaml
api:
  auth:
    secret_key: "${API_SECRET_KEY}"
```

## Best Practices

1. **Security**:
   - Keep sensitive information in rtaspi.secrets.yaml
   - Use environment variables for deployment-specific settings
   - Enable SSL for production deployments

2. **Performance**:
   - Adjust buffer sizes based on available memory
   - Enable GPU processing if available
   - Set appropriate scan intervals

3. **Maintenance**:
   - Regular backup of configuration files
   - Version control for configuration changes
   - Documentation of custom settings

4. **Troubleshooting**:
   - Set log_level to DEBUG for detailed logging
   - Monitor resource usage
   - Regular validation of configuration files
