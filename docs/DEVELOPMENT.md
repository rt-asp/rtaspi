# Development Guide

This guide provides information for developers who want to contribute to RTASPI or extend its functionality.

## Development Environment Setup

1. **Clone the Repository**
```bash
git clone https://github.com/rt-asp/rtaspi.git
cd rtaspi
```

2. **Create Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

3. **Install Development Dependencies**
```bash
pip install -r requirements-dev.txt
```

4. **Install Pre-commit Hooks**
```bash
pre-commit install
```

## Project Structure

```
rtaspi/
├── docs/               # Documentation
├── examples/           # Example configurations and scripts
├── scripts/           # Development and maintenance scripts
├── src/               # Source code
│   └── rtaspi/
│       ├── api/       # REST API implementation
│       ├── cli/       # Command-line interface
│       ├── core/      # Core functionality
│       ├── device_managers/  # Device management
│       ├── processing/      # Stream processing
│       ├── schemas/   # Data models and validation
│       ├── streaming/ # Streaming protocols
│       └── web/       # Web interface
├── tests/             # Test suite
└── tools/             # Development tools
```

## Code Style

RTASPI follows PEP 8 with some modifications:

- Line length: 100 characters
- Docstring style: Google
- Import order: stdlib, third-party, local
- Type hints: Required for public interfaces

Example:
```python
from typing import List, Optional
import os
import sys

import numpy as np
from pydantic import BaseModel

from rtaspi.core.types import DeviceID
from rtaspi.schemas.device import Device


class StreamConfig(BaseModel):
    """Configuration for a media stream.

    Args:
        device_id: ID of the source device
        protocol: Streaming protocol to use
        path: Stream path/endpoint
        settings: Optional stream settings

    Raises:
        ValueError: If protocol is invalid
    """
    device_id: DeviceID
    protocol: str
    path: str
    settings: Optional[dict] = None

    def validate_protocol(self) -> None:
        """Validate the streaming protocol.

        Raises:
            ValueError: If protocol is not supported
        """
        valid_protocols = ["rtsp", "rtmp", "webrtc"]
        if self.protocol not in valid_protocols:
            raise ValueError(f"Invalid protocol: {self.protocol}")
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_discovery.py

# Run tests with coverage
pytest --cov=rtaspi

# Run tests in parallel
pytest -n auto
```

### Writing Tests

Use pytest fixtures and parametrize for clean, maintainable tests:

```python
import pytest
from rtaspi.device_managers.discovery import DeviceDiscovery

@pytest.fixture
def discovery():
    """Create a DeviceDiscovery instance for testing."""
    return DeviceDiscovery()

@pytest.mark.parametrize("protocol,expected", [
    ("rtsp", True),
    ("invalid", False),
])
def test_protocol_validation(discovery, protocol, expected):
    """Test protocol validation logic."""
    assert discovery.is_valid_protocol(protocol) == expected
```

## Documentation

### Building Documentation

```bash
# Install documentation dependencies
pip install -r docs/requirements.txt

# Build documentation
cd docs
make html
```

### Writing Documentation

- Use clear, concise language
- Include code examples
- Document exceptions and edge cases
- Keep API documentation up-to-date
- Add diagrams where helpful

## Debugging

### Logging

```python
from rtaspi.core.logging import get_logger

logger = get_logger(__name__)

logger.debug("Detailed information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error message", exc_info=True)
```

### Debugging Tools

1. **Interactive Debugger**
```python
import pdb; pdb.set_trace()
```

2. **Debug Configuration**
```yaml
system:
  log_level: "DEBUG"
  debug_mode: true
```

3. **Performance Profiling**
```bash
python -m cProfile -o profile.stats your_script.py
python -m pstats profile.stats
```

## Contributing

### Workflow

1. **Fork and Clone**
```bash
git clone https://github.com/your-username/rtaspi.git
```

2. **Create Feature Branch**
```bash
git checkout -b feature/your-feature-name
```

3. **Make Changes**
- Write code
- Add tests
- Update documentation

4. **Run Quality Checks**
```bash
# Run linter
flake8 src tests

# Run type checker
mypy src

# Run tests
pytest

# Run pre-commit hooks
pre-commit run --all-files
```

