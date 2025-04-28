"""
test_streaming.py
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from rtaspi.streaming.rtsp import RTSPServer
from rtaspi.streaming.rtmp import RTMPServer
from rtaspi.streaming.webrtc import WebRTCServer
from rtaspi.device_managers.utils.device import LocalDevice, NetworkDevice

# Common fixtures
@pytest.fixture
def config(tmp_path):
    """Test configuration with temporary directory."""
    return {
        'system': {
            'storage_path': str(tmp_path)
        },
        'streaming': {
            'rtsp': {
                'port_start': 8554
            },
            'rtmp': {
                'port_start': 1935
            },
            'webrtc': {
                'port_start': 8080,
                'stun_server': 'stun://stun.l.google.com:19302',
                'turn_server': '',
                'turn_username': '',
                'turn_password': ''
            }
        }
    }

@pytest.fixture
def rtsp_server(config):
    """RTSP server fixture."""
    return RTSPServer(config)

@pytest.fixture
def rtmp_server(config):
    """RTMP server fixture."""
    return RTMPServer(config)

@pytest.fixture
def webrtc_server(config):
    """WebRTC server fixture."""
    return WebRTCServer(config)

# RTSP Tests
@patch('subprocess.Popen')
@patch('time.sleep')
@patch('socket.socket')
def test_rtsp_start_stream_local_device(mock_socket, mock_sleep, mock_popen, rtsp_server, tmp_path):
    """Test starting RTSP stream from local device."""
    # Simulate free port
    mock_socket_instance = MagicMock()
    mock_socket.return_value = mock_socket_instance
    mock_socket_instance.connect_ex.return_value = 1  # Port is free

    # Simulate FFmpeg process
    mock_process = MagicMock()
    mock_popen.return_value = mock_process
    mock_process.poll.return_value = None  # Process is running

    # Create sample device
    device = LocalDevice(
        device_id='video:test',
        name='Test Camera',
        type='video',
        system_path='/dev/video0',
        driver='v4l2'
    )

    # Mock methods
    with patch('platform.system', return_value='Linux'):
        # Start stream
        url = rtsp_server.start_stream(device, 'test_stream', str(tmp_path))

        # Check if stream was started
        assert url is not None
        assert url.startswith('rtsp://localhost:')
        mock_popen.assert_called_once()

@patch('subprocess.Popen')
@patch('time.sleep')
@patch('socket.socket')
def test_rtsp_proxy_stream_network_device(mock_socket, mock_sleep, mock_popen, rtsp_server, tmp_path):
    """Test starting RTSP proxy for remote device."""
    # Simulate free port
    mock_socket_instance = MagicMock()
    mock_socket.return_value = mock_socket_instance
    mock_socket_instance.connect_ex.return_value = 1  # Port is free

    # Simulate FFmpeg process
    mock_process = MagicMock()
    mock_popen.return_value = mock_process
    mock_process.poll.return_value = None  # Process is running

    # Create sample device
    device = NetworkDevice(
        device_id='network:test',
        name='Test IP Camera',
        type='video',
        ip='192.168.1.100',
        port=554,
        protocol='rtsp'
    )

    # Create source URL
    source_url = 'rtsp://192.168.1.100:554/stream1'

    # Start proxy stream
    url = rtsp_server.proxy_stream(device, 'test_stream', source_url, str(tmp_path), transcode=True)

    # Check if proxy was started
    assert url is not None
    assert url.startswith('rtsp://localhost:')
    mock_popen.assert_called_once()

def test_rtsp_prepare_input_args(rtsp_server):
    """Test preparing input arguments for FFmpeg."""
    # Test devices
    video_device = LocalDevice(
        device_id='video:test',
        name='Test Camera',
        type='video',
        system_path='/dev/video0',
        driver='v4l2'
    )

    audio_device = LocalDevice(
        device_id='audio:test',
        name='Test Microphone',
        type='audio',
        system_path='hw:0,0',
        driver='alsa'
    )

    # Test for different platforms
    with patch('platform.system', return_value='Linux'):
        # Video - Linux
        args = rtsp_server._prepare_input_args(video_device)
        assert args == ['-f', 'v4l2', '-i', '/dev/video0']

        # Audio - Linux
        args = rtsp_server._prepare_input_args(audio_device)
        assert args == ['-f', 'alsa', '-i', 'hw:0,0']

    with patch('platform.system', return_value='Darwin'):
        # Video - macOS
        video_device.driver = 'avfoundation'
        args = rtsp_server._prepare_input_args(video_device)
        assert args == ['-f', 'avfoundation', '-framerate', '30', '-i', '/dev/video0:none']

    with patch('platform.system', return_value='Windows'):
        # Video - Windows
        video_device.driver = 'dshow'
        args = rtsp_server._prepare_input_args(video_device)
        assert args == ['-f', 'dshow', '-i', 'video=/dev/video0']

def test_rtsp_prepare_output_args(rtsp_server):
    """Test preparing output arguments for FFmpeg."""
    # Test devices
    video_device = LocalDevice(
        device_id='video:test',
        name='Test Camera',
        type='video',
        system_path='/dev/video0',
        driver='v4l2'
    )

    audio_device = LocalDevice(
        device_id='audio:test',
        name='Test Microphone',
        type='audio',
        system_path='hw:0,0',
        driver='alsa'
    )

    # Test for different device types
    # Video
    args = rtsp_server._prepare_output_args(video_device, 8554, 'test_stream')
    assert args == [
        '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'zerolatency',
        '-f', 'rtsp', 'rtsp://localhost:8554/test_stream'
    ]

    # Audio
    args = rtsp_server._prepare_output_args(audio_device, 8554, 'test_stream')
    assert args == [
        '-c:a', 'aac', '-b:a', '128k',
        '-f', 'rtsp', 'rtsp://localhost:8554/test_stream'
    ]

# RTMP Tests
@patch('subprocess.Popen')
@patch('time.sleep')
@patch('socket.socket')
def test_rtmp_start_stream_local_device(mock_socket, mock_sleep, mock_popen, rtmp_server, tmp_path):
    """Test starting RTMP stream from local device."""
    # Simulate free port
    mock_socket_instance = MagicMock()
    mock_socket.return_value = mock_socket_instance
    mock_socket_instance.connect_ex.return_value = 1  # Port is free

    # Simulate processes
    mock_popen.side_effect = [MagicMock(), MagicMock()]  # nginx, ffmpeg

    # Create sample device
    device = LocalDevice(
        device_id='video:test',
        name='Test Camera',
        type='video',
        system_path='/dev/video0',
        driver='v4l2'
    )

    # Mock methods
    with patch('platform.system', return_value='Linux'), \
            patch('builtins.open', MagicMock()):
        # Start stream
        url = rtmp_server.start_stream(device, 'test_stream', str(tmp_path))

        # Check if stream was started
        assert url is not None
        assert url.startswith('rtmp://localhost:')
        assert mock_popen.call_count == 2

def test_rtmp_generate_nginx_config(rtmp_server):
    """Test generating NGINX configuration."""
    # Generate configuration
    config = rtmp_server._generate_nginx_config(1935)

    # Check if configuration contains required elements
    assert 'worker_processes 1;' in config
    assert 'listen 1935;' in config
    assert 'application live' in config
    assert 'live on;' in config

# WebRTC Tests
@patch('subprocess.Popen')
@patch('time.sleep')
@patch('socket.socket')
def test_webrtc_start_stream_local_device(mock_socket, mock_sleep, mock_popen, webrtc_server, tmp_path):
    """Test starting WebRTC stream from local device."""
    # Simulate free port
    mock_socket_instance = MagicMock()
    mock_socket.return_value = mock_socket_instance
    mock_socket_instance.connect_ex.return_value = 1  # Port is free

    # Simulate processes
    mock_popen.side_effect = [MagicMock(), MagicMock()]  # http server, gstreamer

    # Create sample device
    device = LocalDevice(
        device_id='video:test',
        name='Test Camera',
        type='video',
        system_path='/dev/video0',
        driver='v4l2'
    )

    # Mock methods
    with patch('platform.system', return_value='Linux'), \
            patch('builtins.open', MagicMock()), \
            patch('json.dump', MagicMock()):
        # Start stream
        url = webrtc_server.start_stream(device, 'test_stream', str(tmp_path))

        # Check if stream was started
        assert url is not None
        assert url.startswith('http://localhost:')
        assert mock_popen.call_count == 2

def test_webrtc_prepare_input_pipeline(webrtc_server):
    """Test preparing input pipeline for GStreamer."""
    # Test devices
    video_device = LocalDevice(
        device_id='video:test',
        name='Test Camera',
        type='video',
        system_path='/dev/video0',
        driver='v4l2'
    )

    audio_device = LocalDevice(
        device_id='audio:test',
        name='Test Microphone',
        type='audio',
        system_path='hw:0,0',
        driver='alsa'
    )

    # Test for different platforms
    with patch('platform.system', return_value='Linux'):
        # Video - Linux
        pipeline = webrtc_server._prepare_input_pipeline(video_device)
        assert 'v4l2src device=/dev/video0' in pipeline

        # Audio - Linux
        pipeline = webrtc_server._prepare_input_pipeline(audio_device)
        assert 'alsasrc device=hw:0,0' in pipeline

def test_webrtc_generate_webrtc_html(webrtc_server):
    """Test generating HTML code for WebRTC."""
    # Generate HTML
    html = webrtc_server._generate_webrtc_html('test_stream', 8080)

    # Check if HTML contains required elements
    assert '<!DOCTYPE html>' in html
    assert 'test_stream' in html
    assert '8080' in html
    assert 'stun.l.google.com:19302' in html
    assert 'RTCPeerConnection' in html
    assert 'createOffer' in html
