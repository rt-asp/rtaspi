"""
test_local_devices.py
"""

import os
import json
import pytest
from unittest.mock import patch, MagicMock, call

from rtaspi.core.mcp import MCPBroker
from rtaspi.device_managers.local_devices import LocalDevicesManager
from rtaspi.device_managers.utils.device import LocalDevice

# Fixtures
@pytest.fixture
def config(tmp_path):
    """Test configuration with temporary directory."""
    return {
        'system': {
            'storage_path': str(tmp_path)
        },
        'local_devices': {
            'enable_video': True,
            'enable_audio': True,
            'auto_start': False,
            'scan_interval': 1,  # Short interval for tests
            'rtsp_port_start': 8554,
            'rtmp_port_start': 1935,
            'webrtc_port_start': 8080
        }
    }

@pytest.fixture
def mcp_broker():
    """MCP broker fixture."""
    return MCPBroker()

@pytest.fixture
def local_devices_manager(config, mcp_broker):
    """Local devices manager fixture."""
    with patch('rtaspi.device_managers.local_devices.RTSPServer'), \
            patch('rtaspi.device_managers.local_devices.RTMPServer'), \
            patch('rtaspi.device_managers.local_devices.WebRTCServer'):
        manager = LocalDevicesManager(config, mcp_broker)
        yield manager

@patch('rtaspi.device_managers.local_devices.LocalDevicesManager._scan_video_devices')
@patch('rtaspi.device_managers.local_devices.LocalDevicesManager._scan_audio_devices')
def test_scan_devices(mock_scan_audio, mock_scan_video, local_devices_manager):
    """Test device scanning."""
    # Call scan method
    local_devices_manager._scan_devices()

    # Check if scan methods were called
    mock_scan_video.assert_called_once()
    mock_scan_audio.assert_called_once()

@patch('subprocess.check_output')
def test_scan_linux_video_devices(mock_check_output, local_devices_manager):
    """Test scanning video devices on Linux."""
    # Simulate v4l2-ctl command output
    mock_check_output.side_effect = [
        # Output for --all
        'Card type       : Test Camera\nDriver name     : v4l2',
        # Output for --list-formats-ext
        'PixelFormat : \'YUYV\'\nSize: Discrete 640x480'
    ]

    with patch('platform.system', return_value='Linux'), \
            patch('pathlib.Path.glob', return_value=['/dev/video0']):
        local_devices_manager._scan_linux_video_devices()

    # Check if device was added
    assert len(local_devices_manager.devices['video']) == 1
    device_id = list(local_devices_manager.devices['video'].keys())[0]
    assert device_id == 'video:/dev/video0'
    assert local_devices_manager.devices['video'][device_id].name == 'Test Camera'
    assert local_devices_manager.devices['video'][device_id].formats == ['YUYV']
    assert local_devices_manager.devices['video'][device_id].resolutions == ['640x480']

@patch('subprocess.check_output')
def test_scan_linux_audio_devices(mock_check_output, local_devices_manager):
    """Test scanning audio devices on Linux."""
    # Simulate arecord and pactl command output
    mock_check_output.side_effect = [
        # Output for arecord -l
        'card 0: Test [Test Sound Card], device 0: Test PCM [Test PCM]\n',
        # Output for pactl list sources
        'Source #0\n  Name: test.monitor\n  Description: Test Monitor\n'
    ]

    with patch('platform.system', return_value='Linux'):
        local_devices_manager._scan_linux_audio_devices()

    # Check if devices were added
    assert len(local_devices_manager.devices['audio']) >= 2
    alsa_device = next((dev for dev in local_devices_manager.devices['audio'].values() if dev.driver == 'alsa'), None)
    pulse_device = next((dev for dev in local_devices_manager.devices['audio'].values() if dev.driver == 'pulse'), None)

    assert alsa_device is not None
    assert pulse_device is not None
    assert 'Sound Card' in alsa_device.name
    assert 'Test Monitor' in pulse_device.name

