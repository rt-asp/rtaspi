import pytest
from unittest.mock import MagicMock, patch
import socket
from urllib.parse import urlparse

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

def test_onvif_discovery_with_library(onvif_discovery):
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

def test_onvif_discovery_alternative(onvif_discovery):
    with patch.object(onvif_discovery, '_discover_with_library', side_effect=ImportError), \
         patch.object(onvif_discovery, '_discover_alternative') as mock_alternative:
        mock_alternative.return_value = [
            {
                'name': 'ONVIF Camera',
                'ip': '192.168.1.101',
                'port': 80,
                'type': 'video',
                'protocol': 'rtsp',
                'paths': ['/onvif-media/media.amp']
            }
        ]
        
        devices = onvif_discovery.discover()
        
        assert isinstance(devices, list)
        assert len(devices) == 1
        assert devices[0]['name'] == 'ONVIF Camera'
        assert devices[0]['ip'] == '192.168.1.101'
        mock_alternative.assert_called_once()

def test_onvif_discovery_error_handling(onvif_discovery):
    with patch.object(onvif_discovery, '_discover_with_library', side_effect=Exception("Test error")):
        devices = onvif_discovery.discover()
        assert isinstance(devices, list)
        assert len(devices) == 0

def test_onvif_extract_ip_from_xaddrs(onvif_discovery):
    # Test valid XAddrs
    xaddrs = ['http://192.168.1.100:80/onvif/device_service']
    assert onvif_discovery._extract_ip_from_xaddrs(xaddrs) == '192.168.1.100'
    
    # Test empty XAddrs
    assert onvif_discovery._extract_ip_from_xaddrs([]) is None
    
    # Test invalid XAddrs
    assert onvif_discovery._extract_ip_from_xaddrs(['invalid_url']) is None

def test_onvif_extract_port_from_xaddrs(onvif_discovery):
    # Test valid XAddrs with port
    xaddrs = ['http://192.168.1.100:8080/onvif/device_service']
    assert onvif_discovery._extract_port_from_xaddrs(xaddrs) == 8080
    
    # Test valid XAddrs without port (should default to 80)
    xaddrs = ['http://192.168.1.100/onvif/device_service']
    assert onvif_discovery._extract_port_from_xaddrs(xaddrs) == 80
    
    # Test empty XAddrs (should default to 80)
    assert onvif_discovery._extract_port_from_xaddrs([]) == 80

def test_upnp_discovery_with_library(upnp_discovery):
    with patch.object(upnp_discovery, '_discover_with_library') as mock_discover:
        mock_discover.return_value = [
            {
                'name': 'Test Video Device',
                'ip': '192.168.1.101',
                'port': 80,
                'type': 'video',
                'protocol': 'http'
            },
            {
                'name': 'Test Audio Device',
                'ip': '192.168.1.102',
                'port': 80,
                'type': 'audio',
                'protocol': 'http'
            }
        ]
        
        devices = upnp_discovery.discover()
        
        assert isinstance(devices, list)
        assert len(devices) == 2
        assert devices[0]['name'] == 'Test Video Device'
        assert devices[0]['type'] == 'video'
        assert devices[1]['name'] == 'Test Audio Device'
        assert devices[1]['type'] == 'audio'
        mock_discover.assert_called_once()

def test_upnp_discovery_alternative(upnp_discovery):
    with patch.object(upnp_discovery, '_discover_with_library', side_effect=ImportError), \
         patch.object(upnp_discovery, '_discover_alternative') as mock_alternative:
        mock_alternative.return_value = [
            {
                'name': 'UPnP Device (192.168.1.103)',
                'ip': '192.168.1.103',
                'port': 80,
                'type': 'video',
                'protocol': 'http'
            }
        ]
        
        devices = upnp_discovery.discover()
        
        assert isinstance(devices, list)
        assert len(devices) == 1
        assert '192.168.1.103' in devices[0]['name']
        mock_alternative.assert_called_once()

def test_upnp_discovery_error_handling(upnp_discovery):
    with patch.object(upnp_discovery, '_discover_with_library', side_effect=Exception("Test error")):
        devices = upnp_discovery.discover()
        assert isinstance(devices, list)
        assert len(devices) == 0

def test_upnp_discovery_timeout(upnp_discovery):
    with patch.object(upnp_discovery, '_discover_with_library') as mock_discover:
        mock_discover.side_effect = socket.timeout()
        devices = upnp_discovery.discover()
        assert isinstance(devices, list)
        assert len(devices) == 0

def test_mdns_discovery_with_library(mdns_discovery):
    with patch.object(mdns_discovery, '_discover_with_library') as mock_discover:
        mock_discover.return_value = [
            {
                'name': 'Test RTSP Camera',
                'ip': '192.168.1.102',
                'port': 5353,
                'type': 'video',
                'protocol': 'rtsp'
            },
            {
                'name': 'Test HTTP Camera',
                'ip': '192.168.1.103',
                'port': 5353,
                'type': 'video',
                'protocol': 'http'
            }
        ]
        
        devices = mdns_discovery.discover()
        
        assert isinstance(devices, list)
        assert len(devices) == 2
        assert devices[0]['protocol'] == 'rtsp'
        assert devices[1]['protocol'] == 'http'
        mock_discover.assert_called_once()

def test_mdns_discovery_alternative(mdns_discovery):
    with patch.object(mdns_discovery, '_discover_with_library', side_effect=ImportError), \
         patch.object(mdns_discovery, '_discover_alternative') as mock_alternative:
        mock_alternative.return_value = [
            {
                'name': 'mDNS Device (192.168.1.104)',
                'ip': '192.168.1.104',
                'port': 5353,
                'type': 'video',
                'protocol': 'rtsp'
            }
        ]
        
        devices = mdns_discovery.discover()
        
        assert isinstance(devices, list)
        assert len(devices) == 1
        assert '192.168.1.104' in devices[0]['name']
        mock_alternative.assert_called_once()

def test_mdns_discovery_error_handling(mdns_discovery):
    with patch.object(mdns_discovery, '_discover_with_library', side_effect=Exception("Test error")):
        devices = mdns_discovery.discover()
        assert isinstance(devices, list)
        assert len(devices) == 0

def test_mdns_discovery_empty_response(mdns_discovery):
    with patch.object(mdns_discovery, '_discover_with_library') as mock_discover:
        mock_discover.return_value = []
        devices = mdns_discovery.discover()
        assert isinstance(devices, list)
        assert len(devices) == 0
