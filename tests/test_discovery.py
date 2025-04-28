"""
test_discovery.py
"""

# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rtaspi - Real-Time Annotation and Stream Processing
Testy jednostkowe dla modułów wykrywania urządzeń
"""

import os
import unittest
from unittest.mock import patch, MagicMock

import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from device_managers.utils.discovery import ONVIFDiscovery, UPnPDiscovery, MDNSDiscovery


class TestONVIFDiscovery(unittest.TestCase):
    """Testy jednostkowe dla modułu wykrywania ONVIF."""

    def setUp(self):
        """Konfiguracja przed każdym testem."""
        self.discovery = ONVIFDiscovery()

    @patch('device_managers.utils.discovery.ONVIFDiscovery._discover_with_library')
    @patch('device_managers.utils.discovery.ONVIFDiscovery._discover_alternative')
    def test_discover(self, mock_alternative, mock_library):
        """Test wykrywania urządzeń ONVIF."""
        # Symulacja znalezionych urządzeń
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

        # Test z działającą biblioteką
        with patch('importlib.import_module', return_value=MagicMock()):
            devices = self.discovery.discover()

            # Sprawdzenie, czy wykryto urządzenia
            self.assertEqual(len(devices), 1)
            self.assertEqual(devices[0]['name'], 'ONVIF Camera 1')
            mock_library.assert_called_once()
            mock_alternative.assert_not_called()

        # Reset mocków
        mock_library.reset_mock()
        mock_alternative.reset_mock()

        # Test bez biblioteki
        with patch('importlib.import_module', side_effect=ImportError):
            devices = self.discovery.discover()

            # Sprawdzenie, czy wykryto urządzenia
            self.assertEqual(len(devices), 1)
            self.assertEqual(devices[0]['name'], 'ONVIF Camera 2')
            mock_library.assert_not_called()
            mock_alternative.assert_called_once()

    @patch('socket.socket')
    def test_discover_alternative(self, mock_socket):
        """Test alternatywnego wykrywania urządzeń ONVIF."""
        # Symulacja odpowiedzi socketa
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance

        # Symulacja odbierania danych
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

        # Wywołanie metody
        devices = self.discovery._discover_alternative()

        # Sprawdzenie, czy wykryto urządzenia
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]['ip'], '192.168.1.103')
        self.assertEqual(devices[0]['port'], 80)
        self.assertEqual(devices[0]['protocol'], 'rtsp')


class TestUPnPDiscovery(unittest.TestCase):
    """Testy jednostkowe dla modułu wykrywania UPnP."""

    def setUp(self):
        """Konfiguracja przed każdym testem."""
        self.discovery = UPnPDiscovery()

    @patch('device_managers.utils.discovery.UPnPDiscovery._discover_with_library')
    @patch('device_managers.utils.discovery.UPnPDiscovery._discover_alternative')
    def test_discover(self, mock_alternative, mock_library):
        """Test wykrywania urządzeń UPnP."""
        # Symulacja znalezionych urządzeń
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

        # Test z działającą biblioteką
        with patch('importlib.import_module', return_value=MagicMock()):
            devices = self.discovery.discover()

            # Sprawdzenie, czy wykryto urządzenia
            self.assertEqual(len(devices), 1)
            self.assertEqual(devices[0]['name'], 'UPnP Camera 1')
            mock_library.assert_called_once()
            mock_alternative.assert_not_called()

        # Reset mocków
        mock_library.reset_mock()
        mock_alternative.reset_mock()

        # Test bez biblioteki
        with patch('importlib.import_module', side_effect=ImportError):
            devices = self.discovery.discover()

            # Sprawdzenie, czy wykryto urządzenia
            self.assertEqual(len(devices), 1)
            self.assertEqual(devices[0]['name'], 'UPnP Camera 2')
            mock_library.assert_not_called()
            mock_alternative.assert_called_once()

    @patch('socket.socket')
    def test_discover_alternative(self, mock_socket):
        """Test alternatywnego wykrywania urządzeń UPnP."""
        # Symulacja odpowiedzi socketa
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance

        # Symulacja odbierania danych
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

        # Wywołanie metody
        devices = self.discovery._discover_alternative()

        # Sprawdzenie, czy wykryto urządzenia
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]['ip'], '192.168.1.106')
        self.assertEqual(devices[0]['port'], 80)
        self.assertEqual(devices[0]['protocol'], 'http')


class TestMDNSDiscovery(unittest.TestCase):
    """Testy jednostkowe dla modułu wykrywania mDNS."""

    def setUp(self):
        """Konfiguracja przed każdym testem."""
        self.discovery = MDNSDiscovery()

    @patch('device_managers.utils.discovery.MDNSDiscovery._discover_with_library')
    @patch('device_managers.utils.discovery.MDNSDiscovery._discover_alternative')
    def test_discover(self, mock_alternative, mock_library):
        """Test wykrywania urządzeń mDNS."""
        # Symulacja znalezionych urządzeń
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

        # Test z działającą biblioteką
        with patch('importlib.import_module', return_value=MagicMock()):
            devices = self.discovery.discover()

            # Sprawdzenie, czy wykryto urządzenia
            self.assertEqual(len(devices), 1)
            self.assertEqual(devices[0]['name'], 'mDNS Camera 1')
            mock_library.assert_called_once()
            mock_alternative.assert_not_called()

        # Reset mocków
        mock_library.reset_mock()
        mock_alternative.reset_mock()

        # Test bez biblioteki
        with patch('importlib.import_module', side_effect=ImportError):
            devices = self.discovery.discover()

            # Sprawdzenie, czy wykryto urządzenia
            self.assertEqual(len(devices), 1)
            self.assertEqual(devices[0]['name'], 'mDNS Camera 2')
            mock_library.assert_not_called()
            mock_alternative.assert_called_once()

    @patch('socket.socket')
    def test_discover_alternative(self, mock_socket):
        """Test alternatywnego wykrywania urządzeń mDNS."""
        # Symulacja odpowiedzi socketa
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance

        # Symulacja odbierania danych
        mock_socket_instance.recvfrom.side_effect = [(b'dummy_data', ('192.168.1.109', 5353)), socket.timeout()]

        # Wywołanie metody
        devices = self.discovery._discover_alternative()

        # Sprawdzenie, czy wykryto urządzenia
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]['ip'], '192.168.1.109')
        self.assertEqual(devices[0]['port'], 80)  # Domyślny port
        self.assertEqual(devices[0]['protocol'], 'http')  # Domyślny protokół


if __name__ == '__main__':
    unittest.main()