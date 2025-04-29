"""Tests for DSC alarm system integration."""

import pytest
import socket
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import threading
import time

from rtaspi.security.alarms.dsc import DSCAlarmSystem
from rtaspi.security.alarms.base import AlarmState, AlarmZone, AlarmEvent


@pytest.fixture
def dsc_config():
    """Create test DSC configuration."""
    return {
        'system_id': 'test_system',
        'name': 'Test DSC',
        'host': 'localhost',
        'port': 4025,
        'password': 'test_pass',
        'user_code': '1234',
        'partition': 1,
        'socket_timeout': 1,
        'keepalive_interval': 1
    }


@pytest.fixture
def mock_socket():
    """Mock socket."""
    with patch('socket.socket') as mock:
        socket = MagicMock()
        mock.return_value = socket
        yield socket


@pytest.fixture
def system(dsc_config, mock_socket):
    """Create test DSC system."""
    system = DSCAlarmSystem(dsc_config)
    yield system
    system.disconnect()


def test_system_init(dsc_config):
    """Test system initialization."""
    system = DSCAlarmSystem(dsc_config)
    
    # Check configuration
    assert system.system_id == 'test_system'
    assert system.name == 'Test DSC'
    assert system.host == 'localhost'
    assert system.port == 4025
    assert system.password == 'test_pass'
    assert system.user_code == '1234'
    assert system.partition == 1
    assert system.socket_timeout == 1
    assert system.keepalive_interval == 1
    
    # Check state
    assert not system._connected
    assert not system._socket
    assert not system._reader_thread
    assert not system._keepalive_thread
    assert system._stop_threads.is_set()


def test_connection(system, mock_socket):
    """Test connection handling."""
    # Mock successful connection
    mock_socket.recv.return_value = b'500\r\n'  # Command acknowledge
    
    # Connect
    assert system.connect()
    assert system._connected
    assert system._socket == mock_socket
    assert system._reader_thread and system._reader_thread.is_alive()
    assert system._keepalive_thread and system._keepalive_thread.is_alive()
    
    # Check login and status request
    expected_calls = [
        b'005test_pass2A\r\n',  # Login
        b'00149\r\n'  # Status request
    ]
    mock_socket.send.assert_any_call(expected_calls[0])
    mock_socket.send.assert_any_call(expected_calls[1])
    
    # Disconnect
    system.disconnect()
    assert not system._connected
    assert not system._socket
    assert not system._reader_thread
    assert not system._keepalive_thread
    assert system._stop_threads.is_set()


def test_arm_disarm(system, mock_socket):
    """Test arming and disarming."""
    # Connect
    mock_socket.recv.return_value = b'500\r\n'
    system.connect()
    
    # Test arm away
    mock_socket.send.reset_mock()
    assert system.arm('away')
    mock_socket.send.assert_called_with(b'0301B1\r\n')
    
    # Test arm stay
    mock_socket.send.reset_mock()
    assert system.arm('stay')
    mock_socket.send.assert_called_with(b'0311B2\r\n')
    
    # Test arm night
    mock_socket.send.reset_mock()
    assert system.arm('night')
    mock_socket.send.assert_called_with(b'0321B3\r\n')
    
    # Test invalid arm mode
    mock_socket.send.reset_mock()
    assert not system.arm('invalid')
    mock_socket.send.assert_not_called()
    
    # Test disarm
    mock_socket.send.reset_mock()
    assert system.disarm()
    mock_socket.send.assert_called_with(b'040112344D\r\n')
    
    # Test disarm with code
    mock_socket.send.reset_mock()
    assert system.disarm('5678')
    mock_socket.send.assert_called_with(b'040156784D\r\n')


def test_zone_operations(system, mock_socket):
    """Test zone operations."""
    # Connect
    mock_socket.recv.return_value = b'500\r\n'
    system.connect()
    
    # Test bypass zone
    mock_socket.send.reset_mock()
    assert system.bypass_zone('1')
    mock_socket.send.assert_called_with(b'07112340014E\r\n')
    
    # Test unbypass zone
    mock_socket.send.reset_mock()
    assert system.unbypass_zone('1')
    mock_socket.send.assert_called_with(b'07212340014F\r\n')
    
    # Test trigger alarm
    mock_socket.send.reset_mock()
    assert system.trigger_alarm('1', 'motion')
    mock_socket.send.assert_called_with(b'60100150\r\n')
    
    # Test clear alarm
    mock_socket.send.reset_mock()
    assert system.clear_alarm('1')
    mock_socket.send.assert_called_with(b'60200151\r\n')


