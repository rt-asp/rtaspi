# Web Interface Examples

This directory contains examples demonstrating RTASPI's web interface capabilities.

## Examples

### 1. HTTPS Server (`https_server.py`)
Shows how to:
- Set up secure HTTPS server
- Handle SSL certificates
- Configure routes
- Manage authentication

### 2. Matrix View (`matrix_view.py`)
Demonstrates:
- Multi-camera display
- Layout management
- Stream synchronization
- Interactive controls

### 3. REST API (`rest_api.py`)
Features:
- RESTful endpoints
- OpenAPI documentation
- Authentication
- Rate limiting

### 4. WebRTC Streaming (`webrtc_streaming.py`)
Implements:
- Browser-based streaming
- Peer connections
- Media constraints
- Network traversal

## Configuration Files

### `server_config.yaml`
```yaml
server:
  host: 0.0.0.0
  port: 8443
  ssl:
    cert: certs/server.crt
    key: certs/server.key
  cors:
    origins: ["*"]
    methods: ["GET", "POST"]

auth:
  type: jwt
  secret: ${JWT_SECRET}
  expiry: 3600

rate_limit:
  requests: 100
  window: 60
```

### `matrix_config.yaml`
```yaml
layout:
  rows: 2
  columns: 2
  fullscreen: true

streams:
  - name: Camera 1
    url: rtsp://camera1/stream
    position: [0, 0]
  - name: Camera 2
    url: rtsp://camera2/stream
    position: [0, 1]
```

## Requirements

- RTASPI with web extensions
- FastAPI
- WebRTC support
- SSL certificates

## Usage

1. Configure web interface:
```bash
# Generate SSL certificates
./generate_certs.sh

# Copy and edit configuration
cp server_config.yaml.example server_config.yaml
cp matrix_config.yaml.example matrix_config.yaml
```

2. Run examples:
```bash
# HTTPS server
python https_server.py --config server_config.yaml

# Matrix view
python matrix_view.py --config matrix_config.yaml

# REST API
python rest_api.py --port 8080

# WebRTC streaming
python webrtc_streaming.py --stun stun.l.google.com:19302
```

## Features

### HTTPS Server
- Automatic certificate management
- HTTP/2 support
- WebSocket support
- Static file serving

### Matrix View
- Flexible layouts
- Drag-and-drop support
- Full-screen mode
- Performance optimization

### REST API
- Swagger documentation
- JWT authentication
- Request validation
- Response caching

### WebRTC
- Peer discovery
- ICE negotiation
- Quality adaptation
- Connection recovery

## Security

### Authentication
- JWT tokens
- OAuth2 support
- Role-based access
- Session management

### SSL/TLS
- Certificate management
- Protocol selection
- Cipher configuration
- Security headers

### API Security
- Input validation
- CORS policies
- Rate limiting
- Error handling

## Best Practices

1. Server Configuration
   - Use secure defaults
   - Enable compression
   - Configure timeouts
   - Handle errors

2. Performance
   - Enable caching
   - Optimize assets
   - Use WebSocket
   - Monitor resources

3. Development
   - Use TypeScript
   - Follow REST conventions
   - Document APIs
   - Write tests

## Troubleshooting

Common issues and solutions:

1. Certificate Problems
   - Check certificate validity
   - Verify trust chain
   - Update expired certs
   - Configure paths

2. Connection Issues
   - Check CORS settings
   - Verify WebSocket
   - Test STUN/TURN
   - Monitor timeouts

3. Performance
   - Optimize stream quality
   - Adjust buffer sizes
   - Enable compression
   - Monitor memory usage

## Support

For web interface issues:
- Check documentation
- Join web development channel on Discord
- Submit detailed bug reports
- Share improvements
