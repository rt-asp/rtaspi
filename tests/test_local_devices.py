import pytest
from unittest.mock import MagicMock, patch

from rtaspi.core.mcp import MCPBroker
from rtaspi.device_managers.local_devices import LocalDevicesManager
from rtaspi.device_managers.utils.device import LocalDevice

@pytest.fixture
def mcp_broker():
    return MagicMock(spec=MCPBroker)

@pytest.fixture
def config():
    return {
        'local_devices': {
            'enable_video': True,
            'enable_audio': True,
            'auto_start': False,
            'scan_interval': 60,
            'rtsp_port_start': 8554,
            'rtmp_port_start': 1935,
            'webrtc_port_start': 8080
        }
    }

@pytest.fixture
def local_manager(config, mcp_broker):
    return LocalDevicesManager(config, mcp_broker)

def test_local_manager_initialization(local_manager, config):
    assert isinstance(local_manager, LocalDevicesManager)
    assert hasattr(local_manager, 'mcp_broker')
    assert hasattr(local_manager, 'devices')
    assert isinstance(local_manager.devices, dict)
    assert 'video' in local_manager.devices
    assert 'audio' in local_manager.devices
    assert local_manager.enable_video == config['local_devices']['enable_video']
    assert local_manager.enable_audio == config['local_devices']['enable_audio']
    assert local_manager.auto_start == config['local_devices']['auto_start']
    assert local_manager.scan_interval == config['local_devices']['scan_interval']

@pytest.mark.asyncio
async def test_scan_devices(local_manager):
    # Mock platform to return 'linux'
    with patch('platform.system', return_value='Linux'):
        # Mock subprocess calls
        mock_v4l2_output = '''Card type      : Test Camera
PixelFormat : 'YUYV'
Size: Discrete 640x480'''
        
        with patch('subprocess.check_output', return_value=mock_v4l2_output):
            # Call _scan_devices which internally calls _scan_video_devices
            local_manager._scan_devices()
            
            # Verify devices were found
            assert len(local_manager.devices['video']) > 0
            
            # Get first device
            device_id, device = next(iter(local_manager.devices['video'].items()))
            assert isinstance(device, LocalDevice)
            assert device.type == 'video'
            assert device.status == 'online'
            assert device.driver == 'v4l2'

@pytest.mark.asyncio
async def test_start_stream(local_manager):
    # Create a mock device
    device = LocalDevice(
        device_id="test_video",
        name="Test Camera",
        type="video",
        system_path="/dev/video0",
        driver="v4l2"
    )
    local_manager.devices['video']["test_video"] = device
    
    # Mock RTSP server
    with patch.object(local_manager.rtsp_server, 'start_stream') as mock_start_stream:
        mock_start_stream.return_value = "rtsp://localhost:8554/test_stream"
        
        # Start stream
        url = local_manager.start_stream("test_video", protocol="rtsp")
        
        assert url == "rtsp://localhost:8554/test_stream"
        mock_start_stream.assert_called_once()

def test_handle_command(local_manager):
    # Mock scan_devices and mcp_client
    with patch.object(local_manager, '_scan_devices') as mock_scan:
        with patch.object(local_manager, 'mcp_client') as mock_mcp:
            # Send scan command
            local_manager._handle_command("command/local_devices/scan", {})
            
            # Verify scan was called
            mock_scan.assert_called_once()
            
            # Verify MCP message was published
            mock_mcp.publish.assert_called()
