"""Tests for Home Assistant integration."""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
import websocket
import requests

from rtaspi.automation.hass import HomeAssistant


@pytest.fixture
def hass_config():
    """Create test Home Assistant configuration."""
    return {
        'host': 'localhost',
        'port': 8123,
        'token': 'test_token',
        'use_ssl': True,
        'verify_ssl': True
    }


@pytest.fixture
def mock_requests():
    """Mock requests library."""
    with patch('rtaspi.automation.hass.requests') as mock_req:
        # Mock successful API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_req.get.return_value = mock_response
        yield mock_req


@pytest.fixture
def mock_websocket():
    """Mock websocket library."""
    with patch('rtaspi.automation.hass.websocket') as mock_ws:
        # Mock WebSocket app
        mock_app = Mock()
        mock_ws.WebSocketApp.return_value = mock_app
        
        # Store callbacks for testing
        callbacks = {}
        def create_ws(url, **kwargs):
            for name, callback in kwargs.items():
                if name.startswith('on_'):
                    callbacks[name] = callback
            return mock_app
        mock_ws.WebSocketApp.side_effect = create_ws
        
        yield mock_ws, callbacks


@pytest.fixture
def client(hass_config, mock_requests, mock_websocket):
    """Create test Home Assistant client."""
    client = HomeAssistant(hass_config)
    client.connect()
    yield client
    client.disconnect()


def test_client_init(hass_config):
    """Test client initialization."""
    client = HomeAssistant(hass_config)
    
    # Check configuration
    assert client.host == hass_config['host']
    assert client.port == hass_config['port']
    assert client.token == hass_config['token']
    assert client.use_ssl == hass_config['use_ssl']
    assert client.verify_ssl == hass_config['verify_ssl']
    
    # Check API URLs
    assert client.api_url == 'https://localhost:8123/api'
    assert client.ws_url == 'wss://localhost:8123/api/websocket'
    
    # Check headers
    assert client.headers['Authorization'] == 'Bearer test_token'
    assert client.headers['Content-Type'] == 'application/json'


def test_client_connect(client, mock_requests, mock_websocket):
    """Test client connection."""
    mock_ws, callbacks = mock_websocket
    
    # Check API connection
    mock_requests.get.assert_called_once_with(
        'https://localhost:8123/api/',
        headers=client.headers,
        verify=client.verify_ssl
    )
    
    # Check WebSocket connection
    mock_ws.WebSocketApp.assert_called_once()
    assert client._ws is not None
    assert client._ws_thread is not None
    assert client._ws_thread.daemon
    
    # Test WebSocket callbacks
    assert 'on_open' in callbacks
    assert 'on_message' in callbacks
    assert 'on_error' in callbacks
    assert 'on_close' in callbacks


def test_client_disconnect(client, mock_websocket):
    """Test client disconnection."""
    mock_ws, _ = mock_websocket
    mock_app = mock_ws.WebSocketApp.return_value
    
    # Disconnect
    client.disconnect()
    
    # Check cleanup
    assert client._ws_stop.is_set()
    mock_app.close.assert_called_once()
    assert client._ws is None
    assert client._ws_thread is None
    assert not client._ws_connected
    assert not client._ws_authenticated


def test_websocket_callbacks(client, mock_websocket):
    """Test WebSocket callbacks."""
    mock_ws, callbacks = mock_websocket
    mock_app = mock_ws.WebSocketApp.return_value
    
    # Test connection opened
    callbacks['on_open'](mock_app)
    assert client._ws_connected
    mock_app.send.assert_called_with(json.dumps({
        'type': 'auth',
        'access_token': client.token
    }))
    
    # Test authentication success
    callbacks['on_message'](mock_app, json.dumps({
        'type': 'auth_ok'
    }))
    assert client._ws_authenticated
    
    # Test authentication failure
    callbacks['on_message'](mock_app, json.dumps({
        'type': 'auth_invalid'
    }))
    assert not client._ws_authenticated
    mock_app.close.assert_called_once()
    
    # Test error handling
    callbacks['on_error'](mock_app, Exception("Test error"))
    
    # Test connection closed
    callbacks['on_close'](mock_app)
    assert not client._ws_connected
    assert not client._ws_authenticated


def test_register_device(client):
    """Test device registration."""
    # Mock successful response
    client._send_ws_message = Mock(return_value={'success': True})
    
    # Register device
    device_info = {
        'id': 'test_device',
        'name': 'Test Device',
        'manufacturer': 'Test Manufacturer',
        'model': 'Test Model',
        'sw_version': '1.0.0',
        'connections': [['mac', '00:11:22:33:44:55']]
    }
    device_id = client.register_device(device_info)
    
    # Check registration
    assert device_id == 'test_device'
    assert device_id in client._devices
    assert client._devices[device_id] == device_info
    
    # Check message
    client._send_ws_message.assert_called_once()
    message = client._send_ws_message.call_args[0][0]
    assert message['type'] == 'config/device_registry/create'
    assert message['device_id'] == device_id
    assert message['name'] == device_info['name']
    assert message['manufacturer'] == device_info['manufacturer']
    assert message['model'] == device_info['model']
    assert message['sw_version'] == device_info['sw_version']
    assert message['identifiers'] == [device_id]
    assert message['connections'] == device_info['connections']