def test_message_handling(system, mock_socket):
    """Test message handling."""
    # Connect
    mock_socket.recv.return_value = b'500\r\n'
    system.connect()
    
    # Mock event callback
    callback = Mock()
    system.add_event_callback(callback)
    
    # Test zone alarm
    system._handle_message('601001A2')  # Zone 1 alarm
    assert system.get_zone('1').state == 'triggered'
    callback.assert_called()
    event = callback.call_args[0][0]
    assert event.type == 'zone_alarm'
    assert event.zone_id == '1'
    assert event.severity == 1.0
    
    # Test zone restore
    callback.reset_mock()
    system._handle_message('602001A3')  # Zone 1 restore
    assert system.get_zone('1').state == 'normal'
    callback.assert_called()
    event = callback.call_args[0][0]
    assert event.type == 'zone_alarm_restore'
    assert event.zone_id == '1'
    assert event.severity == 0.5
    
    # Test partition armed
    callback.reset_mock()
    system._handle_message('6521B4')  # Partition 1 armed
    assert system.get_state().armed
    assert not system.get_state().triggered
    callback.assert_called()
    event = callback.call_args[0][0]
    assert event.type == 'armed'
    assert event.details['partition'] == 1
    
    # Test partition in alarm
    callback.reset_mock()
    system._handle_message('6541B6')  # Partition 1 in alarm
    assert system.get_state().armed
    assert system.get_state().triggered
    callback.assert_called()
    event = callback.call_args[0][0]
    assert event.type == 'alarm'
    assert event.details['partition'] == 1
    
    # Test partition disarmed
    callback.reset_mock()
    system._handle_message('6551B7')  # Partition 1 disarmed
    assert not system.get_state().armed
    assert not system.get_state().triggered
    callback.assert_called()
    event = callback.call_args[0][0]
    assert event.type == 'disarmed'
    assert event.details['partition'] == 1


def test_error_handling(system, mock_socket):
    """Test error handling."""
    # Test connection error
    mock_socket.connect.side_effect = socket.error()
    assert not system.connect()
    assert not system._connected
    
    # Test send error
    mock_socket.connect.side_effect = None
    mock_socket.recv.return_value = b'500\r\n'
    system.connect()
    mock_socket.send.side_effect = socket.error()
    assert not system._send_command('test')
    
    # Test receive error
    mock_socket.recv.side_effect = socket.error()
    time.sleep(2)  # Wait for reader thread to detect error
    assert not system._connected
    
    # Test invalid checksum
    mock_socket.recv.side_effect = None
    mock_socket.recv.return_value = b'601001FF\r\n'  # Wrong checksum
    system._handle_message('601001FF')  # Should not raise or update state
    assert not system.get_zones()
    
    # Test invalid message format
    system._handle_message('invalid')  # Should not raise
    assert not system.get_zones()


def test_reconnection(system, mock_socket):
    """Test automatic reconnection."""
    # Connect initially
    mock_socket.recv.return_value = b'500\r\n'
    system.connect()
    assert system._connected
    
    # Simulate connection loss
    mock_socket.recv.side_effect = socket.error()
    time.sleep(2)  # Wait for reader thread to detect error
    assert not system._connected
    
    # Reset mock and simulate successful reconnection
    mock_socket.recv.side_effect = None
    mock_socket.recv.return_value = b'500\r\n'
    time.sleep(2)  # Wait for reconnect attempt
    assert system._connected


def test_keepalive(system, mock_socket):
    """Test keepalive mechanism."""
    # Connect
    mock_socket.recv.return_value = b'500\r\n'
    system.connect()
    
    # Wait for keepalive
    time.sleep(2)
    mock_socket.send.assert_any_call(b'00048\r\n')  # Poll command


def test_state_callbacks(system):
    """Test state change callbacks."""
    # Add callback
    callback = Mock()
    system.add_state_callback(callback)
    
    # Update state
    new_state = AlarmState(
        armed=True,
        triggered=False,
        bypass_zones=[],
        last_event=None,
        last_update=datetime.now()
    )
    system._update_state(new_state)
    callback.assert_called_with(new_state)
    
    # Remove callback
    callback.reset_mock()
    system.remove_state_callback(callback)
    system._update_state(new_state)
    callback.assert_not_called()


def test_event_history(system):
    """Test event history management."""
    # Add events
    events = []
    for i in range(system.event_history_size + 10):
        event = AlarmEvent(
            timestamp=datetime.now(),
            type='test',
            zone_id=str(i),
            details=None,
            severity=0.5
        )
        system._add_event(event)
        events.append(event)
    
    # Check history size
    assert len(system.get_events()) == system.event_history_size
    assert system.get_events()[-1] == events[-1]  # Most recent event
    
    # Check count parameter
    assert len(system.get_events(10)) == 10
    assert system.get_events(10)[-1] == events[-1]


def test_status(system, mock_socket):
    """Test status reporting."""
    # Connect
    mock_socket.recv.return_value = b'500\r\n'
    system.connect()
    
    # Add some test data
    system._update_state(AlarmState(
        armed=True,
        triggered=False,
        bypass_zones=['1'],
        last_event=None,
        last_update=datetime.now()
    ))
    system._update_zone(AlarmZone(
        zone_id='1',
        name='Test Zone',
        type='security',
        state='normal',
        last_trigger=None,
        metadata=None
    ))
    system._add_event(AlarmEvent(
        timestamp=datetime.now(),
        type='test',
        zone_id='1',
        details=None,
        severity=0.5
    ))
    
    # Check status
    status = system.get_status()
    assert status['system_id'] == 'test_system'
    assert status['name'] == 'Test DSC'
    assert status['connected']
    assert status['armed']
    assert not status['triggered']
    assert status['bypass_zones'] == ['1']
    assert status['zone_count'] == 1
    assert status['event_count'] == 1
