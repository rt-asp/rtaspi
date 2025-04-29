import pytest
from unittest.mock import MagicMock, patch

from rtaspi.streaming.rtsp import RTSPServer
from rtaspi.streaming.rtmp import RTMPServer
from rtaspi.streaming.webrtc import WebRTCServer
from rtaspi.device_managers.utils.device import Device

@pytest.fixture
def rtsp_server():
    return RTSPServer(port=8554)

@pytest.fixture
def rtmp_server():
    return RTMPServer(port=1935)

@pytest.fixture
def webrtc_server():
    return WebRTCServer(port=8080)

@pytest.fixture
def mock_device():
    return Device(
        id="test_camera",
        name="Test Camera",
        type="ip_camera",
        status="online",
        capabilities=["video", "audio"],
        network_info={
            "ip": "192.168.1.100",
            "port": 554,
            "protocol": "RTSP"
        }
    )

def test_rtsp_server_initialization(rtsp_server):
    assert isinstance(rtsp_server, RTSPServer)
    assert rtsp_server.port == 8554
    assert not rtsp_server.is_running

@pytest.mark.asyncio
async def test_rtsp_server_start_stop(rtsp_server):
    with patch.object(rtsp_server, '_start_server') as mock_start:
        mock_start.return_value = True
        success = await rtsp_server.start()
        assert success
        assert rtsp_server.is_running
        mock_start.assert_called_once()

    with patch.object(rtsp_server, '_stop_server') as mock_stop:
        mock_stop.return_value = True
        success = await rtsp_server.stop()
        assert success
        assert not rtsp_server.is_running
        mock_stop.assert_called_once()

def test_rtmp_server_initialization(rtmp_server):
    assert isinstance(rtmp_server, RTMPServer)
    assert rtmp_server.port == 1935
    assert not rtmp_server.is_running

@pytest.mark.asyncio
async def test_rtmp_server_start_stop(rtmp_server):
    with patch.object(rtmp_server, '_start_server') as mock_start:
        mock_start.return_value = True
        success = await rtmp_server.start()
        assert success
        assert rtmp_server.is_running
        mock_start.assert_called_once()

    with patch.object(rtmp_server, '_stop_server') as mock_stop:
        mock_stop.return_value = True
        success = await rtmp_server.stop()
        assert success
        assert not rtmp_server.is_running
        mock_stop.assert_called_once()

def test_webrtc_server_initialization(webrtc_server):
    assert isinstance(webrtc_server, WebRTCServer)
    assert webrtc_server.port == 8080
    assert not webrtc_server.is_running

@pytest.mark.asyncio
async def test_webrtc_server_start_stop(webrtc_server):
    with patch.object(webrtc_server, '_start_server') as mock_start:
        mock_start.return_value = True
        success = await webrtc_server.start()
        assert success
        assert webrtc_server.is_running
        mock_start.assert_called_once()

    with patch.object(webrtc_server, '_stop_server') as mock_stop:
        mock_stop.return_value = True
        success = await webrtc_server.stop()
        assert success
        assert not webrtc_server.is_running
        mock_stop.assert_called_once()

@pytest.mark.asyncio
async def test_stream_device(rtsp_server, mock_device):
    # Test starting stream
    with patch.object(rtsp_server, '_start_device_stream') as mock_start_stream:
        mock_start_stream.return_value = "rtsp://localhost:8554/test_camera"
        
        stream_url = await rtsp_server.start_stream(mock_device)
        
        assert stream_url == "rtsp://localhost:8554/test_camera"
        mock_start_stream.assert_called_once_with(mock_device)
        
    # Test stopping stream
    with patch.object(rtsp_server, '_stop_device_stream') as mock_stop_stream:
        mock_stop_stream.return_value = True
        
        success = await rtsp_server.stop_stream(mock_device)
        
        assert success
        mock_stop_stream.assert_called_once_with(mock_device)
