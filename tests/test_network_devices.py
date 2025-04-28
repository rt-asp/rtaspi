"""
test_network_devices.py
"""

# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rtaspi - Real-Time Annotation and Stream Processing
Testy jednostkowe dla menedżera zdalnych urządzeń
"""

import os
import unittest
import tempfile
import json
from unittest.mock import patch, MagicMock, call

import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.mcp import MCPBroker
from device_managers.network_devices import NetworkDevicesManager
from device_managers.utils.device import NetworkDevice


class TestNetworkDevicesManager(unittest.TestCase):
    """Testy jednostkowe dla menedżera zdalnych urządzeń."""

    def setUp(self):
        """Konfiguracja przed każdym testem."""
        self.temp_dir = tempfile.TemporaryDirectory()

        # Konfiguracja testowa
        self.config = {
            'system': {
                'storage_path': self.temp_dir.name
            },
            'network_devices': {
                'enable': True,
                'scan_interval': 1,  # Krótki interwał dla testów
                'discovery_enabled': True,
                'discovery_methods': ['onvif', 'upnp', 'mdns'],
                'rtsp_port_start': 8654,
                'rtmp_port_start': 2935,
                'webrtc_port_start': 9080
            }
        }

        # Mock brokera MCP
        self.mcp_broker = MCPBroker()

        # Mock modułów wykrywania
        with patch('device_managers.network_devices.ONVIFDiscovery'), \
                patch('device_managers.network_devices.UPnPDiscovery'), \
                patch('device_managers.network_devices.MDNSDiscovery'), \
                patch('device_managers.network_devices.RTSPServer'), \
                patch('device_managers.network_devices.RTMPServer'), \
                patch('device_managers.network_devices.WebRTCServer'):
            self.manager = NetworkDevicesManager(self.config, self.mcp_broker)

    def tearDown(self):
        """Czyszczenie po każdym teście."""
        self.temp_dir.cleanup()

    def test_add_device(self):
        """Test dodawania urządzenia."""
        # Mock metod
        self.manager._check_device_status = MagicMock()
        self.manager._save_devices = MagicMock()
        self.manager.mcp_client.publish = MagicMock()

        # Dodanie urządzenia
        device_id = self.manager.add_device(
            name='Test Camera',
            ip='192.168.1.100',
            port=554,
            username='admin',
            password='admin',
            type='video',
            protocol='rtsp',
            paths=['cam/realmonitor']
        )

        # Sprawdzenie, czy urządzenie zostało dodane
        self.assertIsNotNone(device_id)
        self.assertIn(device_id, self.manager.devices)
        device = self.manager.devices[device_id]
        self.assertEqual(device.name, 'Test Camera')
        self.assertEqual(device.ip, '192.168.1.100')
        self.assertEqual(device.port, 554)
        self.assertEqual(device.username, 'admin')
        self.assertEqual(device.password, 'admin')
        self.assertEqual(device.type, 'video')
        self.assertEqual(device.protocol, 'rtsp')
        self.assertEqual(len(device.streams), 1)

        # Sprawdzenie, czy metody zostały wywołane
        self.manager._check_device_status.assert_called_once()
        self.manager._save_devices.assert_called_once()
        self.manager.mcp_client.publish.assert_called_once()

    def test_remove_device(self):
        """Test usuwania urządzenia."""
        # Dodanie przykładowego urządzenia
        device = NetworkDevice(
            device_id='test_device',
            name='Test Camera',
            type='video',
            ip='192.168.1.100',
            port=554,
            username='admin',
            password='admin',
            protocol='rtsp'
        )
        self.manager.devices['test_device'] = device

        # Mock metod
        self.manager._save_devices = MagicMock()
        self.manager.mcp_client.publish = MagicMock()

        # Usunięcie urządzenia
        result = self.manager.remove_device('test_device')

        # Sprawdzenie, czy urządzenie zostało usunięte
        self.assertTrue(result)
        self.assertNotIn('test_device', self.manager.devices)

        # Sprawdzenie, czy metody zostały wywołane
        self.manager._save_devices.assert_called_once()
        self.manager.mcp_client.publish.assert_called_once()

    @patch('socket.socket')
    def test_check_device_status(self, mock_socket):
        """Test sprawdzania stanu urządzenia."""
        # Utwórz przykładowe urządzenie
        device = NetworkDevice(
            device_id='test_device',
            name='Test Camera',
            type='video',
            ip='192.168.1.100',
            port=554,
            protocol='rtsp'
        )

        # Symulacja odpowiedzi socketa
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance
        mock_socket_instance.connect_ex.return_value = 0  # Port otwarty

        # Sprawdzenie stanu urządzenia
        self.manager._check_device_status(device)

        # Sprawdzenie, czy stan został zaktualizowany
        self.assertEqual(device.status, 'online')

        # Zmiana symulacji - port zamknięty
        mock_socket_instance.connect_ex.return_value = 1

        # Ponowne sprawdzenie stanu urządzenia
        device.last_check = 0  # Reset czasu ostatniego sprawdzenia
        self.manager._check_device_status(device)

        # Sprawdzenie, czy stan został zaktualizowany
        self.assertEqual(device.status, 'offline')

    def test_discover_devices(self):
        """Test wykrywania urządzeń."""
        # Mock modułów wykrywania
        onvif_module = MagicMock()
        upnp_module = MagicMock()
        mdns_module = MagicMock()

        # Symulacja znalezionych urządzeń
        onvif_module.discover.return_value = [{
            'name': 'ONVIF Camera',
            'ip': '192.168.1.101',
            'port': 80,
            'type': 'video',
            'protocol': 'rtsp',
            'paths': ['onvif1']
        }]

        upnp_module.discover.return_value = [{
            'name': 'UPnP Camera',
            'ip': '192.168.1.102',
            'port': 80,
            'type': 'video',
            'protocol': 'http'
        }]

        mdns_module.discover.return_value = [{
            'name': 'mDNS Camera',
            'ip': '192.168.1.103',
            'port': 80,
            'type': 'video',
            'protocol': 'rtsp'
        }]

        # Podmiana modułów wykrywania
        self.manager.discovery_modules = {
            'onvif': onvif_module,
            'upnp': upnp_module,
            'mdns': mdns_module
        }

        # Mock metody add_device
        self.manager.add_device = MagicMock(return_value='new_device_id')

        # Wykrywanie urządzeń
        self.manager._discover_devices()

        # Sprawdzenie, czy metody zostały wywołane
        onvif_module.discover.assert_called_once()
        upnp_module.discover.assert_called_once()
        mdns_module.discover.assert_called_once()

        # Sprawdzenie, czy urządzenia zostały dodane
        self.assertEqual(self.manager.add_device.call_count, 3)

    @patch('device_managers.network_devices.RTSPServer.proxy_stream')
    def test_start_stream(self, mock_proxy_stream):
        """Test uruchamiania strumienia."""
        # Utwórz przykładowe urządzenie
        device = NetworkDevice(
            device_id='test_device',
            name='Test Camera',
            type='video',
            ip='192.168.1.100',
            port=554,
            protocol='rtsp'
        )
        device.streams = {'stream1': 'rtsp://192.168.1.100:554/stream1'}
        self.manager.devices['test_device'] = device

        # Symulacja odpowiedzi serwera RTSP
        mock_proxy_stream.return_value = 'rtsp://localhost:8654/test'

        # Uruchomienie strumienia
        url = self.manager.start_stream('test_device', protocol='rtsp', transcode=True)

        # Sprawdzenie, czy strumień został uruchomiony
        self.assertEqual(url, 'rtsp://localhost:8654/test')
        mock_proxy_stream.assert_called_once()

        # Test bezpośredniego strumienia (bez proxy)
        mock_proxy_stream.reset_mock()
        url = self.manager.start_stream('test_device')

        # Sprawdzenie, czy strumień został uruchomiony
        self.assertEqual(url, 'rtsp://192.168.1.100:554/stream1')
        mock_proxy_stream.assert_not_called()

    def test_handle_command(self):
        """Test obsługi komend MCP."""
        # Utwórz przykładowe urządzenie
        device = NetworkDevice(
            device_id='test_device',
            name='Test Camera',
            type='video',
            ip='192.168.1.100',
            port=554,
            protocol='rtsp'
        )
        self.manager.devices['test_device'] = device

        # Mock metod
        self.manager._scan_devices = MagicMock()
        self.manager._discover_devices = MagicMock()
        self.manager.add_device = MagicMock(return_value='new_device_id')
        self.manager.remove_device = MagicMock(return_value=True)
        self.manager.start_stream = MagicMock(return_value='rtsp://localhost:8654/test')
        self.manager.stop_stream = MagicMock(return_value=True)
        self.manager.mcp_client.publish = MagicMock()

        # Test komendy scan
        self.manager._handle_command('command/network_devices/scan', {})
        self.manager._scan_devices.assert_called_once()

        # Test komendy discover
        self.manager._handle_command('command/network_devices/discover', {})
        self.manager._discover_devices.assert_called_once()

        # Test komendy add_device
        self.manager._handle_command('command/network_devices/add_device', {
            'name': 'New Camera',
            'ip': '192.168.1.200',
            'port': 554,
            'type': 'video',
            'protocol': 'rtsp'
        })
        self.manager.add_device.assert_called_once()

        # Test komendy remove_device
        self.manager._handle_command('command/network_devices/remove_device', {
            'device_id': 'test_device'
        })
        self.manager.remove_device.assert_called_with('test_device')

        # Test komendy start_stream
        self.manager._handle_command('command/network_devices/start_stream', {
            'device_id': 'test_device',
            'protocol': 'rtsp',
            'transcode': True
        })
        self.manager.start_stream.assert_called_with(
            device_id='test_device',
            stream_path=None,
            protocol='rtsp',
            transcode=True
        )

        # Test komendy stop_stream
        self.manager._handle_command('command/network_devices/stop_stream', {
            'stream_id': 'test_stream'
        })
        self.manager.stop_stream.assert_called_with('test_stream')

    def test_load_save_devices(self):
        """Test ładowania i zapisywania urządzeń."""
        # Utwórz przykładowe urządzenie
        device = NetworkDevice(
            device_id='test_device',
            name='Test Camera',
            type='video',
            ip='192.168.1.100',
            port=554,
            username='admin',
            password='admin',
            protocol='rtsp'
        )
        device.streams = {'stream1': 'rtsp://192.168.1.100:554/stream1'}

        # Dodanie urządzenia do menedżera
        self.manager.devices['test_device'] = device

        # Zapisanie urządzeń
        self.manager._save_devices()

        # Utworzenie nowego menedżera, który powinien załadować zapisane urządzenia
        with patch('device_managers.network_devices.ONVIFDiscovery'), \
                patch('device_managers.network_devices.UPnPDiscovery'), \
                patch('device_managers.network_devices.MDNSDiscovery'), \
                patch('device_managers.network_devices.RTSPServer'), \
                patch('device_managers.network_devices.RTMPServer'), \
                patch('device_managers.network_devices.WebRTCServer'):
            new_manager = NetworkDevicesManager(self.config, self.mcp_broker)

        # Sprawdzenie, czy urządzenie zostało załadowane
        self.assertIn('test_device', new_manager.devices)
        loaded_device = new_manager.devices['test_device']
        self.assertEqual(loaded_device.name, 'Test Camera')
        self.assertEqual(loaded_device.ip, '192.168.1.100')
        self.assertEqual(loaded_device.port, 554)
        self.assertEqual(loaded_device.username, 'admin')
        self.assertEqual(loaded_device.password, 'admin')
        self.assertEqual(loaded_device.type, 'video')
        self.assertEqual(loaded_device.protocol, 'rtsp')
        self.assertIn('stream1', loaded_device.streams)

    def test_stop_stream(self):
        """Test zatrzymywania strumienia."""
        # Utwórz przykładowy strumień bezpośredni
        self.manager.streams['direct_stream'] = {
            'device_id': 'test_device',
            'url': 'rtsp://192.168.1.100:554/stream1',
            'source_url': 'rtsp://192.168.1.100:554/stream1',
            'protocol': 'rtsp',
            'direct': True
        }

        # Utwórz przykładowy strumień proxy
        mock_process = MagicMock()
        mock_rtsp_process = MagicMock()
        self.manager.streams['proxy_stream'] = {
            'process': mock_process,
            'rtsp_process': mock_rtsp_process,
            'device_id': 'test_device',
            'url': 'rtsp://localhost:8654/test',
            'source_url': 'rtsp://192.168.1.100:554/stream1',
            'protocol': 'rtsp',
            'port': 8654
        }

        # Mock metody
        self.manager._publish_stream_stopped = MagicMock()

        # Zatrzymanie strumienia bezpośredniego
        result1 = self.manager.stop_stream('direct_stream')

        # Sprawdzenie, czy strumień został zatrzymany
        self.assertTrue(result1)
        self.assertNotIn('direct_stream', self.manager.streams)
        self.manager._publish_stream_stopped.assert_called_once()

        # Reset mocka
        self.manager._publish_stream_stopped.reset_mock()

        # Zatrzymanie strumienia proxy
        result2 = self.manager.stop_stream('proxy_stream')

        # Sprawdzenie, czy strumień został zatrzymany
        self.assertTrue(result2)
        mock_process.terminate.assert_called_once()
        mock_rtsp_process.terminate.assert_called_once()
        self.assertNotIn('proxy_stream', self.manager.streams)
        self.manager._publish_stream_stopped.assert_called_once()


if __name__ == '__main__':
    unittest.main()