# RTASPI Core Module

Core functionality for the Real-Time Annotation and Stream Processing Interface (RTASPI) system.

## Features

- Configuration management with hierarchical support
- Environment variable integration
- Type-safe configuration using Pydantic models
- Extensible architecture for additional core components

## Installation

```bash
# Install in development mode
pip install -e ".[dev]"

# Install for production
pip install .
```

## Configuration Management

The configuration system supports multiple levels of configuration that are merged in order of precedence:

1. Environment variables (highest precedence)
2. Project configuration (`./rtaspi/config.yaml`)
3. User configuration (`~/.config/rtaspi/config.yaml`)
4. Global configuration (`/etc/rtaspi/config.yaml`)
5. Default configuration (lowest precedence)

### Basic Usage

```python
from rtaspi_core import get_config, set_config_value

# Get current configuration
config = get_config()

# Access configuration values
log_level = config.system.log_level
web_port = config.web.port

# Set configuration values
set_config_value("system.log_level", "DEBUG")
set_config_value("web.port", 9000)
```

### Custom Configuration Manager

```python
from rtaspi_core.config import create_config_manager, RTASPIConfig

# Create custom configuration manager
manager = create_config_manager(
    config_model=RTASPIConfig,
    default_config={
        "system": {
            "log_level": "INFO",
        }
    },
    env_map={
        "CUSTOM_LOG_LEVEL": "system.log_level",
    }
)

# Use custom manager
config = manager.config
manager.set("system.log_level", "DEBUG")
```

### Environment Variables

The following environment variables are supported by default:

- `RTASPI_STORAGE_PATH`: Set storage directory
- `RTASPI_LOG_LEVEL`: Set logging level
- `RTASPI_WEB_PORT`: Set web server port
- `RTASPI_WEB_HOST`: Set web server host
- `RTASPI_ENABLE_HTTPS`: Enable/disable HTTPS
- `RTASPI_CERT_PATH`: Path to SSL certificate
- `RTASPI_KEY_PATH`: Path to SSL private key
- `RTASPI_STUN_SERVER`: WebRTC STUN server
- `RTASPI_TURN_SERVER`: WebRTC TURN server
- `RTASPI_TURN_USERNAME`: TURN server username
- `RTASPI_TURN_PASSWORD`: TURN server password

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/config/test_manager.py

# Run with coverage report
pytest --cov=rtaspi_core

# Run tests by marker
pytest -m "unit"
pytest -m "integration"
pytest -m "config"
```

### Test Categories

Tests are organized using markers:

- `unit`: Unit tests
- `integration`: Integration tests
- `config`: Configuration management tests
- `models`: Data model tests
- `utils`: Utility function tests

### Code Style

The project uses:

- Black for code formatting
- isort for import sorting
- mypy for type checking
- pylint for linting

Run formatters:
```bash
black rtaspi_core/
isort rtaspi_core/
```

Run type checking:
```bash
mypy rtaspi_core/
```

Run linting:
```bash
pylint rtaspi_core/
```

## Project Structure

```
rtaspi-core/
├── pyproject.toml         # Project configuration
├── setup.py              # Installation configuration
├── README.md             # This file
├── rtaspi_core/          # Source code
│   ├── __init__.py      # Package initialization
│   └── config/          # Configuration management
│       ├── __init__.py
│       ├── manager.py   # Configuration manager
│       └── models.py    # Configuration models
└── tests/               # Test suite
    ├── conftest.py      # Test fixtures
    └── config/          # Configuration tests
        ├── test_manager.py
        └── test_models.py
```

## Dependencies

Core dependencies:
- pyyaml: Configuration file handling
- python-dotenv: Environment variable management
- structlog: Structured logging
- typing-extensions: Enhanced typing support
- pydantic: Data validation
- aiohttp: Async HTTP client/server
- python-json-logger: JSON logging format

Development dependencies:
- pytest: Testing framework
- pytest-asyncio: Async test support
- pytest-cov: Coverage reporting
- black: Code formatting
- isort: Import sorting
- mypy: Type checking
- pylint: Code linting

## License

MIT License - see LICENSE file for details
