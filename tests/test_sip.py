"""Tests for SIP implementation."""

import pytest
import threading
import time
from unittest.mock import Mock, patch, MagicMock

from rtaspi.device_managers.voip.sip import SIPDevice, SIPAccount, SIPCall


@pytest.fixture
def sip_config():
    """Create test SIP configuration."""
    return {
        'id': 'test-sip',
        'sip_domain': 'sip.test.com',
        'username': 'test_user',
        'password': 'test_pass',
        'proxy': 'sip:proxy.test.com',
        'port': 5060
    }


@pytest.fixture
def mock_pjsua():
    """Mock PJSUA2 library."""
    with patch('rtaspi.device_managers.voip.sip.pj') as mock_pj:
        # Mock endpoint
        mock_ep = Mock()
        mock_pj.Endpoint.return_value = mock_ep
        
        # Mock account config
        mock_pj.AccountConfig = Mock
        mock_pj.AuthCredInfo = Mock
        
        # Mock call states
        mock_pj.PJSIP_INV_STATE_CONFIRMED = 1
        mock_pj.PJSUA_INVALID_ID = -1
        mock_pj.PJMEDIA_TYPE_AUDIO = 0
        mock_pj.PJSUA_CALL_MEDIA_ACTIVE = 1
        
        yield mock_pj


@pytest.fixture
def device(sip_config, mock_pjsua):
    """Create test SIP device."""
    device = SIPDevice('test-sip', sip_config)
    device.initialize()
    yield device
    device.cleanup()


def test_device_init(sip_config):
    """Test device initialization."""
    device = SIPDevice('test-sip', sip_config)
    
    # Check initial state
    assert device.device_id == 'test-sip'
    assert device.sip_domain == 'sip.test.com'
    assert device.username == 'test_user'
    assert device.password == 'test_pass'
    assert device.proxy == 'sip:proxy.test.com'
    assert device.port == 5060
    assert not device._initialized
    assert not device._registered


def test_device_initialization(device, mock_pjsua):
    """Test device initialization process."""
    # Verify endpoint initialization
    mock_pjsua.Endpoint.return_value.libCreate.assert_called_once()
    mock_pjsua.Endpoint.return_value.libInit.assert_called_once()
    mock_pjsua.Endpoint.return_value.transportCreate.assert_called_once()
    mock_pjsua.Endpoint.return_value.libStart.assert_called_once()
    
    # Verify account creation
    assert device._initialized
    assert device._ep is not None
    assert device._account is not None


def test_device_cleanup(device, mock_pjsua):
    """Test device cleanup."""
    # Mock current call
    device._current_call = Mock()
    
    # Clean up
    device.cleanup()
    
    # Verify cleanup
    device._current_call.hangup.assert_called_once()
    device._account.delete.assert_called_once()
    device._ep.libDestroy.assert_called_once()
    assert not device._initialized
    assert not device._registered


def test_make_call(device):
    """Test making outgoing call."""
    # Set registered state
    device._registered = True
    
    # Mock call creation
    mock_call = Mock()
    device._account.create = Mock(return_value=mock_call)
    
    # Make call
    assert device.make_call('sip:test@test.com')
    assert device._current_call is not None
    
    # Test making call while in call
    assert not device.make_call('sip:another@test.com')
    
    # Test making call when not registered
    device._registered = False
    assert not device.make_call('sip:test@test.com')


def test_hangup(device):
    """Test call hangup."""
    # Mock current call
    mock_call = Mock()
    device._current_call = mock_call
    
    # Hang up
    device.hangup()
    mock_call.hangup.assert_called_once()
    assert device._current_call is None
    
    # Test hangup without call
    device.hangup()  # Should not raise


def test_send_audio(device):
    """Test audio transmission."""
    # Mock current call
    mock_call = Mock()
    device._current_call = mock_call
    
    # Send audio
    test_audio = b'test audio data'
    device.send_audio(test_audio)
    mock_call.sendAudio.assert_called_once_with(test_audio)
    
    # Test sending without call
    device._current_call = None
    device.send_audio(test_audio)  # Should not raise


def test_account_callbacks():
    """Test SIP account callbacks."""
    # Create account with mock callback
    callback = Mock()
    account = SIPAccount(callback)
    
    # Test registration state callback
    reg_info = Mock()
    reg_info.code = 200
    reg_info.reason = "OK"
    account.onRegState(reg_info)
    callback.assert_called_with('reg_state', reg_info)
    
    # Test incoming call callback
    call_info = Mock()
    call_info.callId = "test_call"
    account.onIncomingCall(call_info)
    callback.assert_called_with('incoming_call', call_info)


def test_call_callbacks():
    """Test SIP call callbacks."""
    # Create call
    mock_account = Mock()
    call = SIPCall(mock_account)
    
    # Test call state callback
    call_info = Mock()
    call_info.state = 1  # PJSIP_INV_STATE_CONFIRMED
    call_info.stateText = "CONFIRMED"
    call.getInfo = Mock(return_value=call_info)
    
    call.onCallState(Mock())
    assert call._connected
    
    # Test media state callback
    media_info = Mock()
    media_info.type = 0  # PJMEDIA_TYPE_AUDIO
    media_info.status = 1  # PJSUA_CALL_MEDIA_ACTIVE
    call_info.media = [media_info]
    
    with patch.object(call, '_setupAudio') as mock_setup:
        call.onCallMediaState(Mock())
        mock_setup.assert_called_once()


def test_account_event_handling(device):
    """Test account event handling."""
    # Test registration state
    device._handle_account_event('reg_state', Mock(code=200))
    assert device._registered
    
    device._handle_account_event('reg_state', Mock(code=403))
    assert not device._registered
    
    # Test incoming call
    call_data = Mock()
    device._handle_account_event('incoming_call', call_data)
    assert device._current_call is not None
    
    # Test unknown event
    device._handle_account_event('unknown', None)  # Should not raise


def test_device_status(device, sip_config):
    """Test device status reporting."""
    # Set test state
    device._registered = True
    device._current_call = Mock()
    
    # Get status
    status = device.get_status()
    assert status['id'] == sip_config['id']
    assert status['initialized']
    assert status['registered']
    assert status['in_call']
    assert status['sip_domain'] == sip_config['sip_domain']
    assert status['username'] == sip_config['username']
    assert status['proxy'] == sip_config['proxy']
    assert status['port'] == sip_config['port']


def test_error_handling(device, mock_pjsua):
    """Test error handling."""
    # Test initialization error
    mock_pjsua.Endpoint.return_value.libCreate.side_effect = Exception("Test error")
    assert not device.initialize()
    assert not device._initialized
    
    # Test call error
    device._registered = True
    mock_pjsua.Call.makeCall.side_effect = Exception("Test error")
    assert not device.make_call('sip:test@test.com')
    
    # Test hangup error
    device._current_call = Mock()
    device._current_call.hangup.side_effect = Exception("Test error")
    device.hangup()  # Should log error but not raise
    
    # Test cleanup error
    device._ep.libDestroy.side_effect = Exception("Test error")
    device.cleanup()  # Should log error but not raise
