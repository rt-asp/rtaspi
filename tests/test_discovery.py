import pytest
import socket
import asyncio
from unittest.mock import MagicMock, patch
from urllib.parse import urlparse

from rtaspi.core import LoggingManager, ConfigManager
from rtaspi.device_managers.utils.discovery import (
    DiscoveryModule,
    ONVIFDiscovery,
    UPnPDiscovery,
    MDNSDiscovery,
)

# Test data for parametrization
DISCOVERY_MODULES = [
    (ONVIFDiscovery, "onvif"),
    (UPnPDiscovery, "upnp"),
    (MDNSDiscovery, "mdns"),
]

MOCK_DEVICES = {
    "onvif": {
        "name": "Test ONVIF Camera",
        "ip": "192.168.1.100",
        "port": 80,
        "type": "video",
        "protocol": "rtsp",
        "paths": ["/onvif-media/media.amp"],
    },
    "upnp": {
        "name": "Test UPnP Device",
        "ip": "192.168.1.101",
        "port": 80,
        "type": "video",
        "protocol": "http",
    },
    "mdns": {
        "name": "Test mDNS Device",
        "ip": "192.168.1.102",
        "port": 5353,
        "type": "video",
        "protocol": "rtsp",
    },
}


@pytest.fixture(params=DISCOVERY_MODULES)
def discovery_module(request):
    """Parametrized fixture for discovery modules."""
    module_class, _ = request.param
    return module_class()


@pytest.mark.unit
@pytest.mark.discovery
def test_discovery_initialization(discovery_module):
    """Test initialization of discovery modules."""
    assert isinstance(discovery_module, DiscoveryModule)
    assert isinstance(discovery_module, discovery_module.__class__)


@pytest.mark.unit
@pytest.mark.discovery
@pytest.mark.parametrize("discovery_class,module_type", DISCOVERY_MODULES)
def test_discovery_with_library(discovery_class, module_type):
    """Test discovery using primary library method."""
    discovery = discovery_class()
    with patch.object(discovery, "_discover_with_library") as mock_discover:
        mock_discover.return_value = [MOCK_DEVICES[module_type]]
        devices = discovery.discover()

        assert isinstance(devices, list)
        assert len(devices) == 1
        assert devices[0]["name"] == MOCK_DEVICES[module_type]["name"]
        assert devices[0]["ip"] == MOCK_DEVICES[module_type]["ip"]
        mock_discover.assert_called_once()


@pytest.mark.unit
@pytest.mark.discovery
@pytest.mark.parametrize("discovery_class,module_type", DISCOVERY_MODULES)
def test_discovery_alternative(discovery_class, module_type):
    """Test discovery using alternative method when primary fails."""
    discovery = discovery_class()
    with patch.object(
        discovery, "_discover_with_library", side_effect=ImportError
    ), patch.object(discovery, "_discover_alternative") as mock_alternative:
        mock_alternative.return_value = [MOCK_DEVICES[module_type]]
        devices = discovery.discover()

        assert isinstance(devices, list)
        assert len(devices) == 1
        assert devices[0]["ip"] == MOCK_DEVICES[module_type]["ip"]
        mock_alternative.assert_called_once()


@pytest.mark.unit
@pytest.mark.discovery
@pytest.mark.parametrize("discovery_class,module_type", DISCOVERY_MODULES)
def test_discovery_error_handling(discovery_class, module_type):
    """Test error handling in discovery process."""
    discovery = discovery_class()
    with patch.object(
        discovery, "_discover_with_library", side_effect=Exception("Test error")
    ):
        devices = discovery.discover()
        assert isinstance(devices, list)
        assert len(devices) == 0


@pytest.mark.unit
@pytest.mark.discovery
@pytest.mark.asyncio
@pytest.mark.parametrize("discovery_class,module_type", DISCOVERY_MODULES)
async def test_async_discovery(discovery_class, module_type):
    """Test asynchronous discovery functionality."""
    discovery = discovery_class()
    with patch.object(discovery, "_discover_with_library") as mock_discover:
        mock_discover.return_value = [MOCK_DEVICES[module_type]]

        # Simulate async discovery
        devices = await asyncio.gather(asyncio.to_thread(discovery.discover))

        assert isinstance(devices[0], list)
        assert len(devices[0]) == 1
        assert devices[0][0]["ip"] == MOCK_DEVICES[module_type]["ip"]
        mock_discover.assert_called_once()


@pytest.mark.unit
@pytest.mark.discovery
def test_onvif_xaddr_parsing():
    """Test ONVIF-specific XAddr parsing."""
    discovery = ONVIFDiscovery()

    test_cases = [
        {
            "xaddrs": ["http://192.168.1.100:8080/onvif/device_service"],
            "expected_ip": "192.168.1.100",
            "expected_port": 8080,
        },
        {
            "xaddrs": ["http://192.168.1.100/onvif/device_service"],
            "expected_ip": "192.168.1.100",
            "expected_port": 80,
        },
        {"xaddrs": [], "expected_ip": None, "expected_port": 80},
        {"xaddrs": ["invalid_url"], "expected_ip": None, "expected_port": 80},
    ]

    for case in test_cases:
        assert discovery._extract_ip_from_xaddrs(case["xaddrs"]) == case["expected_ip"]
        assert (
            discovery._extract_port_from_xaddrs(case["xaddrs"]) == case["expected_port"]
        )


@pytest.mark.unit
@pytest.mark.discovery
def test_upnp_timeout_handling():
    """Test UPnP timeout handling."""
    discovery = UPnPDiscovery()
    with patch.object(discovery, "_discover_with_library") as mock_discover:
        mock_discover.side_effect = socket.timeout()
        devices = discovery.discover()
        assert isinstance(devices, list)
        assert len(devices) == 0


@pytest.mark.unit
@pytest.mark.discovery
def test_mdns_empty_response():
    """Test mDNS empty response handling."""
    discovery = MDNSDiscovery()
    with patch.object(discovery, "_discover_with_library") as mock_discover:
        mock_discover.return_value = []
        devices = discovery.discover()
        assert isinstance(devices, list)
        assert len(devices) == 0
