"""
test_discovery.py
"""

import pytest
from unittest.mock import patch, MagicMock

from rtaspi.device_managers.utils.discovery import ONVIFDiscovery, UPnPDiscovery, MDNSDiscovery

# Fixtures
@pytest.fixture
def onvif_discovery():
    return ONVIFDiscovery()

@pytest.fixture
def upnp_discovery():
    return UPnPDiscovery()

@pytest.fixture
def mdns_discovery():
    return MDNSDiscovery()

# ONVIF Tests
@patch('rtaspi.device_managers.utils.discovery.ONVIFDiscovery._discover_with_library')
@patch('rtaspi.device_managers.utils.discovery.ONVIFDiscovery._discover_alternative')
def test_onvif_discover(mock_alternative, mock_library, onvif_discovery):
    """Test ONVIF device discovery."""
    # Simulate found devices
    mock_library.return_value = [{
        'name': 'ONVIF Camera 1',
        'ip': '192.168.1.101',
        'port': 80,
        'type': 'video',
        'protocol': 'rtsp',
        'paths': ['onvif1']
    }]

    mock_alternative.return_value = [{
        'name': 'ONVIF Camera 2',
        'ip': '192.168.1.102',
        'port': 80,
        'type': 'video',
        'protocol': 'rtsp',
        'paths': ['onvif1']
    }]

    # Test with working library
    with patch('importlib.import_module', return_value=MagicMock()):
        devices = onvif_discovery.discover()

        # Check if devices were discovered
        assert len(devices) == 1
        assert devices[0]['name'] == 'ONVIF Camera 1'
        mock_library.assert_called_once()
        mock_alternative.assert_not_called()

    # Reset mocks
    mock_library.reset_mock()
    mock_alternative.reset_mock()

    # Test without library
    with patch('importlib.import_module', side_effect=ImportError):
        devices = onvif_discovery.discover()

        # Check if devices were discovered
        assert len(devices) == 1
        assert devices[0]['name'] == 'ONVIF Camera 2'
        mock_library.assert_not_called()
        mock_alternative.assert_called_once()

@patch('socket.socket')
def test_onvif_discover_alternative(mock_socket, onvif_discovery):
    """Test alternative ONVIF device discovery."""
    # Simulate socket response
    mock_socket_instance = MagicMock()
    mock_socket.return_value = mock_socket_instance

    # Simulate receiving data
    response = """
    <?xml version="1.0" encoding="UTF-8"?>
    <SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope">
      <SOAP-ENV:Header>
        <wsa:MessageID>uuid:1</wsa:MessageID>
        <wsa:RelatesTo>uuid:2</wsa:RelatesTo>
      </SOAP-ENV:Header>
      <SOAP-ENV:Body>
        <d:ProbeMatches xmlns:d="http://schemas.xmlsoap.org/ws/2005/04/discovery">
          <d:ProbeMatch>
            <d:XAddrs>http://192.168.1.103:80/onvif/device_service</d:XAddrs>
            <d:Types>dn:NetworkVideoTransmitter</d:Types>
          </d:ProbeMatch>
        </d:ProbeMatches>
      </SOAP-ENV:Body>
    </SOAP-ENV:Envelope>
    """

    mock_socket_instance.recvfrom.side_effect = [(response.encode(), ('192.168.1.103', 80)), socket.timeout()]

    # Call method
    devices = onvif_discovery._discover_alternative()

    # Check if devices were discovered
    assert len(devices) == 1
    assert devices[0]['ip'] == '192.168.1.103'
    assert devices[0]['port'] == 80
    assert devices[0]['protocol'] == 'rtsp'

