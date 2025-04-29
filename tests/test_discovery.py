import pytest
from unittest.mock import MagicMock, patch

import sys
import os
from pathlib import Path

print("\nDebug information from test_discovery.py:")
print(f"Current working directory: {os.getcwd()}")
print(f"__file__: {__file__}")
print("sys.path:")
for p in sys.path:
    print(f"  {p}")

try:
    import rtaspi
    print(f"\nrtaspi found at: {rtaspi.__file__}")
    print(f"rtaspi.__path__: {rtaspi.__path__}")
    
    import rtaspi.core
    print(f"rtaspi.core found at: {rtaspi.core.__file__}")
    from rtaspi.core import LoggingManager, ConfigManager
    print("Successfully imported LoggingManager and ConfigManager")
    
    from rtaspi.device_managers.utils.discovery import DeviceDiscovery
    print("Successfully imported DeviceDiscovery")
except ImportError as e:
    print(f"\nImport error: {e}")
    print(f"Error type: {type(e)}")
    print(f"Error args: {e.args}")
    raise

@pytest.fixture
def discovery():
    config = ConfigManager()
    logger = LoggingManager()
    return DeviceDiscovery(config, logger)

def test_discovery_initialization(discovery):
    assert isinstance(discovery, DeviceDiscovery)
    assert hasattr(discovery, 'config')
    assert hasattr(discovery, 'logger')

@pytest.mark.asyncio
async def test_discover_devices(discovery):
    # Mock the discovery methods
    discovery._discover_upnp = MagicMock(return_value=[])
    discovery._discover_zeroconf = MagicMock(return_value=[])
    discovery._discover_wsd = MagicMock(return_value=[])
    discovery._discover_onvif = MagicMock(return_value=[])
    
    devices = await discovery.discover_devices()
    
    assert isinstance(devices, list)
    assert discovery._discover_upnp.called
    assert discovery._discover_zeroconf.called
    assert discovery._discover_wsd.called
    assert discovery._discover_onvif.called
