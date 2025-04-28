"""
test_network_devices.py
"""

import os
import json
import pytest
from unittest.mock import patch, MagicMock, call

from rtaspi.core.mcp import MCPBroker
from rtaspi.device_managers.network_devices import NetworkDevicesManager
from rtaspi.device_managers.utils.device import NetworkDevice

# Fixtures
@pytest.fixture
def config(tmp_path):
    """Test configuration with temporary directory."""
    return {
        'system': {
            'storage_path': str(tmp_path)
        },
        'network_devices': {
            'enable': True,
            'scan_interval': 1,  # Short interval for tests
            'discovery_enabled': True,
            'discovery_methods': ['onvif', 'upnp', 'mdns'],
            'rtsp_port_start': 8654,
            'rtmp_port_start': 2935,
            'webrtc_port_start': 9080
        }
    }

@pytest.fixture
def mcp_broker():
    """MCP broker fixture."""
    return MCPBroker()

@pytest.fixture
def network_devices_manager(config, mcp_broker):
    """Network devices manager fixture."""
    with patch('rtaspi.device_managers.network_devices.ONVIFDiscovery'), \
            patch('rtaspi.device_managers.network_devices.UPnPDiscovery'), \
            patch('rtaspi.device_managers.network_devices.MDNSDiscovery'), \
            patch('rtaspi.device_managers.network_devices.RTSPServer'), \
            patch('rtaspi.device_managers.network_devices.RTMPServer'), \
            patch('rtaspi.device_managers.network_devices.WebRTCServer'):
        manager = NetworkDevicesManager(config, mcp_broker)
        yield manager

def test_add_device(network_devices_manager):
    """Test adding a device."""
    # Mock methods
    network_devices_manager._check_device_status = MagicMock()
    network_devices_manager._save_devices = MagicMock()
    network_devices_manager.mcp_client.publish = MagicMock()

    # Add device
    device_id = network_devices_manager.add_device(
        name='Test Camera',
        ip='192.168.1.100',
        port=554,
        username='admin',
        password='admin',
        type='video',
        protocol='rtsp',
        paths=['cam/realmonitor']
    )

    # Check if device was added
    assert device_id is not None
    assert device_id in network_devices_manager.devices
    device = network_devices_manager.devices[device_id]
    assert device.name == 'Test Camera'
    assert device.ip == '192.168.1.100'
    assert device.port == 554
    assert device.username == 'admin'
    assert device.password == 'admin'
    assert device.type == 'video'
    assert device.protocol == 'rtsp'
    assert len(device.streams) == 1

    # Check if methods were called
    network_devices_manager._check_device_status.assert_called_once()
    network_devices_manager._save_devices.assert_called_once()
    network_devices_manager.mcp_client.publish.assert_called_once()

def test_remove_device(network_devices_manager):
    """Test removing a device."""
    # Add sample device
    device = NetworkDevice(
        device_id='test_device',
        name='Test Camera',
        type='video',
        ip='192.168.1.100',
        port=554,
        username='admin',
        password='admin',
        protocol='rtsp'
    )
    network_devices_manager.devices['test_device'] = device

    # Mock methods
    network_devices_manager._save_devices = MagicMock()
    network_devices_manager.mcp_client.publish = MagicMock()

    # Remove device
    result = network_devices_manager.remove_device('test_device')

    # Check if device was removed
    assert result is True
    assert 'test_device' not in network_devices_manager.devices

    # Check if methods were called
    network_devices_manager._save_devices.assert_called_once()
    network_devices_manager.mcp_client.publish.assert_called_once()

@patch('socket.socket')
def test_check_device_status(mock_socket, network_devices_manager):
    """Test checking device status."""
    # Create sample device
    device = NetworkDevice(
        device_id='test_device',
        name='Test Camera',
        type='video',
        ip='192.168.1.100',
        port=554,
        protocol='rtsp'
    )

    # Simulate socket response
    mock_socket_instance = MagicMock()
    mock_socket.return_value = mock_socket_instance
    mock_socket_instance.connect_ex.return_value = 0  # Port open

    # Check device status
    network_devices_manager._check_device_status(device)

    # Check if status was updated
    assert device.status == 'online'

    # Change simulation - port closed
    mock_socket_instance.connect_ex.return_value = 1

    # Check device status again
    device.last_check = 0  # Reset last check time
    network_devices_manager._check_device_status(device)

    # Check if status was updated
    assert device.status == 'offline'

