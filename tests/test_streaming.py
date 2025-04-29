import pytest
from unittest.mock import MagicMock, patch

from rtaspi.streaming.rtsp import RTSPServer
from rtaspi.device_managers.utils.device import LocalDevice, NetworkDevice


@pytest.fixture
def rtsp_server(test_config):
    return RTSPServer(test_config)


def test_rtsp_server_initialization(rtsp_server, test_config):
    assert isinstance(rtsp_server, RTSPServer)
    assert rtsp_server.port_start == test_config["streaming"]["rtsp"]["port_start"]
    assert rtsp_server.storage_path == test_config["system"]["storage_path"]


@pytest.mark.asyncio
async def test_start_stream_local_device_success(rtsp_server, mock_local_device):
    # Mock subprocess and socket
    with patch("subprocess.Popen") as mock_popen, patch(
        "socket.socket"
    ) as mock_socket, patch("platform.system", return_value="Linux"):

        # Configure mock socket to indicate port is free
        mock_socket_instance = MagicMock()
        mock_socket_instance.connect_ex.return_value = 1  # Port is free
        mock_socket.return_value = mock_socket_instance

        # Configure mock process
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process is running
        mock_popen.return_value = mock_process

        # Start stream
        stream_url = await rtsp_server.start_stream(
            device=mock_local_device, stream_id="test_stream", output_dir="/tmp/streams"
        )

        # Verify stream was started
        assert stream_url is not None
        assert stream_url.startswith("rtsp://localhost:")
        assert "/test_stream" in stream_url

        # Verify FFmpeg was called with correct arguments
        mock_popen.assert_called_once()
        args = mock_popen.call_args[0][0]
        assert args[0] == "ffmpeg"
        assert "-f" in args
        assert "v4l2" in args
        assert "-i" in args
        assert "/dev/video0" in args
        assert "rtsp://localhost" in args[-1]


@pytest.mark.asyncio
async def test_start_stream_local_device_failure(rtsp_server, mock_local_device):
    with patch("subprocess.Popen") as mock_popen, patch("socket.socket") as mock_socket:
        # Configure mock socket
        mock_socket_instance = MagicMock()
        mock_socket_instance.connect_ex.return_value = 1
        mock_socket.return_value = mock_socket_instance

        # Configure mock process to fail immediately
        mock_process = MagicMock()
        mock_process.poll.return_value = 1  # Process failed
        mock_popen.return_value = mock_process

        # Start stream should return None on failure
        result = await rtsp_server.start_stream(
            device=mock_local_device,
            stream_id="test_stream",
            output_dir="/tmp/streams",
        )
        assert result is None


@pytest.mark.asyncio
async def test_start_stream_invalid_device(rtsp_server):
    invalid_device = LocalDevice(
        device_id="invalid",
        name="Invalid Device",
        type="unknown",  # Invalid type
        system_path="/dev/invalid",
        driver="unknown",
    )

    # Should return None for invalid device
    result = await rtsp_server.start_stream(
        device=invalid_device, stream_id="test_stream", output_dir="/tmp/streams"
    )
    assert result is None


@pytest.mark.asyncio
async def test_concurrent_streams(rtsp_server, mock_local_device):
    with patch("subprocess.Popen") as mock_popen, patch("socket.socket") as mock_socket:
        # Configure mock socket
        mock_socket_instance = MagicMock()
        mock_socket_instance.connect_ex.return_value = 1
        mock_socket.return_value = mock_socket_instance

        # Configure mock process
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        # Start multiple streams
        stream_urls = []
        for i in range(3):
            url = await rtsp_server.start_stream(
                device=mock_local_device,
                stream_id=f"test_stream_{i}",
                output_dir="/tmp/streams",
            )
            stream_urls.append(url)

        # Verify each stream got a unique port
        ports = [int(url.split(":")[2].split("/")[0]) for url in stream_urls]
        assert len(set(ports)) == 3  # All ports should be unique


