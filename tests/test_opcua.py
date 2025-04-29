"""Tests for OPC UA protocol support."""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from asyncua import Client, Node, ua
from asyncua.common.node import Node as NodeType

from rtaspi.device_managers.industrial.opcua import OPCUADevice, OPCUAManager


@pytest.fixture
def opcua_config():
    """Create test OPC UA configuration."""
    return {
        'url': 'opc.tcp://localhost:4840',
        'username': 'test_user',
        'password': 'test_pass',
        'security_policy': 'Basic256Sha256',
        'security_mode': 'SignAndEncrypt',
        'certificate': '/path/to/cert.pem',
        'private_key': '/path/to/key.pem',
        'nodes': {
            'temperature': {
                'id': 'ns=2;s=temperature',
                'scale': 0.1,
                'offset': 0,
                'subscribe': True,
                'interval': 1000
            },
            'status': {
                'id': 'ns=2;s=status'
            },
            'serial_number': {
                'id': 'ns=2;s=serial_number'
            }
        }
    }


@pytest.fixture
def mock_client():
    """Mock OPC UA client."""
    with patch('rtaspi.device_managers.industrial.opcua.Client') as mock:
        client = MagicMock()
        mock.return_value = client
        
        # Mock security settings
        client.set_security = asyncio.Future()
        client.set_security.set_result(None)
        
        # Mock authentication
        client.set_user = asyncio.Future()
        client.set_user.set_result(None)
        client.set_password = asyncio.Future()
        client.set_password.set_result(None)
        
        # Mock connection
        client.connect = asyncio.Future()
        client.connect.set_result(None)
        client.disconnect = asyncio.Future()
        client.disconnect.set_result(None)
        
        yield client


@pytest.fixture
def device(opcua_config, mock_client):
    """Create test OPC UA device."""
    device = OPCUADevice('test_device', opcua_config)
    device.connect()
    yield device
    device.disconnect()


def test_device_init(opcua_config):
    """Test device initialization."""
    device = OPCUADevice('test_device', opcua_config)
    
    # Check configuration
    assert device.device_id == 'test_device'
    assert device.url == 'opc.tcp://localhost:4840'
    assert device.username == 'test_user'
    assert device.password == 'test_pass'
    assert device.security_policy == 'Basic256Sha256'
    assert device.security_mode == 'SignAndEncrypt'
    assert device.certificate == '/path/to/cert.pem'
    assert device.private_key == '/path/to/key.pem'
    assert 'temperature' in device.nodes
    assert 'status' in device.nodes
    assert 'serial_number' in device.nodes


def test_connection(opcua_config, mock_client):
    """Test connection handling."""
    device = OPCUADevice('test_device', opcua_config)
    
    # Test successful connection
    assert device.connect()
    assert device._connected
    
    # Check security settings
    mock_client.set_security.assert_called_with(
        certificate='/path/to/cert.pem',
        private_key='/path/to/key.pem',
        policy=ua.SecurityPolicyType.Basic256Sha256,
        mode=ua.MessageSecurityMode.SignAndEncrypt
    )
    
    # Check authentication
    mock_client.set_user.assert_called_with('test_user')
    mock_client.set_password.assert_called_with('test_pass')
    
    # Check connection
    mock_client.connect.assert_called_once()
    
    # Test disconnection
    device.disconnect()
    assert not device._connected
    mock_client.disconnect.assert_called_once()


def test_read_node(device, mock_client):
    """Test node reading."""
    # Mock node
    node = MagicMock()
    mock_client.get_node.return_value = node
    
    # Mock read value
    value_future = asyncio.Future()
    value_future.set_result(31.25)
    node.read_value = value_future
    
    # Read temperature node
    value = device.read_node('temperature')
    assert value == pytest.approx(31.25 * 0.1)  # Apply scale
    mock_client.get_node.assert_called_with('ns=2;s=temperature')
    
    # Test read error
    value_future = asyncio.Future()
    value_future.set_exception(Exception("Read error"))
    node.read_value = value_future
    assert device.read_node('temperature') is None


def test_write_node(device, mock_client):
    """Test node writing."""
    # Mock node
    node = MagicMock()
    mock_client.get_node.return_value = node
    
    # Mock write value
    write_future = asyncio.Future()
    write_future.set_result(None)
    node.write_value = write_future
    
    # Write temperature node
    assert device.write_node('temperature', 31.25)  # Will be scaled to 312.5
    mock_client.get_node.assert_called_with('ns=2;s=temperature')
    node.write_value.assert_called_with(312.5)
    
    # Test write error
    write_future = asyncio.Future()
    write_future.set_exception(Exception("Write error"))
    node.write_value = write_future
    assert not device.write_node('temperature', 31.25)


def test_subscription(device, mock_client):
    """Test subscription handling."""
    # Mock subscription
    subscription = MagicMock()
    subscription_future = asyncio.Future()
    subscription_future.set_result(subscription)
    mock_client.create_subscription.return_value = subscription_future
    
    # Mock node
    node = MagicMock()
    mock_client.get_node.return_value = node
    
    # Mock subscribe
    subscribe_future = asyncio.Future()
    subscribe_future.set_result(None)
    subscription.subscribe_data_change = subscribe_future
    
    # Create subscription
    handler = Mock()
    device._loop.run_until_complete(
        device._create_subscription('temperature', {
            'id': 'ns=2;s=temperature',
            'interval': 1000,
            'handler': handler
        })
    )
    
    # Check subscription
    mock_client.create_subscription.assert_called_with(1000, handler)
    mock_client.get_node.assert_called_with('ns=2;s=temperature')
    subscription.subscribe_data_change.assert_called_with(node)
    assert 'temperature' in device._subscriptions


def test_read_all_nodes(device):
    """Test reading all nodes."""
    # Mock node reads
    device.read_node = Mock()
    device.read_node.side_effect = [31.25, True, "ABC123"]
    
    # Read all nodes
    values = device.read_all_nodes()
    assert values == {
        'temperature': 31.25,
        'status': True,
        'serial_number': "ABC123"
    }
    assert device.read_node.call_count == 3


def test_error_handling(device, mock_client):
    """Test error handling."""
    # Test connection error
    connect_future = asyncio.Future()
    connect_future.set_exception(Exception("Connection failed"))
    mock_client.connect.return_value = connect_future
    device._connected = False
    assert not device.connect()
    
    # Test read error
    node = MagicMock()
    mock_client.get_node.return_value = node
    read_future = asyncio.Future()
    read_future.set_exception(Exception("Read error"))
    node.read_value = read_future
    assert device.read_node('temperature') is None
    
    # Test write error
    write_future = asyncio.Future()
    write_future.set_exception(Exception("Write error"))
    node.write_value = write_future
    assert not device.write_node('temperature', 31.25)


def test_manager():
    """Test OPC UA manager."""
    manager = OPCUAManager()
    
    # Mock device
    device = Mock()
    device.connect.return_value = True
    with patch('rtaspi.device_managers.industrial.opcua.OPCUADevice', return_value=device):
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
    assert status['url'] == 'opc.tcp://localhost:4840'
    assert status['security_policy'] == 'Basic256Sha256'
    assert status['security_mode'] == 'SignAndEncrypt'
    assert set(status['nodes']) == {'temperature', 'status', 'serial_number'}
