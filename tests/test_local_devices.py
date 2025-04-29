import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

from rtaspi.core.mcp import MCPBroker
from rtaspi.device_managers.local_devices import LocalDevicesManager
from rtaspi.device_managers.utils.device import LocalDevice, DeviceStatus

@pytest.fixture
def local_manager(test_config, mcp_broker):
    return LocalDevicesManager(test_config, mcp_broker)

def test_local_manager_initialization(local_manager, test_config):
    assert isinstance(local_manager, LocalDevicesManager)
    assert hasattr(local_manager, 'mcp_broker')
    assert hasattr(local_manager, 'devices')
    assert isinstance(local_manager.devices, dict)
    assert 'video' in local_manager.devices
    assert 'audio' in local_manager.devices
    assert local_manager.enable_video == test_config['local_devices']['enable_video']
    assert local_manager.enable_audio == test_config['local_devices']['enable_audio']
    assert local_manager.auto_start == test_config['local_devices']['auto_start']
    assert local_manager.scan_interval == test_config['local_devices']['scan_interval']

@pytest.mark.asyncio
async def test_scan_video_devices_success(local_manager):
    # Mock platform to return 'linux'
    with patch('platform.system', return_value='Linux'):
        # Mock subprocess calls
        with patch('pathlib.Path.glob', return_value=[Path('/dev/video0')]):
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
            assert device.status == DeviceStatus.ONLINE
            assert device.driver == 'v4l2'
            assert device.capabilities['formats'] == ['YUYV']
            assert device.capabilities['resolutions'] == ['640x480']

@pytest.mark.asyncio
async def test_scan_video_devices_error(local_manager):
    with patch('platform.system', return_value='Linux'):
        with patch('subprocess.check_output', side_effect=Exception("Test error")):
            # Should not raise exception, but log error and continue
            local_manager._scan_devices()
            assert len(local_manager.devices['video']) == 0

@pytest.mark.asyncio
async def test_scan_audio_devices_success(local_manager):
    mock_audio_devices = '''**** List of CAPTURE Hardware Devices ****
card 0: TestMic [Test Microphone], device 0: USB Audio [USB Audio]
  Subdevices: 1/1
  Subdevice #0: subdevice #0'''
    
    with patch('subprocess.check_output', return_value=mock_audio_devices):
        local_manager._scan_devices()
        
        assert len(local_manager.devices['audio']) > 0
        device_id, device = next(iter(local_manager.devices['audio'].items()))
        assert isinstance(device, LocalDevice)
        assert device.type == 'audio'
        assert device.status == DeviceStatus.ONLINE
        assert device.name == 'Test Microphone'

@pytest.mark.asyncio
async def test_scan_audio_devices_error(local_manager):
    with patch('subprocess.check_output', side_effect=Exception("Test error")):
        # Should not raise exception, but log error and continue
        local_manager._scan_devices()
        assert len(local_manager.devices['audio']) == 0

@pytest.mark.asyncio
async def test_auto_start_enabled(test_config, mcp_broker, mock_local_device):
    test_config['local_devices']['auto_start'] = True
    manager = LocalDevicesManager(test_config, mcp_broker)
    
    # Add a test device
    manager.devices['video'][mock_local_device.device_id] = mock_local_device
    
    # Mock device scanning and stream starting
    with patch.object(manager, '_scan_devices') as mock_scan, \
         patch.object(manager, 'start_stream') as mock_start:
        mock_scan.return_value = None
        mock_start.return_value = "rtsp://localhost:8554/test"
        
        # Initialize manager which should trigger auto-start
        await manager.initialize()
        
        mock_scan.assert_called_once()
        mock_start.assert_called_once_with(mock_local_device.device_id, protocol="rtsp")

@pytest.mark.asyncio
async def test_start_stream_rtsp(local_manager, mock_local_device):
    local_manager.devices['video'][mock_local_device.device_id] = mock_local_device
    
    # Mock RTSP server
    with patch.object(local_manager.rtsp_server, 'start_stream') as mock_start_stream:
        mock_start_stream.return_value = "rtsp://localhost:8554/test_stream"
        
        # Start stream
        url = await local_manager.start_stream("test_video", protocol="rtsp")
        
        assert url == "rtsp://localhost:8554/test_stream"
        mock_start_stream.assert_called_once()

