"""
test_streaming.py
"""

# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rtaspi - Real-Time Annotation and Stream Processing
Testy jednostkowe dla modułów streamingu
"""

import os
import unittest
import tempfile
from unittest.mock import patch, MagicMock

import sys


from rtaspi.streaming.rtsp import RTSPServer
from rtaspi.streaming.rtmp import RTMPServer
from rtaspi.streaming.webrtc import WebRTCServer
from rtaspi.device_managers.utils.device import LocalDevice, NetworkDevice


class TestRTSPServer(unittest.TestCase):
    """Testy jednostkowe dla serwera RTSP."""

    def setUp(self):
        """Konfiguracja przed każdym testem."""
        self.temp_dir = tempfile.TemporaryDirectory()

        # Konfiguracja testowa
        self.config = {
            'system': {
                'storage_path': self.temp_dir.name
            },
            'streaming': {
                'rtsp': {
                    'port_start': 8554
                }
            }
        }

        # Utwórz serwer RTSP
        self.server = RTSPServer(self.config)

    def tearDown(self):
        """Czyszczenie po każdym teście."""
        self.temp_dir.cleanup()

    @patch('subprocess.Popen')
    @patch('time.sleep')
    @patch('socket.socket')
    def test_start_stream_local_device(self, mock_socket, mock_sleep, mock_popen):
        """Test uruchamiania strumienia RTSP z lokalnego urządzenia."""
        # Symulacja wolnego portu
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance
        mock_socket_instance.connect_ex.return_value = 1  # Port wolny

        # Symulacja procesu FFmpeg
        mock_process = MagicMock()
        mock_popen.return_value = mock_process
        mock_process.poll.return_value = None  # Proces działa

        # Utwórz przykładowe urządzenie
        device = LocalDevice(
            device_id='video:test',
            name='Test Camera',
            type='video',
            system_path='/dev/video0',
            driver='v4l2'
        )

        # Mock metod
        with patch('platform.system', return_value='Linux'):
            # Uruchomienie strumienia
            url = self.server.start_stream(device, 'test_stream', self.temp_dir.name)

            # Sprawdzenie, czy strumień został uruchomiony
            self.assertIsNotNone(url)
            self.assertTrue(url.startswith('rtsp://localhost:'))
            mock_popen.assert_called_once()

    @patch('subprocess.Popen')
    @patch('time.sleep')
    @patch('socket.socket')
    def test_proxy_stream_network_device(self, mock_socket, mock_sleep, mock_popen):
        """Test uruchamiania proxy RTSP dla zdalnego urządzenia."""
        # Symulacja wolnego portu
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance
        mock_socket_instance.connect_ex.return_value = 1  # Port wolny

        # Symulacja procesu FFmpeg
        mock_process = MagicMock()
        mock_popen.return_value = mock_process
        mock_process.poll.return_value = None  # Proces działa

        # Utwórz przykładowe urządzenie
        device = NetworkDevice(
            device_id='network:test',
            name='Test IP Camera',
            type='video',
            ip='192.168.1.100',
            port=554,
            protocol='rtsp'
        )

        # Utwórz źródłowy URL
        source_url = 'rtsp://192.168.1.100:554/stream1'

        # Uruchomienie proxy strumienia
        url = self.server.proxy_stream(device, 'test_stream', source_url, self.temp_dir.name, transcode=True)

        # Sprawdzenie, czy proxy został uruchomiony
        self.assertIsNotNone(url)
        self.assertTrue(url.startswith('rtsp://localhost:'))
        mock_popen.assert_called_once()

    def test_prepare_input_args(self):
        """Test przygotowania argumentów wejściowych dla FFmpeg."""
        # Testowe urządzenia
        video_device = LocalDevice(
            device_id='video:test',
            name='Test Camera',
            type='video',
            system_path='/dev/video0',
            driver='v4l2'
        )

        audio_device = LocalDevice(
            device_id='audio:test',
            name='Test Microphone',
            type='audio',
            system_path='hw:0,0',
            driver='alsa'
        )

        # Testowanie dla różnych platform
        with patch('platform.system', return_value='Linux'):
            # Wideo - Linux
            args = self.server._prepare_input_args(video_device)
            self.assertEqual(args, ['-f', 'v4l2', '-i', '/dev/video0'])

            # Audio - Linux
            args = self.server._prepare_input_args(audio_device)
            self.assertEqual(args, ['-f', 'alsa', '-i', 'hw:0,0'])

        with patch('platform.system', return_value='Darwin'):
            # Wideo - macOS
            video_device.driver = 'avfoundation'
            args = self.server._prepare_input_args(video_device)
            self.assertEqual(args, ['-f', 'avfoundation', '-framerate', '30', '-i', '/dev/video0:none'])

        with patch('platform.system', return_value='Windows'):
            # Wideo - Windows
            video_device.driver = 'dshow'
            args = self.server._prepare_input_args(video_device)
            self.assertEqual(args, ['-f', 'dshow', '-i', 'video=/dev/video0'])

    def test_prepare_output_args(self):
        """Test przygotowania argumentów wyjściowych dla FFmpeg."""
        # Testowe urządzenia
        video_device = LocalDevice(
            device_id='video:test',
            name='Test Camera',
            type='video',
            system_path='/dev/video0',
            driver='v4l2'
        )

        audio_device = LocalDevice(
            device_id='audio:test',
            name='Test Microphone',
            type='audio',
            system_path='hw:0,0',
            driver='alsa'
        )

        # Testowanie dla różnych typów urządzeń
        # Wideo
        args = self.server._prepare_output_args(video_device, 8554, 'test_stream')
        self.assertEqual(args, [
            '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'zerolatency',
            '-f', 'rtsp', 'rtsp://localhost:8554/test_stream'
        ])

        # Audio
        args = self.server._prepare_output_args(audio_device, 8554, 'test_stream')
        self.assertEqual(args, [
            '-c:a', 'aac', '-b:a', '128k',
            '-f', 'rtsp', 'rtsp://localhost:8554/test_stream'
        ])


class TestRTMPServer(unittest.TestCase):
    """Testy jednostkowe dla serwera RTMP."""

    def setUp(self):
        """Konfiguracja przed każdym testem."""
        self.temp_dir = tempfile.TemporaryDirectory()

        # Konfiguracja testowa
        self.config = {
            'system': {
                'storage_path': self.temp_dir.name
            },
            'streaming': {
                'rtmp': {
                    'port_start': 1935
                }
            }
        }

        # Utwórz serwer RTMP
        self.server = RTMPServer(self.config)

    def tearDown(self):
        """Czyszczenie po każdym teście."""
        self.temp_dir.cleanup()

    @patch('subprocess.Popen')
    @patch('time.sleep')
    @patch('socket.socket')
    def test_start_stream_local_device(self, mock_socket, mock_sleep, mock_popen):
        """Test uruchamiania strumienia RTMP z lokalnego urządzenia."""
        # Symulacja wolnego portu
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance
        mock_socket_instance.connect_ex.return_value = 1  # Port wolny

        # Symulacja procesów
        mock_popen.side_effect = [MagicMock(), MagicMock()]  # nginx, ffmpeg

        # Utwórz przykładowe urządzenie
        device = LocalDevice(
            device_id='video:test',
            name='Test Camera',
            type='video',
            system_path='/dev/video0',
            driver='v4l2'
        )

        # Mock metod
        with patch('platform.system', return_value='Linux'), \
                patch('builtins.open', MagicMock()):
            # Uruchomienie strumienia
            url = self.server.start_stream(device, 'test_stream', self.temp_dir.name)

            # Sprawdzenie, czy strumień został uruchomiony
            self.assertIsNotNone(url)
            self.assertTrue(url.startswith('rtmp://localhost:'))
            self.assertEqual(mock_popen.call_count, 2)

    def test_generate_nginx_config(self):
        """Test generowania konfiguracji NGINX."""
        # Generowanie konfiguracji
        config = self.server._generate_nginx_config(1935)

        # Sprawdzenie, czy konfiguracja zawiera wymagane elementy
        self.assertIn('worker_processes 1;', config)
        self.assertIn('listen 1935;', config)
        self.assertIn('application live', config)
        self.assertIn('live on;', config)


class TestWebRTCServer(unittest.TestCase):
    """Testy jednostkowe dla serwera WebRTC."""

    def setUp(self):
        """Konfiguracja przed każdym testem."""
        self.temp_dir = tempfile.TemporaryDirectory()

        # Konfiguracja testowa
        self.config = {
            'system': {
                'storage_path': self.temp_dir.name
            },
            'streaming': {
                'webrtc': {
                    'port_start': 8080,
                    'stun_server': 'stun://stun.l.google.com:19302',
                    'turn_server': '',
                    'turn_username': '',
                    'turn_password': ''
                }
            }
        }

        # Utwórz serwer WebRTC
        self.server = WebRTCServer(self.config)

    def tearDown(self):
        """Czyszczenie po każdym teście."""
        self.temp_dir.cleanup()

    @patch('subprocess.Popen')
    @patch('time.sleep')
    @patch('socket.socket')
    def test_start_stream_local_device(self, mock_socket, mock_sleep, mock_popen):
        """Test uruchamiania strumienia WebRTC z lokalnego urządzenia."""
        # Symulacja wolnego portu
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance
        mock_socket_instance.connect_ex.return_value = 1  # Port wolny

        # Symulacja procesów
        mock_popen.side_effect = [MagicMock(), MagicMock()]  # http server, gstreamer

        # Utwórz przykładowe urządzenie
        device = LocalDevice(
            device_id='video:test',
            name='Test Camera',
            type='video',
            system_path='/dev/video0',
            driver='v4l2'
        )

        # Mock metod
        with patch('platform.system', return_value='Linux'), \
                patch('builtins.open', MagicMock()), \
                patch('json.dump', MagicMock()):
            # Uruchomienie strumienia
            url = self.server.start_stream(device, 'test_stream', self.temp_dir.name)

            # Sprawdzenie, czy strumień został uruchomiony
            self.assertIsNotNone(url)
            self.assertTrue(url.startswith('http://localhost:'))
            self.assertEqual(mock_popen.call_count, 2)

    def test_prepare_input_pipeline(self):
        """Test przygotowania potoku wejściowego dla GStreamer."""
        # Testowe urządzenia
        video_device = LocalDevice(
            device_id='video:test',
            name='Test Camera',
            type='video',
            system_path='/dev/video0',
            driver='v4l2'
        )

        audio_device = LocalDevice(
            device_id='audio:test',
            name='Test Microphone',
            type='audio',
            system_path='hw:0,0',
            driver='alsa'
        )

        # Testowanie dla różnych platform
        with patch('platform.system', return_value='Linux'):
            # Wideo - Linux
            pipeline = self.server._prepare_input_pipeline(video_device)
            self.assertIn('v4l2src device=/dev/video0', pipeline)

            # Audio - Linux
            pipeline = self.server._prepare_input_pipeline(audio_device)
            self.assertIn('alsasrc device=hw:0,0', pipeline)

    def test_generate_webrtc_html(self):
        """Test generowania kodu HTML dla WebRTC."""
        # Generowanie HTML
        html = self.server._generate_webrtc_html('test_stream', 8080)

        # Sprawdzenie, czy HTML zawiera wymagane elementy
        self.assertIn('<!DOCTYPE html>', html)
        self.assertIn('test_stream', html)
        self.assertIn('8080', html)
        self.assertIn('stun.l.google.com:19302', html)
        self.assertIn('RTCPeerConnection', html)
        self.assertIn('createOffer', html)


if __name__ == '__main__':
    unittest.main()