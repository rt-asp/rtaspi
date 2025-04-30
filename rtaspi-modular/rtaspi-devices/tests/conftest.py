"""
Pytest configuration and fixtures for rtaspi-devices tests.
"""

import pytest
import asyncio
import logging
from unittest.mock import MagicMock, AsyncMock
from rtaspi_devices import DeviceManager
from rtaspi_devices.events import EventSystem

@pytest.fixture
def event_loop():
    """Create and provide an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_config():
    """Provide a test configuration."""
    return {
        "system": {
            "storage_path": "test_storage",
            "log_level": "INFO"
        },
        "devices": {
            "network": {
                "enabled": True,
                "discovery": {
                    "enabled": True,
                    "scan_ranges": ["192.168.1.0/24"],
                    "protocols": ["rtsp", "onvif"]
                }
            },
            "local": {
                "enabled": True,
                "auto_connect": True,
                "drivers": ["v4l2", "alsa"]
            }
        }
    }

@pytest.fixture
def mock_device():
    """Provide a mock device for testing."""
    return {
        'id': 'test-device-1',
        'name': 'Test Camera',
        'type': 'video',
        'status': 'online',
        'protocol': 'rtsp',
        'address': '192.168.1.100'
    }

@pytest.fixture
def mock_stream():
    """Provide a mock stream for testing."""
    return {
        'id': 'stream-1',
        'device_id': 'test-device-1',
        'format': 'h264',
        'resolution': '1280x720'
    }

@pytest.fixture
def event_system():
    """Provide an event system for testing."""
    return EventSystem()

@pytest.fixture
def mock_device_manager(test_config, event_system):
    """Provide a mock device manager for testing."""
    manager = MagicMock(spec=DeviceManager)
    manager.start = AsyncMock()
    manager.stop = AsyncMock()
    manager.get_devices.return_value = {
        'test-device-1': MagicMock(
            id='test-device-1',
            name='Test Camera',
            type='video',
            get_status=AsyncMock(return_value='online')
        )
    }
    manager.start_stream = AsyncMock(return_value={
        'id': 'stream-1',
        'device_id': 'test-device-1',
        'format': 'h264'
    })
    return manager

@pytest.fixture
def mock_network_discovery():
    """Provide mock network discovery functionality."""
    async def discover_devices(*args, **kwargs):
        return [
            {
                'id': 'camera-1',
                'name': 'IP Camera 1',
                'type': 'video',
                'protocol': 'rtsp',
                'address': '192.168.1.100'
            },
            {
                'id': 'camera-2',
                'name': 'IP Camera 2',
                'type': 'video',
                'protocol': 'onvif',
                'address': '192.168.1.101'
            }
        ]
    return AsyncMock(side_effect=discover_devices)

@pytest.fixture
def example_test_env(tmp_path):
    """Set up a test environment for examples."""
    # Create test directories
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()
    
    # Create test environment
    env = {
        "storage_path": str(storage_dir),
        "test_device": {
            "id": "test-camera",
            "name": "Test Camera",
            "type": "video",
            "address": "127.0.0.1"
        }
    }
    
    return env

@pytest.fixture(autouse=True)
def setup_logging():
    """Configure logging for tests."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