def test_register_entity(client):
    """Test entity registration."""
    # Mock successful response
    client._send_ws_message = Mock(return_value={'success': True})
    
    # Register entity
    entity_info = {
        'domain': 'sensor',
        'name': 'Test Sensor',
        'device_id': 'test_device',
        'device_class': 'temperature',
        'unit': '°C',
        'icon': 'mdi:thermometer'
    }
    entity_id = client.register_entity(entity_info)
    
    # Check registration
    assert entity_id == 'sensor.rtaspi_test_sensor'
    assert entity_id in client._entities
    assert client._entities[entity_id] == entity_info
    
    # Check message
    client._send_ws_message.assert_called_once()
    message = client._send_ws_message.call_args[0][0]
    assert message['type'] == 'config/entity_registry/create'
    assert message['entity_id'] == entity_id
    assert message['name'] == entity_info['name']
    assert message['device_id'] == entity_info['device_id']
    assert message['platform'] == 'rtaspi'
    assert message['device_class'] == entity_info['device_class']
    assert message['unit_of_measurement'] == entity_info['unit']
    assert message['icon'] == entity_info['icon']


def test_update_state(client):
    """Test state updates."""
    # Mock successful response
    client._send_ws_message = Mock(return_value={'success': True})
    
    # Update state
    assert client.update_state(
        'sensor.test',
        25.5,
        {'unit': '°C', 'friendly_name': 'Test Sensor'}
    )
    
    # Check message
    client._send_ws_message.assert_called_once()
    message = client._send_ws_message.call_args[0][0]
    assert message['type'] == 'state/update'
    assert message['entity_id'] == 'sensor.test'
    assert message['state'] == 25.5
    assert message['attributes'] == {'unit': '°C', 'friendly_name': 'Test Sensor'}


def test_subscribe_events(client):
    """Test event subscription."""
    # Mock successful response
    client._send_ws_message = Mock(return_value={'success': True})
    
    # Subscribe to events
    callback = Mock()
    assert client.subscribe_events('state_changed', callback)
    
    # Check subscription
    client._send_ws_message.assert_called_once()
    message = client._send_ws_message.call_args[0][0]
    assert message['type'] == 'subscribe_events'
    assert message['event_type'] == 'state_changed'
    
    # Test event handling
    handle_event = client._send_ws_message.call_args[0][1]
    event = {
        'type': 'event',
        'event': {
            'event_type': 'state_changed',
            'data': {'entity_id': 'sensor.test'}
        }
    }
    handle_event(event)
    callback.assert_called_once_with(event['event'])


def test_call_service(client):
    """Test service calls."""
    # Mock successful response
    client._send_ws_message = Mock(return_value={'success': True})
    
    # Call service
    assert client.call_service(
        'light',
        'turn_on',
        {'entity_id': 'light.test', 'brightness': 255}
    )
    
    # Check message
    client._send_ws_message.assert_called_once()
    message = client._send_ws_message.call_args[0][0]
    assert message['type'] == 'call_service'
    assert message['domain'] == 'light'
    assert message['service'] == 'turn_on'
    assert message['service_data'] == {'entity_id': 'light.test', 'brightness': 255}


def test_send_message(client):
    """Test message sending."""
    # Mock WebSocket
    client._ws = Mock()
    client._ws_authenticated = True
    
    # Create test message
    message = {'type': 'test', 'data': 'test'}
    
    # Test with callback
    callback = Mock()
    response = client._send_ws_message(message, callback)
    assert response == {'success': True}
    assert client._ws_message_id in client._ws_callbacks
    assert client._ws_callbacks[client._ws_message_id] == callback
    
    # Test without callback
    response = client._send_ws_message(message)
    assert response is None  # Timeout waiting for response
    
    # Test message sending
    client._ws.send.assert_called_with(json.dumps({
        'id': client._ws_message_id,
        'type': 'test',
        'data': 'test'
    }))


def test_error_handling(client):
    """Test error handling."""
    # Test API error
    with patch('rtaspi.automation.hass.requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.RequestException()
        assert not client.connect()
    
    # Test WebSocket error
    client._ws = Mock()
    client._ws.send.side_effect = websocket.WebSocketException()
    assert client._send_ws_message({'type': 'test'}) is None
    
    # Test message handling error
    client._ws_callbacks[1] = Mock(side_effect=Exception())
    client._on_ws_message(client._ws, json.dumps({
        'id': 1,
        'type': 'result',
        'success': True
    }))  # Should not raise
