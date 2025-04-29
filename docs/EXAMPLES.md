# Usage Examples and Tutorials

This document provides practical examples and tutorials for common RTASPI use cases.

## Basic Examples

### 1. Stream from USB Webcam

```bash
# Start RTASPI
rtaspi start

# List available devices
rtaspi devices list

# Start RTSP stream from webcam
rtaspi streams start \
  --device video0 \
  --protocol rtsp \
  --path /webcam \
  --video-codec h264 \
  --video-bitrate 2M
```

Access the stream at: `rtsp://localhost:8554/webcam`

### 2. Connect IP Camera

```bash
# Add network camera
rtaspi devices add \
  --type network \
  --protocol rtsp \
  --address 192.168.1.100 \
  --port 554 \
  --username admin \
  --password secret

# Start WebRTC stream
rtaspi streams start \
  --device ipcam1 \
  --protocol webrtc \
  --path /camera1
```

Access the stream at: `http://localhost:8080/webrtc/camera1`

### 3. Record Audio from Microphone

```bash
# Start RTMP stream from microphone
rtaspi streams start \
  --device audio0 \
  --protocol rtmp \
  --path /mic \
  --audio-codec aac \
  --audio-bitrate 128k

# Record stream
rtaspi pipelines create \
  --input mic_stream \
  --config - <<EOF
output:
  - type: "record"
    format: "mp3"
    path: "recordings/"
EOF
```

## Advanced Examples

### 1. Motion Detection Pipeline

Create a pipeline that detects motion and sends notifications:

```yaml
# motion_detection.yaml
pipelines:
  - id: "security_cam"
    input:
      stream_id: "camera1"
    
    stages:
      - type: "motion_detector"
        sensitivity: 0.8
        region: [0, 0, 1920, 1080]
        min_area: 1000
      
      - type: "object_detector"
        model: "yolov3"
        confidence: 0.5
        classes: ["person", "car"]
      
      - type: "event_trigger"
        conditions:
          - type: "motion"
            duration: 5
          - type: "object"
            classes: ["person"]
    
    output:
      - type: "webhook"
        url: "http://localhost:8000/alerts"
      
      - type: "record"
        format: "mp4"
        duration: 30
        pre_buffer: 5
```

```bash
# Start the pipeline
rtaspi pipelines create --config motion_detection.yaml
```

### 2. Multi-Camera Setup

Stream from multiple cameras with different configurations:

```yaml
# multi_camera.yaml
streams:
  - id: "entrance_cam"
    device_id: "ipcam1"
    protocol: "rtsp"
    path: "/entrance"
    settings:
      video:
        codec: "h264"
        bitrate: "2M"
        framerate: 30
      audio:
        enabled: false
  
  - id: "parking_cam"
    device_id: "ipcam2"
    protocol: "rtmp"
    path: "/parking"
    settings:
      video:
        codec: "h264"
        bitrate: "1M"
        framerate: 15
      audio:
        enabled: false
  
  - id: "reception_cam"
    device_id: "video0"
    protocol: "webrtc"
    path: "/reception"
    settings:
      video:
        codec: "vp8"
        bitrate: "1.5M"
      audio:
        enabled: true
        codec: "opus"
```

```bash
# Start all streams
rtaspi streams start --config multi_camera.yaml
```

### 3. Video Processing Pipeline

Create a pipeline for real-time video processing:

```yaml
# video_processing.yaml
pipelines:
  - id: "video_effects"
    input:
      stream_id: "webcam_stream"
    
    stages:
      - type: "resize"
        width: 1280
        height: 720
      
      - type: "color_correction"
        brightness: 1.2
        contrast: 1.1
        saturation: 1.1
      
      - type: "overlay"
        text: "%timestamp%"
        position: [10, 10]
        font: "Arial"
        size: 24
      
      - type: "face_detection"
        model: "face_detection_v1"
        blur_faces: true
    
    output:
      - type: "rtmp"
        url: "rtmp://localhost/live/processed"
      
      - type: "webrtc"
        path: "/processed"
```

```bash
# Start the processing pipeline
rtaspi pipelines create --config video_processing.yaml
```

### 4. Audio Processing Pipeline

Create a pipeline for audio processing:

