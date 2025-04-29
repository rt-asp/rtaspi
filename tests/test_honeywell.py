"""Tests for Honeywell alarm system integration."""

import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import time
import json

from rtaspi.security.alarms.honeywell import HoneywellAlarmSystem, API_BASE, API_ENDPOINTS, ARM_MODES
from rtaspi.security.alarms.base import AlarmState, AlarmZone, AlarmEvent


@pytest.fixture
def honeywell_config():
    """Create test Honeywell configuration."""
    return {
        'system_id': 'test_system',
        'name': 'Test Honeywell',
        'username': 'test_user',
        'password': 'test_pass',
        'application_id': 'test_app',
        'application_version': '1.0.0',
        'location_id': '1234',
        'device_id': '5678',
        'session_timeout': 1,
        'keepalive_interval': 1
    }


@pytest.fixture
def mock_response():
    """Create mock response."""
    response = Mock()
    response.raise_for_status = Mock()
    response.json.return_value = {
        'resultCode': 0,
        'sessionId': 'test_session',
        'resultData': 'Success'
    }
    return response


@pytest.fixture
def mock_requests(mock_response):
    """Mock requests module."""
    with patch('requests.post', return_value=mock_response) as mock:
        yield mock


@pytest.fixture
def system(honeywell_config, mock_requests):
    """Create test Honeywell system."""
    system = HoneywellAlarmSystem(honeywell_config)
    yield system
    system.disconnect()


def test_system_init(honeywell_config):
    """Test system initialization."""
    system = HoneywellAlarmSystem(honeywell_config)
    
    # Check configuration
    assert system.system_id == 'test_system'
    assert system.name == 'Test Honeywell'
    assert system.username == 'test_user'
    assert system.password == 'test_pass'
    assert system.application_id == 'test_app'
    assert system.application_version == '1.0.0'
    assert system.location_id == '1234'
    assert system.device_id == '5678'
    assert system.session_timeout == 1
    assert system.keepalive_interval == 1
    
    # Check state
    assert not system._connected
    assert not system._session_id
    assert not system._session_start
    assert not system._keepalive_thread
    assert system._stop_keepalive.is_set()


def test_api_call(system, mock_requests, mock_response):
    """Test API call handling."""
    # Test successful call
    result = system._api_call('authenticate', {'test': 'data'})
    assert result == mock_response.json()
    mock_requests.assert_called_with(
        f"{API_BASE}{API_ENDPOINTS['authenticate']}",
        json={'test': 'data'}
    )
    
    # Test with session ID
    system._session_id = 'test_session'
    result = system._api_call('get_panel_status', {'test': 'data'})
    assert result == mock_response.json()
    mock_requests.assert_called_with(
        f"{API_BASE}{API_ENDPOINTS['get_panel_status']}",
        json={'test': 'data', 'sessionId': 'test_session'}
    )
    
    # Test request error
    mock_requests.side_effect = requests.RequestException()
    assert system._api_call('test', {}) is None
    
    # Test response error
    mock_requests.side_effect = None
    mock_response.raise_for_status.side_effect = requests.HTTPError()
    assert system._api_call('test', {}) is None


def test_connection(system, mock_requests, mock_response):
    """Test connection handling."""
    # Test successful connection
    mock_response.json.return_value = {
        'resultCode': 0,
        'sessionId': 'test_session',
        'panelStatus': {
            'armedState': 0,
            'alarmState': 0,
            'zones': []
        },
        'zones': [],
        'events': []
    }
    
    assert system.connect()
    assert system._connected
    assert system._session_id == 'test_session'
    assert system._session_start is not None
    assert system._keepalive_thread and system._keepalive_thread.is_alive()
    
    # Check authentication
    mock_requests.assert_any_call(
        f"{API_BASE}{API_ENDPOINTS['authenticate']}",
        json={
            'userName': 'test_user',
            'password': 'test_pass',
            'applicationId': 'test_app',
            'applicationVersion': '1.0.0'
        }
    )
    
    # Test authentication failure
    mock_response.json.return_value = {
        'resultCode': 1,
        'resultData': 'Auth failed'
    }
    system.disconnect()
    assert not system.connect()
    assert not system._connected
    
    # Test connection error
    mock_requests.side_effect = requests.RequestException()
    assert not system.connect()
    assert not system._connected


def test_arm_disarm(system, mock_requests, mock_response):
    """Test arming and disarming."""
    # Connect first
    mock_response.json.return_value = {
        'resultCode': 0,
        'sessionId': 'test_session',
        'panelStatus': {'armedState': 0},
        'zones': [],
        'events': []
    }
    system.connect()
    mock_requests.reset_mock()
    
    # Test arm away
    assert system.arm('away')
    mock_requests.assert_any_call(
        f"{API_BASE}{API_ENDPOINTS['arm_panel']}",
        json={
            'locationId': '1234',
            'deviceId': '5678',
            'armType': ARM_MODES['away'],
            'sessionId': 'test_session'
        }
    )
    
    # Test arm stay
    assert system.arm('stay')
    mock_requests.assert_any_call(
        f"{API_BASE}{API_ENDPOINTS['arm_panel']}",
        json={
            'locationId': '1234',
            'deviceId': '5678',
            'armType': ARM_MODES['stay'],
            'sessionId': 'test_session'
        }
    )
    
    # Test invalid arm mode
    assert not system.arm('invalid')
    
    # Test disarm
    assert system.disarm('1234')
    mock_requests.assert_any_call(
        f"{API_BASE}{API_ENDPOINTS['disarm_panel']}",
        json={
            'locationId': '1234',
            'deviceId': '5678',
            'userCode': '1234',
            'sessionId': 'test_session'
        }
    )