5. **Commit Changes**
```bash
git add .
git commit -m "feat: add your feature description"
```

6. **Push and Create Pull Request**
```bash
git push origin feature/your-feature-name
```

### Commit Message Format

Follow conventional commits:

- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- style: Code style changes
- refactor: Code refactoring
- test: Test changes
- chore: Build/maintenance changes

Example:
```
feat(streaming): add WebRTC support

- Add WebRTC streaming capability
- Implement STUN/TURN configuration
- Add WebRTC stream tests
```

## Extension Points

### Adding New Device Types

1. Create new device manager class:
```python
from rtaspi.device_managers.base import DeviceManager

class CustomDeviceManager(DeviceManager):
    """Custom device manager implementation."""

    def discover_devices(self):
        """Implement device discovery logic."""
        pass

    def start_device(self, device_id: str):
        """Implement device start logic."""
        pass
```

2. Register device manager:
```python
from rtaspi.core.registry import register_device_manager

register_device_manager("custom", CustomDeviceManager)
```

### Adding Processing Filters

1. Create new filter class:
```python
from rtaspi.processing.base import Filter

class CustomFilter(Filter):
    """Custom video/audio filter implementation."""

    def process_frame(self, frame):
        """Implement frame processing logic."""
        pass
```

2. Register filter:
```python
from rtaspi.core.registry import register_filter

register_filter("custom", CustomFilter)
```

### Adding Stream Protocols

1. Create new protocol handler:
```python
from rtaspi.streaming.base import StreamHandler

class CustomProtocolHandler(StreamHandler):
    """Custom streaming protocol implementation."""

    def start_stream(self, config):
        """Implement stream start logic."""
        pass

    def stop_stream(self):
        """Implement stream stop logic."""
        pass
```

2. Register protocol:
```python
from rtaspi.core.registry import register_protocol

register_protocol("custom", CustomProtocolHandler)
```

## Performance Optimization

### Memory Management

- Use generators for large datasets
- Implement proper cleanup in `__del__` methods
- Monitor memory usage with `memory_profiler`

### CPU Optimization

- Use numpy for numerical operations
- Implement caching where appropriate
- Profile code to identify bottlenecks

### GPU Acceleration

- Use CUDA when available
- Implement fallback for CPU-only systems
- Profile GPU memory usage

## Deployment

### Building Packages

```bash
# Build wheel
python setup.py bdist_wheel

# Build source distribution
python setup.py sdist
```

### Creating System Service

1. Create service file:
```ini
[Unit]
Description=RTASPI Service
After=network.target

[Service]
Type=simple
User=rtaspi
ExecStart=/usr/local/bin/rtaspi start
Restart=always

[Install]
WantedBy=multi-user.target
```

2. Install service:
```bash
sudo cp rtaspi.service /etc/systemd/system/
sudo systemctl enable rtaspi
sudo systemctl start rtaspi
```

## Troubleshooting

### Common Issues

1. **Device Detection**
- Check device permissions
- Verify hardware compatibility
- Check system logs

2. **Streaming Issues**
- Verify network connectivity
- Check port availability
- Monitor system resources

3. **Performance Problems**
- Profile code execution
- Monitor resource usage
- Check for memory leaks

### Debug Tools

1. **System Information**
```bash
rtaspi dev debug-info
```

2. **Connection Testing**
```bash
rtaspi dev test-connection
```

3. **Resource Monitoring**
```bash
rtaspi dev monitor
```

## Security Considerations

1. **Input Validation**
- Validate all user input
- Sanitize file paths
- Check parameter bounds

2. **Authentication**
- Use secure password storage
- Implement rate limiting
- Use HTTPS for web interface

3. **Device Access**
- Implement device access control
- Validate device credentials
- Monitor device access logs

## Best Practices

1. **Code Quality**
- Write comprehensive tests
- Document public interfaces
- Follow type hints
- Keep functions focused

2. **Performance**
- Profile before optimizing
- Use appropriate data structures
- Implement caching strategically

3. **Security**
- Review security implications
- Keep dependencies updated
- Follow security best practices

4. **Maintenance**
- Keep documentation updated
- Review and update dependencies
- Monitor system health
