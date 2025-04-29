import pytest
from unittest.mock import MagicMock, patch

from rtaspi.core import LoggingManager, ConfigManager
from rtaspi.device_managers.utils.discovery import (
    DiscoveryModule,
    ONVIFDiscovery,
    UPnPDiscovery,
    MDNSDiscovery
)

@pytest.fixture
def onvif_discovery():
    return ONVIFDiscovery()

@pytest.fixture
def upnp_discovery():
    return UPnPDiscovery()

@pytest.fixture
def mdns_discovery():
    return MDNSDiscovery()

def test_onvif_discovery_initialization(onvif_discovery):
    assert isinstance(onvif_discovery, DiscoveryModule)
    assert isinstance(onvif_discovery, ONVIFDiscovery)

def test_upnp_discovery_initialization(upnp_discovery):
    assert isinstance(upnp_discovery, DiscoveryModule)
    assert isinstance(upnp_discovery, UPnPDiscovery)

def test_mdns_discovery_initialization(mdns_discovery):
    assert isinstance(mdns_discovery, DiscoveryModule)
    assert isinstance(mdns_discovery, MDNSDiscovery)

def test_onvif_discovery(onvif_discovery):
    with patch.object(onvif_discovery, '_discover_with_library') as mock_discover:
        mock_discover.return_value = [
            {
                'name': 'Test Camera',
                'ip': '192.168.1.100',
                'port': 80,
                'type': 'video',
                'protocol': 'rtsp',
                'paths': ['/onvif-media/media.amp']
            }
        ]
        
        devices = onvif_discovery.discover()
        
        assert isinstance(devices, list)
        assert len(devices) == 1
        assert devices[0]['name'] == 'Test Camera'
        assert devices[0]['ip'] == '192.168.1.100'
        mock_discover.assert_called_once()

def test_upnp_discovery(upnp_discovery):
    with patch.object(upnp_discovery, '_discover_with_library') as mock_discover:
        mock_discover.return_value = [
            {
                'name': 'Test UPnP Device',
                'ip': '192.168.1.101',
                'port': 80,
                'type': 'video',
                'protocol': 'http'
            }
        ]
        
        devices = upnp_discovery.discover()
        
        assert isinstance(devices, list)
        assert len(devices) == 1
        assert devices[0]['name'] == 'Test UPnP Device'
        assert devices[0]['ip'] == '192.168.1.101'
        mock_discover.assert_called_once()

def test_mdns_discovery(mdns_discovery):
    with patch.object(mdns_discovery, '_discover_with_library') as mock_discover:
        mock_discover.return_value = [
            {
                'name': 'Test mDNS Device',
                'ip': '192.168.1.102',
                'port': 5353,
                'type': 'video',
                'protocol': 'rtsp'
            }
        ]
        
        devices = mdns_discovery.discover()
        
        assert isinstance(devices, list)
        assert len(devices) == 1
        assert devices[0]['name'] == 'Test mDNS Device'
        assert devices[0]['ip'] == '192.168.1.102'
        mock_discover.assert_called_once()
