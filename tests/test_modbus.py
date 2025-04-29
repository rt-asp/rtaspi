"""Tests for Modbus protocol support."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pymodbus.client import ModbusTcpClient, ModbusSerialClient
from pymodbus.exceptions import ModbusException
from pymodbus.payload import BinaryPayloadDecoder, BinaryPayloadBuilder

from rtaspi.device_managers.industrial.modbus import ModbusDevice, ModbusManager


@pytest.fixture
def modbus_config():
    """Create test Modbus configuration."""
    return {
        'mode': 'tcp',
        'host': 'localhost',
        'port': 502,
        'unit': 1,
        'registers': {
            'temperature': {
                'type': 'holding',
                'address': 100,
                'data_type': 'float32',
                'scale': 0.1,
                'offset': 0
            },
            'status': {
                'type': 'coil',
                'address': 0
            },
            'serial_number': {
                'type': 'holding',
                'address': 200,
                'data_type': 'string',
                'count': 8
            }
        }
    }


@pytest.fixture
def mock_tcp_client():
    """Mock Modbus TCP client."""
    with patch('rtaspi.device_managers.industrial.modbus.ModbusTcpClient') as mock:
        client = Mock()
        client.connect.return_value = True
        mock.return_value = client
        yield client


@pytest.fixture
def mock_serial_client():
    """Mock Modbus Serial client."""
    with patch('rtaspi.device_managers.industrial.modbus.ModbusSerialClient') as mock:
        client = Mock()
        client.connect.return_value = True
        mock.return_value = client
        yield client


@pytest.fixture
def device(modbus_config, mock_tcp_client):
    """Create test Modbus device."""
    device = ModbusDevice('test_device', modbus_config)
    device.connect()
    yield device
    device.disconnect()


def test_device_init(modbus_config):
    """Test device initialization."""
    device = ModbusDevice('test_device', modbus_config)
    
    # Check configuration
    assert device.device_id == 'test_device'
    assert device.mode == 'tcp'
    assert device.host == 'localhost'
    assert device.port == 502
    assert device.unit == 1
    assert 'temperature' in device.registers
    assert 'status' in device.registers
    assert 'serial_number' in device.registers


def test_tcp_connection(modbus_config, mock_tcp_client):
    """Test TCP connection."""
    device = ModbusDevice('test_device', modbus_config)
    
    # Test successful connection
    assert device.connect()
    assert device._connected
    mock_tcp_client.connect.assert_called_once()
    
    # Test connection failure
    mock_tcp_client.connect.return_value = False
    device._connected = False
    assert not device.connect()
    assert not device._connected


def test_serial_connection(mock_serial_client):
    """Test serial connection."""
    config = {
        'mode': 'rtu',
        'serial_port': '/dev/ttyUSB0',
        'baudrate': 9600,
        'parity': 'N',
        'stopbits': 1,
        'bytesize': 8
    }
    device = ModbusDevice('test_device', config)
    
    # Test successful connection
    assert device.connect()
    assert device._connected
    mock_serial_client.assert_called_with(
        method='rtu',
        port='/dev/ttyUSB0',
        baudrate=9600,
        parity='N',
        stopbits=1,
        bytesize=8
    )


def test_read_holding_register(device, mock_tcp_client):
    """Test reading holding register."""
    # Mock successful read
    result = Mock()
    result.isError.return_value = False
    result.registers = [0x4048, 0x0000]  # float32 value 3.125
    mock_tcp_client.read_holding_registers.return_value = result
    
    # Read temperature register
    value = device.read_register('temperature')
    assert value == pytest.approx(3.125 * 0.1)  # Apply scale
    mock_tcp_client.read_holding_registers.assert_called_with(100, 2, unit=1)
    
    # Test read error
    result.isError.return_value = True
    assert device.read_register('temperature') is None


def test_read_coil(device, mock_tcp_client):
    """Test reading coil."""
    # Mock successful read
    result = Mock()
    result.isError.return_value = False
    result.bits = [True]
    mock_tcp_client.read_coils.return_value = result
    
    # Read status register
    value = device.read_register('status')
    assert value is True
    mock_tcp_client.read_coils.assert_called_with(0, 1, unit=1)


def test_read_string(device, mock_tcp_client):
    """Test reading string."""
    # Mock successful read
    result = Mock()
    result.isError.return_value = False
    # "ABC123" as registers
    result.registers = [0x4142, 0x4331, 0x3233, 0x0000]
    mock_tcp_client.read_holding_registers.return_value = result
    
    # Read serial number register
    value = device.read_register('serial_number')
    assert value == "ABC123"
    mock_tcp_client.read_holding_registers.assert_called_with(200, 8, unit=1)


def test_write_holding_register(device, mock_tcp_client):
    """Test writing holding register."""
    # Mock successful write
    result = Mock()
    result.isError.return_value = False
    mock_tcp_client.write_registers.return_value = result
    
    # Write temperature register
    assert device.write_register('temperature', 31.25)  # Will be scaled to 312.5
    mock_tcp_client.write_registers.assert_called_once()
    registers = mock_tcp_client.write_registers.call_args[0][1]
    decoder = BinaryPayloadDecoder.fromRegisters(
        registers,
        byteorder='big',
        wordorder='big'
    )
    assert decoder.decode_32bit_float() == 312.5


def test_write_coil(device, mock_tcp_client):
    """Test writing coil."""
    # Mock successful write
    result = Mock()
    result.isError.return_value = False
    mock_tcp_client.write_coil.return_value = result
    
    # Write status register
    assert device.write_register('status', True)
    mock_tcp_client.write_coil.assert_called_with(0, True, unit=1)


def test_write_string(device, mock_tcp_client):
    """Test writing string."""
    # Mock successful write
    result = Mock()
    result.isError.return_value = False
    mock_tcp_client.write_registers.return_value = result
    
    # Write serial number register
    assert device.write_register('serial_number', "ABC123")
    mock_tcp_client.write_registers.assert_called_once()
    registers = mock_tcp_client.write_registers.call_args[0][1]
    decoder = BinaryPayloadDecoder.fromRegisters(
        registers,
        byteorder='big',
        wordorder='big'
    )
    assert decoder.decode_string(16).decode().strip('\x00') == "ABC123"


def test_read_all_registers(device):
    """Test reading all registers."""
    # Mock register reads
    device.read_register = Mock()
    device.read_register.side_effect = [31.25, True, "ABC123"]
    
    # Read all registers
    values = device.read_all_registers()
    assert values == {
        'temperature': 31.25,
        'status': True,
        'serial_number': "ABC123"
    }
    assert device.read_register.call_count == 3


def test_error_handling(device, mock_tcp_client):
    """Test error handling."""
    # Test connection error
    mock_tcp_client.connect.side_effect = ModbusException()
    device._connected = False
    assert not device.connect()
    
    # Test read error
    mock_tcp_client.read_holding_registers.side_effect = ModbusException()
    assert device.read_register('temperature') is None
    
    # Test write error
    mock_tcp_client.write_registers.side_effect = ModbusException()
    assert not device.write_register('temperature', 31.25)


def test_manager():
    """Test Modbus manager."""
    manager = ModbusManager()
    
    # Mock device
    device = Mock()
    device.connect.return_value = True
    with patch('rtaspi.device_managers.industrial.modbus.ModbusDevice', return_value=device):
        # Add device
        assert manager.add_device('test_device', {})
        assert 'test_device' in manager._devices
        
        # Get device
        assert manager.get_device('test_device') == device
        assert manager.get_devices() == [device]
        
        # Remove device
        assert manager.remove_device('test_device')
        assert 'test_device' not in manager._devices
        device.disconnect.assert_called_once()
        
        # Cleanup
        manager.add_device('test_device', {})
        manager.cleanup()
        assert not manager._devices
        device.disconnect.assert_called()


def test_device_status(device):
    """Test device status."""
    status = device.get_status()
    assert status['id'] == 'test_device'
    assert status['connected'] is True
    assert status['mode'] == 'tcp'
    assert status['host'] == 'localhost'
    assert status['unit'] == 1
    assert set(status['registers']) == {'temperature', 'status', 'serial_number'}
