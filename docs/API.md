# API Reference

RTASPI provides a comprehensive RESTful API for managing devices, streams, and pipelines. This document details all available endpoints and their usage.

## Authentication

The API uses JWT (JSON Web Token) authentication. To access protected endpoints:

1. Obtain a token:
```bash
curl -X POST http://localhost:8081/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}'
```

2. Use the token in subsequent requests:
```bash
curl -H "Authorization: Bearer your-token" http://localhost:8081/api/devices
```

## Device Management

### List Devices
```http
GET /api/devices
```

Response:
```json
{
  "devices": [
    {
      "id": "video0",
      "type": "video",
      "name": "Webcam",
      "status": "active",
      "capabilities": {
        "resolutions": ["1920x1080", "1280x720"],
        "formats": ["YUYV", "MJPG"]
      }
    }
  ]
}
```

### Get Device Details
```http
GET /api/devices/{device_id}
```

Response:
```json
{
  "id": "video0",
  "type": "video",
  "name": "Webcam",
  "path": "/dev/video0",
  "status": "active",
  "settings": {
    "resolution": "1920x1080",
    "framerate": 30,
    "format": "YUYV"
  },
  "capabilities": {
    "resolutions": ["1920x1080", "1280x720"],
    "formats": ["YUYV", "MJPG"],
    "framerates": [30, 60]
  }
}
```

### Add Network Device
```http
POST /api/devices
```

Request:
```json
{
  "type": "network",
  "protocol": "rtsp",
  "address": "192.168.1.100",
  "port": 554,
  "path": "/stream1",
  "username": "admin",
  "password": "password"
}
```

### Update Device Settings
```http
PATCH /api/devices/{device_id}
```

Request:
```json
{
  "settings": {
    "resolution": "1280x720",
    "framerate": 60
  }
}
```

### Remove Device
```http
DELETE /api/devices/{device_id}
```

## Stream Management

### List Streams
```http
GET /api/streams
```

Response:
```json
{
  "streams": [
    {
      "id": "webcam_stream",
      "device_id": "video0",
      "protocol": "rtsp",
      "status": "active",
      "url": "rtsp://localhost:8554/webcam"
    }
  ]
}
```

### Get Stream Details
```http
GET /api/streams/{stream_id}
```

Response:
```json
{
  "id": "webcam_stream",
  "device_id": "video0",
  "protocol": "rtsp",
  "status": "active",
  "url": "rtsp://localhost:8554/webcam",
  "settings": {
    "video": {
      "codec": "h264",
      "bitrate": "2M",
      "framerate": 30
    },
    "audio": {
      "enabled": false
    }
  },
  "stats": {
    "uptime": 3600,
    "bytes_sent": 1024000,
    "clients_connected": 2
  }
}
```

### Start Stream
```http
POST /api/streams
```

Request:
```json
{
  "device_id": "video0",
  "protocol": "rtsp",
  "path": "/webcam",
  "settings": {
    "video": {
      "codec": "h264",
      "bitrate": "2M"
    },
    "audio": {
      "enabled": false
    }
  }
}
```

### Update Stream Settings
```http
PATCH /api/streams/{stream_id}
```

Request:
```json
{
  "settings": {
    "video": {
      "bitrate": "4M"
    }
  }
}
```

### Stop Stream
```http
DELETE /api/streams/{stream_id}
```

## Pipeline Management

### List Pipelines
```http
GET /api/pipelines
```

Response:
```json
{
  "pipelines": [
    {
      "id": "motion_detection",
      "status": "running",
      "input": {
        "stream_id": "webcam_stream"
      }
    }
  ]
}
```

### Get Pipeline Details
```http
GET /api/pipelines/{pipeline_id}
```

Response:
```json
{
  "id": "motion_detection",
  "status": "running",
  "input": {
    "stream_id": "webcam_stream"
  },
  "stages": [
    {
      "type": "motion_detector",
      "settings": {
        "sensitivity": 0.8,
        "region": [0, 0, 1920, 1080]
      }
    }
  ],
  "output": [
    {
      "type": "webhook",
      "url": "http://localhost:8000/events"
    }
  ],
  "stats": {
    "uptime": 3600,
    "events_triggered": 10,
    "last_event": "2025-04-29T08:15:30Z"
  }
}
```