def test_discover_devices(network_devices_manager):
    """Test device discovery."""
    # Mock discovery modules
    onvif_module = MagicMock()
    upnp_module = MagicMock()
    mdns_module = MagicMock()

    # Simulate found devices
    onvif_module.discover.return_value = [{
        'name': 'ONVIF Camera',
        'ip': '192.168.1.101',
        'port': 80,
        'type': 'video',
        'protocol': 'rtsp',
        'paths': ['onvif1']
    }]

    upnp_module.discover.return_value = [{
        'name': 'UPnP Camera',
        'ip': '192.168.1.102',
        'port': 80,
        'type': 'video',
        'protocol': 'http'
    }]

    mdns_module.discover.return_value = [{
        'name': 'mDNS Camera',
        'ip': '192.168.1.103',
        'port': 80,
        'type': 'video',
        'protocol': 'rtsp'
    }]

    # Replace discovery modules
    network_devices_manager.discovery_modules = {
        'onvif': onvif_module,
        'upnp': upnp_module,
        'mdns': mdns_module
    }

    # Mock add_device method
    network_devices_manager.add_device = MagicMock(return_value='new_device_id')

    # Discover devices
    network_devices_manager._discover_devices()

    # Check if methods were called
    onvif_module.discover.assert_called_once()
    upnp_module.discover.assert_called_once()
    mdns_module.discover.assert_called_once()

    # Check if devices were added
    assert network_devices_manager.add_device.call_count == 3

@patch('rtaspi.device_managers.network_devices.RTSPServer.proxy_stream')
def test_start_stream(mock_proxy_stream, network_devices_manager):
    """Test starting a stream."""
    # Create sample device
    device = NetworkDevice(
        device_id='test_device',
        name='Test Camera',
        type='video',
        ip='192.168.1.100',
        port=554,
        protocol='rtsp'
    )
    device.streams = {'stream1': 'rtsp://192.168.1.100:554/stream1'}
    network_devices_manager.devices['test_device'] = device

    # Simulate RTSP server response
    mock_proxy_stream.return_value = 'rtsp://localhost:8654/test'

    # Start stream
    url = network_devices_manager.start_stream('test_device', protocol='rtsp', transcode=True)

    # Check if stream was started
    assert url == 'rtsp://localhost:8654/test'
    mock_proxy_stream.assert_called_once()

    # Test direct stream (without proxy)
    mock_proxy_stream.reset_mock()
    url = network_devices_manager.start_stream('test_device')

    # Check if stream was started
    assert url == 'rtsp://192.168.1.100:554/stream1'
    mock_proxy_stream.assert_not_called()

def test_handle_command(network_devices_manager):
    """Test MCP command handling."""
    # Create sample device
    device = NetworkDevice(
        device_id='test_device',
        name='Test Camera',
        type='video',
        ip='192.168.1.100',
        port=554,
        protocol='rtsp'
    )
    network_devices_manager.devices['test_device'] = device

    # Mock methods
    network_devices_manager._scan_devices = MagicMock()
    network_devices_manager._discover_devices = MagicMock()
    network_devices_manager.add_device = MagicMock(return_value='new_device_id')
    network_devices_manager.remove_device = MagicMock(return_value=True)
    network_devices_manager.start_stream = MagicMock(return_value='rtsp://localhost:8654/test')
    network_devices_manager.stop_stream = MagicMock(return_value=True)
    network_devices_manager.mcp_client.publish = MagicMock()

    # Test scan command
    network_devices_manager._handle_command('command/network_devices/scan', {})
    network_devices_manager._scan_devices.assert_called_once()

    # Test discover command
    network_devices_manager._handle_command('command/network_devices/discover', {})
    network_devices_manager._discover_devices.assert_called_once()

    # Test add_device command
    network_devices_manager._handle_command('command/network_devices/add_device', {
        'name': 'New Camera',
        'ip': '192.168.1.200',
        'port': 554,
        'type': 'video',
        'protocol': 'rtsp'
    })
    network_devices_manager.add_device.assert_called_once()

    # Test remove_device command
    network_devices_manager._handle_command('command/network_devices/remove_device', {
        'device_id': 'test_device'
    })
    network_devices_manager.remove_device.assert_called_with('test_device')

    # Test start_stream command
    network_devices_manager._handle_command('command/network_devices/start_stream', {
        'device_id': 'test_device',
        'protocol': 'rtsp',
        'transcode': True
    })
    network_devices_manager.start_stream.assert_called_with(
        device_id='test_device',
        stream_path=None,
        protocol='rtsp',
        transcode=True
    )

    # Test stop_stream command
    network_devices_manager._handle_command('command/network_devices/stop_stream', {
        'stream_id': 'test_stream'
    })
    network_devices_manager.stop_stream.assert_called_with('test_stream')