def test_zone_operations(system, mock_requests, mock_response):
    """Test zone operations."""
    # Connect first
    mock_response.json.return_value = {
        'resultCode': 0,
        'sessionId': 'test_session',
        'panelStatus': {'armedState': 0},
        'zones': [],
        'events': []
    }
    system.connect()
    mock_requests.reset_mock()
    
    # Test bypass zone
    assert system.bypass_zone('1')
    mock_requests.assert_any_call(
        f"{API_BASE}{API_ENDPOINTS['bypass_zone']}",
        json={
            'locationId': '1234',
            'deviceId': '5678',
            'zoneId': '1',
            'sessionId': 'test_session'
        }
    )
    
    # Test unbypass zone
    assert system.unbypass_zone('1')
    mock_requests.assert_any_call(
        f"{API_BASE}{API_ENDPOINTS['clear_bypass']}",
        json={
            'locationId': '1234',
            'deviceId': '5678',
            'zoneId': '1',
            'sessionId': 'test_session'
        }
    )
    
    # Test trigger/clear alarm (not supported)
    assert not system.trigger_alarm('1', 'motion')
    assert not system.clear_alarm('1')


def test_state_update(system, mock_requests, mock_response):
    """Test state update handling."""
    # Connect first
    mock_response.json.return_value = {
        'resultCode': 0,
        'sessionId': 'test_session',
        'panelStatus': {
            'armedState': 1,
            'alarmState': 0,
            'zones': [
                {'id': '1', 'bypassed': True}
            ]
        },
        'zones': [
            {
                'id': '1',
                'name': 'Front Door',
                'type': 'contact',
                'faulted': False,
                'troubled': False,
                'bypassed': True,
                'alarmed': False,
                'partition': 1,
                'canBypass': True
            }
        ],
        'events': [
            {
                'type': 'arm',
                'time': time.time(),
                'zoneId': None,
                'partition': 1,
                'user': 'test_user',
                'message': 'System armed'
            }
        ]
    }
    system.connect()
    
    # Check state
    state = system.get_state()
    assert state.armed
    assert not state.triggered
    assert state.bypass_zones == ['1']
    
    # Check zone
    zone = system.get_zone('1')
    assert zone.zone_id == '1'
    assert zone.name == 'Front Door'
    assert zone.type == 'contact'
    assert zone.state == 'bypassed'
    assert zone.metadata['partition'] == 1
    assert zone.metadata['can_bypass']
    
    # Check events
    events = system.get_events()
    assert len(events) == 1
    assert events[0].type == 'arm'
    assert events[0].severity == 0.5


def test_keepalive(system, mock_requests, mock_response):
    """Test keepalive mechanism."""
    # Connect first
    mock_response.json.return_value = {
        'resultCode': 0,
        'sessionId': 'test_session',
        'panelStatus': {'armedState': 0},
        'zones': [],
        'events': []
    }
    system.connect()
    mock_requests.reset_mock()
    
    # Wait for keepalive
    time.sleep(2)
    mock_requests.assert_any_call(
        f"{API_BASE}{API_ENDPOINTS['keep_alive']}",
        json={'sessionId': 'test_session'}
    )
    
    # Test keepalive failure
    mock_response.json.return_value = {
        'resultCode': 1,
        'resultData': 'Session expired'
    }
    time.sleep(2)
    assert not system._connected
    
    # Test session timeout
    mock_response.json.return_value = {
        'resultCode': 0,
        'sessionId': 'new_session',
        'panelStatus': {'armedState': 0},
        'zones': [],
        'events': []
    }
    time.sleep(2)
    assert system._connected
    assert system._session_id == 'new_session'


def test_error_handling(system, mock_requests, mock_response):
    """Test error handling."""
    # Test connection error
    mock_requests.side_effect = requests.RequestException()
    assert not system.connect()
    assert not system._connected
    
    # Test authentication error
    mock_requests.side_effect = None
    mock_response.json.return_value = {
        'resultCode': 1,
        'resultData': 'Auth failed'
    }
    assert not system.connect()
    assert not system._connected
    
    # Test state update error
    mock_response.json.side_effect = [
        # Authentication success
        {
            'resultCode': 0,
            'sessionId': 'test_session'
        },
        # Status update failure
        {
            'resultCode': 1,
            'resultData': 'Error'
        }
    ]
    assert not system.connect()
    assert not system._connected
    
    # Test keepalive error
    mock_response.json.side_effect = None
    mock_response.json.return_value = {
        'resultCode': 0,
        'sessionId': 'test_session',
        'panelStatus': {'armedState': 0},
        'zones': [],
        'events': []
    }
    system.connect()
    mock_requests.side_effect = requests.RequestException()
    time.sleep(2)
    assert not system._connected


def test_event_severity(system):
    """Test event severity calculation."""
    events = [
        {'type': 'alarm', 'time': time.time()},
        {'type': 'panic', 'time': time.time()},
        {'type': 'fire', 'time': time.time()},
        {'type': 'trouble', 'time': time.time()},
        {'type': 'fault', 'time': time.time()},
        {'type': 'arm', 'time': time.time()},
        {'type': 'disarm', 'time': time.time()},
        {'type': 'bypass', 'time': time.time()},
        {'type': 'unknown', 'time': time.time()}
    ]
    
    system._update_events_from_status(events)
    events = system.get_events()
    
    # Check severities
    assert len(events) == 9
    assert events[0].severity == 1.0  # alarm
    assert events[1].severity == 1.0  # panic
    assert events[2].severity == 1.0  # fire
    assert events[3].severity == 0.8  # trouble
    assert events[4].severity == 0.8  # fault
    assert events[5].severity == 0.5  # arm
    assert events[6].severity == 0.5  # disarm
    assert events[7].severity == 0.5  # bypass
    assert events[8].severity == 0.5  # unknown
