# Industrial Integration Examples

This directory contains examples demonstrating RTASPI's industrial protocol support.

## Examples

### 1. Modbus Integration (`modbus_example.py`)
Shows how to:
- Connect to Modbus TCP/RTU devices
- Read/write registers
- Handle device events
- Monitor industrial sensors

### 2. OPC UA Client (`opcua_client.py`)
Demonstrates:
- OPC UA client setup
- Node browsing
- Data subscription
- Event handling

### 3. Industrial Camera (`industrial_camera.py`)
Examples of:
- GigE Vision camera integration
- Machine vision processing
- Quality control automation
- Production line monitoring

## Configuration Files

### `modbus_config.yaml`
```yaml
device:
  type: modbus_tcp
  host: 192.168.1.100
  port: 502
  unit_id: 1
registers:
  - address: 1000
    type: holding
    name: temperature
  - address: 1001
    type: coil
    name: pump_status
```

### `opcua_config.yaml`
```yaml
server:
  url: opc.tcp://localhost:4840
  security_mode: None
  security_policy: None
nodes:
  - id: ns=2;s=temperature
    name: Temperature Sensor
  - id: ns=2;s=pressure
    name: Pressure Sensor
```

## Requirements

- RTASPI with industrial extensions
- pymodbus>=3.9.2
- asyncua>=1.1.6
- Additional hardware-specific dependencies

## Usage

1. Configure your industrial devices:
```bash
# Copy and edit configuration
cp modbus_config.yaml.example modbus_config.yaml
cp opcua_config.yaml.example opcua_config.yaml
```

2. Run examples:
```bash
# Modbus example
python modbus_example.py --config modbus_config.yaml

# OPC UA example
python opcua_client.py --config opcua_config.yaml

# Industrial camera
python industrial_camera.py --device GigE://192.168.1.100
```

## Hardware Support

### Supported Protocols
- Modbus TCP/RTU
- OPC UA
- EtherNet/IP
- GigE Vision
- Profinet (basic support)

### Tested Devices
- Siemens S7 PLCs
- Allen-Bradley CompactLogix
- Omron NJ/NX Series
- Basler/FLIR Cameras

## Error Handling

Examples include robust error handling for:
- Connection failures
- Protocol errors
- Device timeouts
- Data validation

## Troubleshooting

Common issues and solutions:
1. Connection Problems
   - Check network settings
   - Verify device IP/port
   - Test with device diagnostic tools

2. Protocol Errors
   - Verify protocol settings
   - Check device compatibility
   - Enable debug logging

3. Performance Issues
   - Adjust polling rates
   - Optimize data requests
   - Monitor network traffic

## Security Notes

- Always use secure protocols when available
- Implement proper authentication
- Follow industrial network best practices
- Keep firmware updated