@pytest.mark.asyncio
async def test_proxy_stream_network_device_success(rtsp_server, mock_network_device):
    # Mock subprocess and socket
    with patch("subprocess.Popen") as mock_popen, patch("socket.socket") as mock_socket:
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
        stream_url = await rtsp_server.proxy_stream(
            device=mock_network_device,
            stream_id="test_proxy",
            source_url=source_url,
            output_dir="/tmp/streams",
        )

        # Verify stream was started
        assert stream_url is not None
        assert stream_url.startswith("rtsp://localhost:")
        assert "/test_proxy" in stream_url

        # Verify FFmpeg was called with correct arguments
        mock_popen.assert_called_once()
        args = mock_popen.call_args[0][0]
        assert args[0] == "ffmpeg"
        assert "-rtsp_transport" in args
        assert "tcp" in args
        assert "-i" in args
        assert source_url in args
        assert "rtsp://localhost" in args[-1]


@pytest.mark.asyncio
async def test_proxy_stream_network_device_failure(rtsp_server, mock_network_device):
    with patch("subprocess.Popen") as mock_popen:
        # Configure mock process to fail
        mock_process = MagicMock()
        mock_process.poll.return_value = 1  # Process failed
        mock_popen.return_value = mock_process

        # Start proxy stream should return None on failure
        result = await rtsp_server.proxy_stream(
            device=mock_network_device,
            stream_id="test_proxy",
            source_url="rtsp://192.168.1.100:554/stream1",
            output_dir="/tmp/streams",
        )
        assert result is None


@pytest.mark.asyncio
async def test_stop_stream(rtsp_server, mock_local_device):
    with patch("subprocess.Popen") as mock_popen:
        # Configure mock process
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        # Start stream
        stream_url = await rtsp_server.start_stream(
            device=mock_local_device, stream_id="test_stream", output_dir="/tmp/streams"
        )

        # Stop stream
        success = await rtsp_server.stop_stream("test_stream")
        assert success
        mock_process.terminate.assert_called_once()


@pytest.mark.asyncio
async def test_stop_nonexistent_stream(rtsp_server):
    success = await rtsp_server.stop_stream("nonexistent_stream")
    assert not success


@pytest.mark.asyncio
async def test_get_stream_status(rtsp_server, mock_local_device):
    with patch("subprocess.Popen") as mock_popen:
        # Configure mock process
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        # Start stream
        await rtsp_server.start_stream(
            device=mock_local_device, stream_id="test_stream", output_dir="/tmp/streams"
        )

        # Check status
        status = rtsp_server.get_stream_status("test_stream")
        assert status == "running"

        # Simulate process termination
        mock_process.poll.return_value = 0
        status = rtsp_server.get_stream_status("test_stream")
        assert status == "stopped"


@pytest.mark.asyncio
async def test_cleanup_on_shutdown(rtsp_server, mock_local_device):
    with patch("subprocess.Popen") as mock_popen:
        # Start multiple streams
        mock_processes = []
        for i in range(3):
            mock_process = MagicMock()
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process
            mock_processes.append(mock_process)

            await rtsp_server.start_stream(
                device=mock_local_device,
                stream_id=f"test_stream_{i}",
                output_dir="/tmp/streams",
            )

        # Shutdown server
        await rtsp_server.shutdown()

        # Verify all processes were terminated
        for process in mock_processes:
            process.terminate.assert_called_once()


def test_find_free_port(rtsp_server):
    # Mock socket to simulate ports 8554-8556 being used and 8557 being free
    with patch("socket.socket") as mock_socket:
        mock_socket_instance = MagicMock()
        mock_socket_instance.connect_ex.side_effect = [
            0,
            0,
            0,
            1,
        ]  # First 3 ports used, 4th free
        mock_socket.return_value = mock_socket_instance

        port = rtsp_server._find_free_port(8554)

        assert port == 8557
        assert mock_socket_instance.connect_ex.call_count == 4


def test_prepare_output_args(rtsp_server, mock_local_device):
    # Test video device
    mock_local_device.type = "video"
    args = rtsp_server._prepare_output_args(mock_local_device, 8554, "test_stream")
    assert args is not None
    assert "-c:v" in args
    assert "libx264" in args
    assert "rtsp://localhost:8554/test_stream" in args

    # Test audio device
    mock_local_device.type = "audio"
    args = rtsp_server._prepare_output_args(mock_local_device, 8554, "test_stream")
    assert args is not None
    assert "-c:a" in args
    assert "aac" in args
    assert "rtsp://localhost:8554/test_stream" in args