@pytest.mark.asyncio
async def test_start_stream_rtmp(local_manager, mock_local_device):
    local_manager.devices['video'][mock_local_device.device_id] = mock_local_device
    
    with patch.object(local_manager.rtmp_server, 'start_stream') as mock_start_stream:
        mock_start_stream.return_value = "rtmp://localhost:1935/live/test_stream"
        
        url = await local_manager.start_stream("test_video", protocol="rtmp")
        
        assert url == "rtmp://localhost:1935/live/test_stream"
        mock_start_stream.assert_called_once()

@pytest.mark.asyncio
async def test_start_stream_webrtc(local_manager, mock_local_device):
    local_manager.devices['video'][mock_local_device.device_id] = mock_local_device
    
    with patch.object(local_manager.webrtc_server, 'start_stream') as mock_start_stream:
        mock_start_stream.return_value = "ws://localhost:8080/test_stream"
        
        url = await local_manager.start_stream("test_video", protocol="webrtc")
        
        assert url == "ws://localhost:8080/test_stream"
        mock_start_stream.assert_called_once()

@pytest.mark.asyncio
async def test_start_stream_invalid_device(local_manager):
    with pytest.raises(ValueError):
        await local_manager.start_stream("nonexistent_device", protocol="rtsp")

@pytest.mark.asyncio
async def test_start_stream_invalid_protocol(local_manager, mock_local_device):
    local_manager.devices['video'][mock_local_device.device_id] = mock_local_device
    
    with pytest.raises(ValueError):
        await local_manager.start_stream("test_video", protocol="invalid")

@pytest.mark.asyncio
async def test_stop_stream(local_manager, mock_local_device):
    local_manager.devices['video'][mock_local_device.device_id] = mock_local_device
    
    # Add a test stream
    stream_id = "test_stream"
    local_manager.streams[stream_id] = {
        "stream_id": stream_id,
        "device_id": mock_local_device.device_id,
        "type": "video",
        "protocol": "rtsp",
        "url": "rtsp://localhost:8554/test"
    }
    
    # Mock stream servers
    with patch.object(local_manager.rtsp_server, 'stop_stream') as mock_stop_rtsp:
        mock_stop_rtsp.return_value = True
        
        success = await local_manager.stop_stream(stream_id)
        assert success
        
        mock_stop_rtsp.assert_called_once_with(stream_id)

@pytest.mark.asyncio
async def test_stop_stream_invalid_device(local_manager):
    success = await local_manager.stop_stream("nonexistent_device")
    assert not success

@pytest.mark.asyncio
async def test_handle_command_valid(local_manager, mock_local_device):
    # Mock scan_devices and mcp_client
    with patch.object(local_manager, '_scan_devices') as mock_scan, \
         patch.object(local_manager, 'mcp_client') as mock_mcp:
        
        # Test scan command
        await local_manager._handle_command("command/local_devices/scan", {})
        mock_scan.assert_called_once()
        mock_mcp.publish.assert_called()
        
        # Test start stream command
        local_manager.devices['video'][mock_local_device.device_id] = mock_local_device
        
        with patch.object(local_manager, 'start_stream') as mock_start:
            mock_start.return_value = "rtsp://localhost:8554/test"
            await local_manager._handle_command("command/local_devices/start_stream", {
                "device_id": "test_video",
                "protocol": "rtsp"
            })
            mock_start.assert_called_once_with("test_video", protocol="rtsp")

@pytest.mark.asyncio
async def test_handle_command_invalid(local_manager):
    # Test invalid command type
    with pytest.raises(ValueError):
        await local_manager._handle_command("command/local_devices/invalid", {})
    
    # Test start stream with missing parameters
    with pytest.raises(ValueError):
        await local_manager._handle_command("command/local_devices/start_stream", {})
    
    # Test start stream with invalid device
    with pytest.raises(ValueError):
        await local_manager._handle_command("command/local_devices/start_stream", {
            "device_id": "nonexistent",
            "protocol": "rtsp"
        })

@pytest.mark.asyncio
async def test_update_device_status(local_manager, mock_local_device):
    local_manager.devices['video'][mock_local_device.device_id] = mock_local_device
    
    # Update status to offline
    local_manager.update_device_status(mock_local_device.device_id, DeviceStatus.OFFLINE)
    assert mock_local_device.status == DeviceStatus.OFFLINE
    
    # Update status back to online
    local_manager.update_device_status(mock_local_device.device_id, DeviceStatus.ONLINE)
    assert mock_local_device.status == DeviceStatus.ONLINE
    
    # Test invalid status
    with pytest.raises(ValueError):
        local_manager.update_device_status(mock_local_device.device_id, "invalid")