@patch('rtaspi.device_managers.local_devices.RTSPServer.start_stream')
def test_start_stream(mock_start_stream, local_devices_manager):
    """Test starting a stream."""
    # Create sample device
    device = LocalDevice(
        device_id='video:test',
        name='Test Camera',
        type='video',
        system_path='/dev/video0',
        driver='v4l2'
    )
    local_devices_manager.devices['video']['video:test'] = device

    # Simulate RTSP server response
    mock_start_stream.return_value = 'rtsp://localhost:8554/test'

    # Start stream
    url = local_devices_manager.start_stream('video:test', protocol='rtsp')

    # Check if stream was started
    assert url == 'rtsp://localhost:8554/test'
    mock_start_stream.assert_called_once()

def test_auto_start_streams(local_devices_manager):
    """Test automatic stream starting."""
    # Create sample devices
    device1 = LocalDevice(
        device_id='video:test1',
        name='Test Camera 1',
        type='video',
        system_path='/dev/video0',
        driver='v4l2'
    )
    device2 = LocalDevice(
        device_id='audio:test1',
        name='Test Mic 1',
        type='audio',
        system_path='hw:0,0',
        driver='alsa'
    )
    local_devices_manager.devices['video']['video:test1'] = device1
    local_devices_manager.devices['audio']['audio:test1'] = device2

    # Enable auto-start
    local_devices_manager.auto_start = True

    # Mock start_stream method
    local_devices_manager.start_stream = MagicMock(return_value='rtsp://localhost:8554/test')

    # Call auto_start_streams
    local_devices_manager._auto_start_streams()

    # Check if streams were started
    assert local_devices_manager.start_stream.call_count == 2
    local_devices_manager.start_stream.assert_has_calls([
        call('video:test1', protocol='rtsp'),
        call('audio:test1', protocol='rtsp')
    ], any_order=True)

def test_handle_command(local_devices_manager):
    """Test MCP command handling."""
    # Create sample device
    device = LocalDevice(
        device_id='video:test',
        name='Test Camera',
        type='video',
        system_path='/dev/video0',
        driver='v4l2'
    )
    local_devices_manager.devices['video']['video:test'] = device

    # Mock methods
    local_devices_manager._scan_devices = MagicMock()
    local_devices_manager.start_stream = MagicMock(return_value='rtsp://localhost:8554/test')
    local_devices_manager.stop_stream = MagicMock(return_value=True)
    local_devices_manager.mcp_client.publish = MagicMock()

    # Test scan command
    local_devices_manager._handle_command('command/local_devices/scan', {})
    local_devices_manager._scan_devices.assert_called_once()

    # Test start_stream command
    local_devices_manager._handle_command('command/local_devices/start_stream', {
        'device_id': 'video:test',
        'protocol': 'rtsp'
    })
    local_devices_manager.start_stream.assert_called_with('video:test', 'rtsp')

    # Test stop_stream command
    local_devices_manager._handle_command('command/local_devices/stop_stream', {
        'stream_id': 'test_stream'
    })
    local_devices_manager.stop_stream.assert_called_with('test_stream')

    # Test get_devices command
    local_devices_manager._handle_command('command/local_devices/get_devices', {})
    local_devices_manager.mcp_client.publish.assert_called()

def test_stop_stream(local_devices_manager):
    """Test stopping a stream."""
    # Create sample stream
    mock_process = MagicMock()
    local_devices_manager.streams['test_stream'] = {
        'process': mock_process,
        'device_id': 'video:test',
        'type': 'video',
        'url': 'rtsp://localhost:8554/test',
        'protocol': 'rtsp',
        'port': 8554
    }

    # Mock method
    local_devices_manager._publish_stream_stopped = MagicMock()

    # Stop stream
    result = local_devices_manager.stop_stream('test_stream')

    # Check if stream was stopped
    assert result is True
    mock_process.terminate.assert_called_once()
    local_devices_manager._publish_stream_stopped.assert_called_once()
    assert 'test_stream' not in local_devices_manager.streams