### Create Pipeline
```http
POST /api/pipelines
```

Request:
```json
{
  "id": "motion_detection",
  "input": {
    "stream_id": "webcam_stream"
  },
  "stages": [
    {
      "type": "motion_detector",
      "sensitivity": 0.8,
      "region": [0, 0, 1920, 1080]
    },
    {
      "type": "object_detector",
      "model": "yolov3",
      "confidence": 0.5
    }
  ],
  "output": [
    {
      "type": "webhook",
      "url": "http://localhost:8000/events"
    }
  ]
}
```

### Update Pipeline
```http
PATCH /api/pipelines/{pipeline_id}
```

Request:
```json
{
  "stages": [
    {
      "type": "motion_detector",
      "sensitivity": 0.9
    }
  ]
}
```

### Delete Pipeline
```http
DELETE /api/pipelines/{pipeline_id}
```

## System Management

### Get System Status
```http
GET /api/system/status
```

Response:
```json
{
  "version": "1.0.0",
  "uptime": 3600,
  "components": {
    "web_interface": "running",
    "api_server": "running",
    "device_manager": "running"
  },
  "resources": {
    "cpu_usage": 25.5,
    "memory_usage": 512.0,
    "disk_usage": 1024.0
  }
}
```

### Get System Logs
```http
GET /api/system/logs
```

Query Parameters:
- `level`: Log level (debug, info, warning, error)
- `start`: Start timestamp
- `end`: End timestamp
- `limit`: Maximum number of logs to return

Response:
```json
{
  "logs": [
    {
      "timestamp": "2025-04-29T08:00:00Z",
      "level": "info",
      "component": "device_manager",
      "message": "New device detected: video0"
    }
  ]
}
```

### Update System Configuration
```http
PATCH /api/system/config
```

Request:
```json
{
  "system": {
    "log_level": "DEBUG"
  },
  "streaming": {
    "rtsp": {
      "port_start": 8654
    }
  }
}
```

## WebSocket API

RTASPI also provides a WebSocket API for real-time updates.

### Connect to WebSocket
```javascript
const ws = new WebSocket('ws://localhost:8081/api/ws');
```

### Subscribe to Events
```javascript
ws.send(JSON.stringify({
  type: 'subscribe',
  topics: [
    'devices/status',
    'streams/status',
    'pipelines/events'
  ]
}));
```

### Event Examples

Device Status Change:
```json
{
  "type": "device_status",
  "device_id": "video0",
  "status": "active",
  "timestamp": "2025-04-29T08:00:00Z"
}
```

Stream Status Update:
```json
{
  "type": "stream_status",
  "stream_id": "webcam_stream",
  "status": "streaming",
  "clients_connected": 2,
  "timestamp": "2025-04-29T08:00:00Z"
}
```

Pipeline Event:
```json
{
  "type": "pipeline_event",
  "pipeline_id": "motion_detection",
  "event": {
    "type": "motion_detected",
    "region": [100, 100, 200, 200],
    "confidence": 0.85
  },
  "timestamp": "2025-04-29T08:00:00Z"
}
```

## Error Handling

The API uses standard HTTP status codes and returns detailed error messages:

```json
{
  "error": {
    "code": "DEVICE_NOT_FOUND",
    "message": "Device with ID 'video0' not found",
    "details": {
      "device_id": "video0"
    }
  }
}
```

Common status codes:
- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 409: Conflict
- 500: Internal Server Error

## Rate Limiting

The API implements rate limiting to prevent abuse:

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1619683200
```

## Versioning

The API version is included in the response headers:

```http
X-API-Version: 1.0.0
```

## CORS

The API supports Cross-Origin Resource Sharing (CORS) for web client integration:

```http
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE
Access-Control-Allow-Headers: Content-Type, Authorization
