# RTASPI Devices Examples

This directory contains example code demonstrating various features and use cases of the RTASPI Devices module.

## Directory Structure

```
examples/
├── basic_usage/           # Basic usage examples
│   ├── simple_example.py  # Simple device management
│   └── quick_start.py     # Quick start with discovery
├── integrations/          # Integration examples
│   └── cross_module.py    # Cross-module integration
└── network/              # Network device examples
    ├── device_discovery.py    # Network discovery
    └── advanced_discovery.py  # Advanced discovery
```

## Basic Usage Examples

### Simple Example

Demonstrates basic device management functionality:

```bash
python examples/basic_usage/simple_example.py
```

Features demonstrated:
- Device manager configuration
- Network device creation
- Stream management
- Basic error handling

### Quick Start

Shows device discovery and event handling:

```bash
python examples/basic_usage/quick_start.py
```

Features demonstrated:
- Automatic device discovery
- Event system usage
- Stream management
- Device status monitoring

## Integration Examples

### Cross-Module Integration

Shows integration with other RTASPI modules:

```bash
python examples/integrations/cross_module.py
```

Features demonstrated:
- MCP broker usage
- Cross-module communication
- Pipeline integration
- Event handling

## Network Examples

### Device Discovery

Basic network device discovery:

```bash
python examples/network/device_discovery.py
```

Features demonstrated:
- Network scanning
- Protocol detection
- Device identification

### Advanced Discovery

Advanced network device discovery features:

```bash
python examples/network/advanced_discovery.py
```

Features demonstrated:
- Custom protocol handlers
- Advanced scanning options
- Device filtering
- State persistence

## Running the Examples

1. Install required dependencies:
   ```bash
   pip install -e .[examples]
   ```

2. Configure your environment:
   ```bash
   # Create storage directory
   mkdir -p storage/devices

   # Copy example config
   cp config/example.yaml config/core.yaml
   ```

3. Run desired example:
   ```bash
   python examples/basic_usage/quick_start.py
   ```

## Configuration

Examples use configuration from `config/` directory:

- `core.yaml`: Core configuration
- `devices.yaml`: Device-specific settings
- `network.yaml`: Network discovery settings

## Common Issues

1. **Permission Errors**
   - Ensure proper permissions for device access
   - Run with sudo if needed for hardware access

2. **Network Issues**
   - Check firewall settings
   - Verify network device accessibility
   - Ensure correct IP ranges in config

3. **Missing Dependencies**
   - Install optional dependencies:
     ```bash
     pip install -e .[all]
     ```

## Development

To create new examples:

1. Choose appropriate directory based on example type
2. Create new Python file with descriptive name
3. Include detailed docstring explaining purpose
4. Add error handling and cleanup
5. Update this README with new example

## Best Practices

1. **Configuration**
   - Use configuration files for settings
   - Don't hardcode sensitive data
   - Document all configuration options

2. **Error Handling**
   - Include proper try/except blocks
   - Clean up resources in finally blocks
   - Log errors appropriately

3. **Documentation**
   - Include detailed docstrings
   - Comment complex logic
   - Update README for new examples

4. **Testing**
   - Test with different configurations
   - Verify error handling
   - Check resource cleanup

## Contributing

1. Fork the repository
2. Create feature branch
3. Add or modify examples
4. Update documentation
5. Submit pull request

## License

All examples are licensed under the same terms as the RTASPI project.
