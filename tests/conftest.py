import os
import sys
import shutil
import logging
import tempfile
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from rtaspi.core import LoggingManager, ConfigManager
from rtaspi.core.logging import setup_logging
from rtaspi.core.mcp import MCPBroker
from rtaspi.device_managers.utils.device import LocalDevice, NetworkDevice


def pytest_configure(config):
    """Configure pytest before running tests."""
    try:
        # Get absolute paths
        current_dir = Path(__file__).resolve().parent
        project_root = current_dir.parent
        src_dir = project_root / "src"

        # Verify required directories exist
        required_dirs = {
            "src": src_dir,
            "rtaspi": src_dir / "rtaspi",
            "device_managers": src_dir / "rtaspi/device_managers",
            "streaming": src_dir / "rtaspi/streaming",
            "core": src_dir / "rtaspi/core",
        }

        for name, path in required_dirs.items():
            if not path.exists():
                raise RuntimeError(f"{name} directory not found at {path}")

        # Configure Python path
        sys.path.clear()
        sys.path.extend(
            [
                str(src_dir),
                str(project_root / "venv/lib/python3.12/site-packages"),
                "/home/tom/miniconda3/lib/python3.12",
                "/home/tom/miniconda3/lib/python3.12/lib-dynload",
            ]
        )

        # Configure logging for tests
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    except Exception as e:
        print(f"\nError during test configuration: {e}")
        raise


@pytest.fixture(scope="session")
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup after all tests
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="session")
def test_config():
    """Common test configuration."""
    return {
        "system": {"storage_path": "/tmp", "log_level": "DEBUG"},
        "local_devices": {
            "enable_video": True,
            "enable_audio": True,
            "auto_start": False,
            "scan_interval": 60,
            "rtsp_port_start": 8554,
            "rtmp_port_start": 1935,
            "webrtc_port_start": 8080,
        },
        "network_devices": {
            "scan_interval": 60,
            "discovery_enabled": True,
            "discovery_methods": ["onvif", "upnp", "mdns"],
        },
        "streaming": {
            "rtsp": {"port_start": 8554},
            "rtmp": {"port_start": 1935},
            "webrtc": {"port_start": 8080},
        },
    }


@pytest.fixture(scope="session")
def mcp_broker():
    """Common MCP broker mock."""
    return MagicMock(spec=MCPBroker)


@pytest.fixture
def mock_local_device():
    """Common local device fixture."""
    return LocalDevice(
        device_id="test_video",
        name="Test Camera",
        type="video",
        system_path="/dev/video0",
        driver="v4l2",
    )


@pytest.fixture
def mock_network_device():
    """Common network device fixture."""
    return NetworkDevice(
        device_id="test_ip_camera",
        name="Test IP Camera",
        type="video",
        ip="192.168.1.100",
        port=554,
        protocol="rtsp",
    )


@pytest.fixture(scope="session", autouse=True)
def setup_test_env(temp_dir):
    """Setup test environment variables and configurations."""
    # Set environment variables for testing
    os.environ["RTASPI_TEST_MODE"] = "true"
    os.environ["RTASPI_STORAGE_PATH"] = temp_dir
    os.environ["RTASPI_LOG_LEVEL"] = "DEBUG"

    # Initialize logging
    config = {
        "system": {
            "log_level": os.environ["RTASPI_LOG_LEVEL"],
            "storage_path": os.environ["RTASPI_STORAGE_PATH"],
        }
    }
    setup_logging(config)

    yield

    # Cleanup
    os.environ.pop("RTASPI_TEST_MODE", None)
    os.environ.pop("RTASPI_STORAGE_PATH", None)
    os.environ.pop("RTASPI_LOG_LEVEL", None)
