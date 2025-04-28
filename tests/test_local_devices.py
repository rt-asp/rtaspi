"""
test_local_devices.py
"""

# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rtaspi - Real-Time Annotation and Stream Processing
Testy jednostkowe dla menedżera lokalnych urządzeń
"""

import os
import unittest
import tempfile
import json
from unittest.mock import patch, MagicMock, call

import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.mcp import MCPBroker
from device_managers.local_devices import LocalDevicesManager
from device_managers.utils.device import LocalDevice


class TestLocalDevicesManager(unittest.TestCase):
    """Testy jednostkowe dla menedżera lokalnych urządzeń."""

    def setUp(self):
        """Konfiguracja przed każdym testem."""
        self.temp_dir = tempfile.TemporaryDirectory()

        # Konfiguracja testowa
        self.config = {
            'system': {
                'storage_path': self.temp_dir.name
            },
            'local_devices': {
                'enable_video': True,
                'enable_audio': True,
                'auto_start': False,
                'scan_interval': 1,  # Krótki interwał dla testów
                'rtsp_port_start': 8554,
                'rtmp_port_start': 1935,
                'webrtc_port_start': 8080
            }
        }

        # Mock brokera MCP
        self.mcp_broker = MCPBroker()

        # Tworzymy menedżera lokalnych urządzeń
        with patch('device_managers.local_devices.RTSPServer'), \
                patch('device_managers.local_devices.RTMPServer'), \
                patch('device_managers.local_devices.WebRTCServer'):
            self.manager = LocalDevicesManager(self.config, self.mcp_broker)

    def tearDown(self):
        """Czyszczenie po każdym teście."""
        self.temp_dir.cleanup()

    @patch('device_managers.local_devices.LocalDevicesManager._scan_video_devices')
    @patch('device_managers.local_devices.LocalDevicesManager._scan_audio_devices')
    def test_scan_devices(self, mock_scan_audio, mock_scan_video):
        """Test skanowania urządzeń."""
        # Wywołanie metody skanowania
        self.manager._scan_devices()

        # Sprawdzenie, czy metody skanowania zostały wywołane
        mock_scan_video.assert_called_once()
        mock_scan_audio.assert_called_once()

    @patch('subprocess.check_output')
    def test_scan_linux_video_devices(self, mock_check_output):
        """Test skanowania urządzeń wideo w systemie Linux."""
        # Symulacja wyjścia komendy v4l2-ctl
        mock_check_output.side_effect = [
            # Wyjście dla --all
            'Card type       : Test Camera\nDriver name     : v4l2',
            # Wyjście dla --list-formats-ext
            'PixelFormat : \'YUYV\'\nSize: Discrete 640x480'
        ]

        with patch('platform.system', return_value='Linux'), \
                patch('pathlib.Path.glob', return_value=['/dev/video0']):
            self.manager._scan_linux_video_devices()

        # Sprawdzenie, czy urządzenie zostało dodane
        self.assertEqual(len(self.manager.devices['video']), 1)
        device_id = list(self.manager.devices['video'].keys())[0]
        self.assertEqual(device_id, 'video:/dev/video0')
        self.assertEqual(self.manager.devices['video'][device_id].name, 'Test Camera')
        self.assertEqual(self.manager.devices['video'][device_id].formats, ['YUYV'])
        self.assertEqual(self.manager.devices['video'][device_id].resolutions, ['640x480'])

    @patch('subprocess.check_output')
    def test_scan_linux_audio_devices(self, mock_check_output):
        """Test skanowania urządzeń audio w systemie Linux."""
        # Symulacja wyjścia komendy arecord i pactl
        mock_check_output.side_effect = [
            # Wyjście dla arecord -l
            'card 0: Test [Test Sound Card], device 0: Test PCM [Test PCM]\n',
            # Wyjście dla pactl list sources
            'Source #0\n  Name: test.monitor\n  Description: Test Monitor\n'
        ]

        with patch('platform.system', return_value='Linux'):
            self.manager._scan_linux_audio_devices()

        # Sprawdzenie, czy urządzenia zostały dodane
        self.assertGreaterEqual(len(self.manager.devices['audio']), 2)
        alsa_device = next((dev for dev in self.manager.devices['audio'].values() if dev.driver == 'alsa'), None)
        pulse_device = next((dev for dev in self.manager.devices['audio'].values() if dev.driver == 'pulse'), None)

        self.assertIsNotNone(alsa_device)
        self.assertIsNotNone(pulse_device)
        self.assertTrue('Sound Card' in alsa_device.name)
        self.assertTrue('Test Monitor' in pulse_device.name)

    @patch('device_managers.local_devices.RTSPServer.start_stream')
    def test_start_stream(self, mock_start_stream):
        """Test uruchamiania strumienia."""
        # Utwórz przykładowe urządzenie
        device = LocalDevice(
            device_id='video:test',
            name='Test Camera',
            type='video',
            system_path='/dev/video0',
            driver='v4l2'
        )
        self.manager.devices['video']['video:test'] = device

        # Symulacja odpowiedzi serwera RTSP
        mock_start_stream.return_value = 'rtsp://localhost:8554/test'

        # Uruchomienie strumienia
        url = self.manager.start_stream('video:test', protocol='rtsp')

        # Sprawdzenie, czy strumień został uruchomiony
        self.assertEqual(url, 'rtsp://localhost:8554/test')
        mock_start_stream.assert_called_once()

    def test_auto_start_streams(self):
        """Test automatycznego uruchamiania strumieni."""
        # Utwórz przykładowe urządzenia
        device1 = LocalDevice(
            device_id='video:test1',
            name='Test Camera 1',
            type='video',
            system_path='/dev/video0',
            driver='v4l2'
        )
        device2 = LocalDevice(
            device_id='audio:test1',
            name='Test Mic 1',
            type='audio',
            system_path='hw:0,0',
            driver='alsa'
        )
        self.manager.devices['video']['video:test1'] = device1
        self.manager.devices['audio']['audio:test1'] = device2

        # Włącz automatyczne uruchamianie
        self.manager.auto_start = True

        # Mock metody start_stream
        self.manager.start_stream = MagicMock(return_value='rtsp://localhost:8554/test')

        # Wywołanie auto_start_streams
        self.manager._auto_start_streams()

        # Sprawdzenie, czy strumienie zostały uruchomione
        self.assertEqual(self.manager.start_stream.call_count, 2)
        self.manager.start_stream.assert_has_calls([
            call('video:test1', protocol='rtsp'),
            call('audio:test1', protocol='rtsp')
        ], any_order=True)

    def test_handle_command(self):
        """Test obsługi komend MCP."""
        # Utwórz przykładowe urządzenie
        device = LocalDevice(
            device_id='video:test',
            name='Test Camera',
            type='video',
            system_path='/dev/video0',
            driver='v4l2'
        )
        self.manager.devices['video']['video:test'] = device

        # Mock metod
        self.manager._scan_devices = MagicMock()
        self.manager.start_stream = MagicMock(return_value='rtsp://localhost:8554/test')
        self.manager.stop_stream = MagicMock(return_value=True)
        self.manager.mcp_client.publish = MagicMock()

        # Test komendy scan
        self.manager._handle_command('command/local_devices/scan', {})
        self.manager._scan_devices.assert_called_once()

        # Test komendy start_stream
        self.manager._handle_command('command/local_devices/start_stream', {
            'device_id': 'video:test',
            'protocol': 'rtsp'
        })
        self.manager.start_stream.assert_called_with('video:test', 'rtsp')

        # Test komendy stop_stream
        self.manager._handle_command('command/local_devices/stop_stream', {
            'stream_id': 'test_stream'
        })
        self.manager.stop_stream.assert_called_with('test_stream')

        # Test komendy get_devices
        self.manager._handle_command('command/local_devices/get_devices', {})
        self.manager.mcp_client.publish.assert_called()

    def test_stop_stream(self):
        """Test zatrzymywania strumienia."""
        # Utwórz przykładowy strumień
        mock_process = MagicMock()
        self.manager.streams['test_stream'] = {
            'process': mock_process,
            'device_id': 'video:test',
            'type': 'video',
            'url': 'rtsp://localhost:8554/test',
            'protocol': 'rtsp',
            'port': 8554
        }

        # Mock metody
        self.manager._publish_stream_stopped = MagicMock()

        # Zatrzymanie strumienia
        result = self.manager.stop_stream('test_stream')

        # Sprawdzenie, czy strumień został zatrzymany
        self.assertTrue(result)
        mock_process.terminate.assert_called_once()
        self.manager._publish_stream_stopped.assert_called_once()
        self.assertNotIn('test_stream', self.manager.streams)


if __name__ == '__main__':
    unittest.main()