# UPnP Tests
@patch('rtaspi.device_managers.utils.discovery.UPnPDiscovery._discover_with_library')
@patch('rtaspi.device_managers.utils.discovery.UPnPDiscovery._discover_alternative')
def test_upnp_discover(mock_alternative, mock_library, upnp_discovery):
    """Test UPnP device discovery."""
    # Simulate found devices
    mock_library.return_value = [{
        'name': 'UPnP Camera 1',
        'ip': '192.168.1.104',
        'port': 80,
        'type': 'video',
        'protocol': 'http'
    }]

    mock_alternative.return_value = [{
        'name': 'UPnP Camera 2',
        'ip': '192.168.1.105',
        'port': 80,
        'type': 'video',
        'protocol': 'http'
    }]

    # Test with working library
    with patch('importlib.import_module', return_value=MagicMock()):
        devices = upnp_discovery.discover()

        # Check if devices were discovered
        assert len(devices) == 1
        assert devices[0]['name'] == 'UPnP Camera 1'
        mock_library.assert_called_once()
        mock_alternative.assert_not_called()

    # Reset mocks
    mock_library.reset_mock()
    mock_alternative.reset_mock()

    # Test without library
    with patch('importlib.import_module', side_effect=ImportError):
        devices = upnp_discovery.discover()

        # Check if devices were discovered
        assert len(devices) == 1
        assert devices[0]['name'] == 'UPnP Camera 2'
        mock_library.assert_not_called()
        mock_alternative.assert_called_once()

@patch('socket.socket')
def test_upnp_discover_alternative(mock_socket, upnp_discovery):
    """Test alternative UPnP device discovery."""
    # Simulate socket response
    mock_socket_instance = MagicMock()
    mock_socket.return_value = mock_socket_instance

    # Simulate receiving data
    response = """
    HTTP/1.1 200 OK
    CACHE-CONTROL: max-age=1800
    LOCATION: http://192.168.1.106:80/description.xml
    NT: upnp:rootdevice
    NTS: ssdp:alive
    SERVER: Linux/3.10.33 UPnP/1.0 MiniUPnPd/1.8
    USN: uuid:abcdef-1234::upnp:rootdevice

    """

    mock_socket_instance.recvfrom.side_effect = [(response.encode(), ('192.168.1.106', 1900)), socket.timeout()]

    # Call method
    devices = upnp_discovery._discover_alternative()

    # Check if devices were discovered
    assert len(devices) == 1
    assert devices[0]['ip'] == '192.168.1.106'
    assert devices[0]['port'] == 80
    assert devices[0]['protocol'] == 'http'

# mDNS Tests
@patch('rtaspi.device_managers.utils.discovery.MDNSDiscovery._discover_with_library')
@patch('rtaspi.device_managers.utils.discovery.MDNSDiscovery._discover_alternative')
def test_mdns_discover(mock_alternative, mock_library, mdns_discovery):
    """Test mDNS device discovery."""
    # Simulate found devices
    mock_library.return_value = [{
        'name': 'mDNS Camera 1',
        'ip': '192.168.1.107',
        'port': 80,
        'type': 'video',
        'protocol': 'rtsp'
    }]

    mock_alternative.return_value = [{
        'name': 'mDNS Camera 2',
        'ip': '192.168.1.108',
        'port': 80,
        'type': 'video',
        'protocol': 'rtsp'
    }]

    # Test with working library
    with patch('importlib.import_module', return_value=MagicMock()):
        devices = mdns_discovery.discover()

        # Check if devices were discovered
        assert len(devices) == 1
        assert devices[0]['name'] == 'mDNS Camera 1'
        mock_library.assert_called_once()
        mock_alternative.assert_not_called()

    # Reset mocks
    mock_library.reset_mock()
    mock_alternative.reset_mock()

    # Test without library
    with patch('importlib.import_module', side_effect=ImportError):
        devices = mdns_discovery.discover()

        # Check if devices were discovered
        assert len(devices) == 1
        assert devices[0]['name'] == 'mDNS Camera 2'
        mock_library.assert_not_called()
        mock_alternative.assert_called_once()

@patch('socket.socket')
def test_mdns_discover_alternative(mock_socket, mdns_discovery):
    """Test alternative mDNS device discovery."""
    # Simulate socket response
    mock_socket_instance = MagicMock()
    mock_socket.return_value = mock_socket_instance

    # Simulate receiving data
    mock_socket_instance.recvfrom.side_effect = [(b'dummy_data', ('192.168.1.109', 5353)), socket.timeout()]

    # Call method
    devices = mdns_discovery._discover_alternative()

    # Check if devices were discovered
    assert len(devices) == 1
    assert devices[0]['ip'] == '192.168.1.109'
    assert devices[0]['port'] == 80  # Default port
    assert devices[0]['protocol'] == 'http'  # Default protocol