```yaml
# audio_processing.yaml
pipelines:
  - id: "audio_effects"
    input:
      stream_id: "mic_stream"
    
    stages:
      - type: "noise_reduction"
        strength: 0.7
      
      - type: "equalizer"
        bands:
          - frequency: 100
            gain: -3
          - frequency: 1000
            gain: 2
          - frequency: 8000
            gain: 1
      
      - type: "compressor"
        threshold: -20
        ratio: 4
        attack: 5
        release: 50
      
      - type: "speech_detection"
        language: "en"
        output_format: "srt"
    
    output:
      - type: "rtmp"
        url: "rtmp://localhost/live/processed_audio"
      
      - type: "file"
        path: "subtitles.srt"
```

```bash
# Start the audio processing pipeline
rtaspi pipelines create --config audio_processing.yaml
```

## Integration Examples

### 1. Web Application Integration

```javascript
// Connect to WebSocket API
const ws = new WebSocket('ws://localhost:8081/api/ws');

// Subscribe to events
ws.send(JSON.stringify({
  type: 'subscribe',
  topics: ['devices/status', 'streams/status']
}));

// Handle events
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  switch(data.type) {
    case 'device_status':
      updateDeviceStatus(data);
      break;
    case 'stream_status':
      updateStreamStatus(data);
      break;
  }
};

// Start WebRTC stream
async function startStream(deviceId) {
  const response = await fetch('http://localhost:8081/api/streams', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + token
    },
    body: JSON.stringify({
      device_id: deviceId,
      protocol: 'webrtc',
      path: '/stream1'
    })
  });
  
  const data = await response.json();
  const player = new RTCPeerConnection();
  // ... WebRTC setup code ...
}
```

### 2. REST API Integration

Python example using requests:

```python
import requests

class RTASPIClient:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {'Authorization': f'Bearer {token}'}
    
    def list_devices(self):
        response = requests.get(
            f'{self.base_url}/api/devices',
            headers=self.headers
        )
        return response.json()
    
    def start_stream(self, device_id, protocol, path):
        response = requests.post(
            f'{self.base_url}/api/streams',
            headers=self.headers,
            json={
                'device_id': device_id,
                'protocol': protocol,
                'path': path
            }
        )
        return response.json()
    
    def create_pipeline(self, config):
        response = requests.post(
            f'{self.base_url}/api/pipelines',
            headers=self.headers,
            json=config
        )
        return response.json()

# Usage example
client = RTASPIClient('http://localhost:8081', 'your-token')

# List devices
devices = client.list_devices()

# Start stream
stream = client.start_stream('video0', 'rtsp', '/webcam')

# Create pipeline
pipeline = client.create_pipeline({
    'id': 'motion_detection',
    'input': {'stream_id': stream['id']},
    'stages': [
        {
            'type': 'motion_detector',
            'sensitivity': 0.8
        }
    ],
    'output': [
        {
            'type': 'webhook',
            'url': 'http://localhost:8000/events'
        }
    ]
})
```

### 3. System Service Integration

Create a systemd service for automatic startup:

1. Create service file `/etc/systemd/system/rtaspi.service`:
```ini
[Unit]
Description=RTASPI Service
After=network.target

[Service]
Type=simple
User=rtaspi
Environment=RTASPI_CONFIG=/etc/rtaspi/config.yaml
ExecStart=/usr/local/bin/rtaspi start
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

2. Create configuration in `/etc/rtaspi/config.yaml`:
```yaml
system:
  storage_path: "/var/lib/rtaspi"
  log_level: "INFO"

local_devices:
  enable_video: true
  enable_audio: true
  auto_start: true

streaming:
  rtsp:
    port_start: 8554
  rtmp:
    port_start: 1935
  webrtc:
    port_start: 8080
```

3. Setup and start service:
```bash
# Create rtaspi user
sudo useradd -r rtaspi

# Create directories
sudo mkdir -p /etc/rtaspi /var/lib/rtaspi
sudo chown -R rtaspi:rtaspi /etc/rtaspi /var/lib/rtaspi

# Enable and start service
sudo systemctl enable rtaspi
sudo systemctl start rtaspi
```

## Best Practices

1. **Resource Management**
   - Monitor system resources
   - Use appropriate video quality settings
   - Clean up unused streams and pipelines

2. **Security**
   - Use strong passwords
   - Enable SSL/TLS
   - Implement access control
   - Monitor access logs

3. **Performance**
   - Choose appropriate codecs
   - Set reasonable bitrates
   - Monitor network bandwidth
   - Use hardware acceleration when available

4. **Reliability**
   - Implement error handling
   - Set up automatic recovery
   - Monitor system health
   - Keep logs for troubleshooting
