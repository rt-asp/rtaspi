import pytest
from unittest.mock import MagicMock, patch

from rtaspi.streaming.rtsp import RTSPServer
from rtaspi.device_managers.utils.device import LocalDevice, NetworkDevice

@pytest.fixture
def config():
    return {
        'streaming': {
            'rtsp': {
                'port_start': 8554
            }
        },
        'system': {
            'storage_path': '/tmp'
        }
    }

@pytest.fixture
def rtsp_server(config):
    return RTSPServer(config)

@pytest.fixture
def local_device():
    return LocalDevice(
        device_id="test_video",
        name="Test Camera",
        type="video",
        system_path="/dev/video0",
        driver="v4l2"
    )

@pytest.fixture
def network_device():
    return NetworkDevice(
        device_id="test_ip_camera",
        name="Test IP Camera",
        type="video",
        ip="192.168.1.100",
        port=554,
        protocol="rtsp"
    )

def test_rtsp_server_initialization(rtsp_server, config):
    assert isinstance(rtsp_server, RTSPServer)
    assert rtsp_server.port_start == config['streaming']['rtsp']['port_start']
    assert rtsp_server.storage_path == config['system']['storage_path']

@pytest.mark.asyncio
async def test_start_stream_local_device(rtsp_server, local_device):
    # Mock subprocess and socket
    with patch('subprocess.Popen') as mock_popen, \
         patch('socket.socket') as mock_socket, \
         patch('platform.system', return_value='Linux'):
        
        # Configure mock socket to indicate port is free
        mock_socket_instance = MagicMock()
        mock_socket_instance.connect_ex.return_value = 1  # Port is free
        mock_socket.return_value = mock_socket_instance
        
        # Configure mock process
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process is running
        mock_popen.return_value = mock_process
        
        # Start stream
        stream_url = rtsp_server.start_stream(
            device=local_device,
            stream_id="test_stream",
            output_dir="/tmp/streams"
        )
        
        # Verify stream was started
        assert stream_url is not None
        assert stream_url.startswith("rtsp://localhost:")
        assert "/test_stream" in stream_url
        
        # Verify FFmpeg was called with correct arguments
        mock_popen.assert_called_once()
        args = mock_popen.call_args[0][0]
        assert args[0] == 'ffmpeg'
        assert '-f' in args
        assert 'v4l2' in args
        assert '-i' in args
        assert '/dev/video0' in args
        assert 'rtsp://localhost' in args[-1]

@pytest.mark.asyncio
async def test_proxy_stream_network_device(rtsp_server, network_device):
    # Mock subprocess and socket
    with patch('subprocess.Popen') as mock_popen, \
         patch('socket.socket') as mock_socket:
        
        # Configure mock socket to indicate port is free
        mock_socket_instance = MagicMock()
        mock_socket_instance.connect_ex.return_value = 1  # Port is free
        mock_socket.return_value = mock_socket_instance
        
        # Configure mock process
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process is running
        mock_popen.return_value = mock_process
        
        # Start proxy stream
        source_url = "rtsp://192.168.1.100:554/stream1"
        stream_url = rtsp_server.proxy_stream(
            device=network_device,
            stream_id="test_proxy",
            source_url=source_url,
            output_dir="/tmp/streams"
        )
        
        # Verify stream was started
        assert stream_url is not None
        assert stream_url.startswith("rtsp://localhost:")
        assert "/test_proxy" in stream_url
        
        # Verify FFmpeg was called with correct arguments
        mock_popen.assert_called_once()
        args = mock_popen.call_args[0][0]
        assert args[0] == 'ffmpeg'
        assert '-rtsp_transport' in args
        assert 'tcp' in args
        assert '-i' in args
        assert source_url in args
        assert 'rtsp://localhost' in args[-1]

def test_find_free_port(rtsp_server):
    # Mock socket to simulate ports 8554-8556 being used and 8557 being free
    with patch('socket.socket') as mock_socket:
        mock_socket_instance = MagicMock()
        mock_socket_instance.connect_ex.side_effect = [0, 0, 0, 1]  # First 3 ports used, 4th free
        mock_socket.return_value = mock_socket_instance
        
        port = rtsp_server._find_free_port(8554)
        
        assert port == 8557
        assert mock_socket_instance.connect_ex.call_count == 4

def test_prepare_output_args(rtsp_server, local_device):
    # Test video device
    local_device.type = 'video'
    args = rtsp_server._prepare_output_args(local_device, 8554, "test_stream")
    assert args is not None
    assert '-c:v' in args
    assert 'libx264' in args
    assert 'rtsp://localhost:8554/test_stream' in args
    
    # Test audio device
    local_device.type = 'audio'
    args = rtsp_server._prepare_output_args(local_device, 8554, "test_stream")
    assert args is not None
    assert '-c:a' in args
    assert 'aac' in args
    assert 'rtsp://localhost:8554/test_stream' in args