def test_load_save_devices(network_devices_manager, config, mcp_broker):
    """Test loading and saving devices."""
    # Create sample device
    device = NetworkDevice(
        device_id='test_device',
        name='Test Camera',
        type='video',
        ip='192.168.1.100',
        port=554,
        username='admin',
        password='admin',
        protocol='rtsp'
    )
    device.streams = {'stream1': 'rtsp://192.168.1.100:554/stream1'}

    # Add device to manager
    network_devices_manager.devices['test_device'] = device

    # Save devices
    network_devices_manager._save_devices()

    # Create new manager that should load saved devices
    with patch('rtaspi.device_managers.network_devices.ONVIFDiscovery'), \
            patch('rtaspi.device_managers.network_devices.UPnPDiscovery'), \
            patch('rtaspi.device_managers.network_devices.MDNSDiscovery'), \
            patch('rtaspi.device_managers.network_devices.RTSPServer'), \
            patch('rtaspi.device_managers.network_devices.RTMPServer'), \
            patch('rtaspi.device_managers.network_devices.WebRTCServer'):
        new_manager = NetworkDevicesManager(config, mcp_broker)

    # Check if device was loaded
    assert 'test_device' in new_manager.devices
    loaded_device = new_manager.devices['test_device']
    assert loaded_device.name == 'Test Camera'
    assert loaded_device.ip == '192.168.1.100'
    assert loaded_device.port == 554
    assert loaded_device.username == 'admin'
    assert loaded_device.password == 'admin'
    assert loaded_device.type == 'video'
    assert loaded_device.protocol == 'rtsp'
    assert 'stream1' in loaded_device.streams

def test_stop_stream(network_devices_manager):
    """Test stopping a stream."""
    # Create sample direct stream
    network_devices_manager.streams['direct_stream'] = {
        'device_id': 'test_device',
        'url': 'rtsp://192.168.1.100:554/stream1',
        'source_url': 'rtsp://192.168.1.100:554/stream1',
        'protocol': 'rtsp',
        'direct': True
    }

    # Create sample proxy stream
    mock_process = MagicMock()
    mock_rtsp_process = MagicMock()
    network_devices_manager.streams['proxy_stream'] = {
        'process': mock_process,
        'rtsp_process': mock_rtsp_process,
        'device_id': 'test_device',
        'url': 'rtsp://localhost:8654/test',
        'source_url': 'rtsp://192.168.1.100:554/stream1',
        'protocol': 'rtsp',
        'port': 8654
    }

    # Mock method
    network_devices_manager._publish_stream_stopped = MagicMock()

    # Stop direct stream
    result1 = network_devices_manager.stop_stream('direct_stream')

    # Check if stream was stopped
    assert result1 is True
    assert 'direct_stream' not in network_devices_manager.streams
    network_devices_manager._publish_stream_stopped.assert_called_once()

    # Reset mock
    network_devices_manager._publish_stream_stopped.reset_mock()

    # Stop proxy stream
    result2 = network_devices_manager.stop_stream('proxy_stream')

    # Check if stream was stopped
    assert result2 is True
    mock_process.terminate.assert_called_once()
    mock_rtsp_process.terminate.assert_called_once()
    assert 'proxy_stream' not in network_devices_manager.streams
    network_devices_manager._publish_stream_stopped.assert_called_once()

def test_start_and_stop(network_devices_manager):
    """Test that start and stop work and set running flag."""
    assert not getattr(network_devices_manager, 'running', False)
    network_devices_manager.start()
    assert network_devices_manager.running
    network_devices_manager.stop()
    assert not network_devices_manager.running

def test_load_saved_devices(network_devices_manager):
    """Test loading saved devices does not crash on empty dir."""
    network_devices_manager._load_saved_devices()  # Should not raise
    assert isinstance(getattr(network_devices_manager, 'devices', {}), dict)

def test_event_subscription(network_devices_manager):
    """Test _subscribe_to_events sets up subscriptions."""
    network_devices_manager.mcp_broker.subscribe = MagicMock()
    network_devices_manager._subscribe_to_events()
    network_devices_manager.mcp_broker.subscribe.assert_called()
