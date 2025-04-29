#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rtaspi - Real-Time Annotation and Stream Processing
Obsługa protokołu RTMP
"""

import os
import logging
import subprocess
import shlex
import time
import socket
import uuid
from pathlib import Path

logger = logging.getLogger("RTMP")


class RTMPServer:
    """Klasa do obsługi streamingu RTMP."""

    def __init__(self, config):
        """
        Inicjalizacja serwera RTMP.

        Args:
            config (dict): Konfiguracja serwera.
        """
        self.config = config

        # Pobranie konfiguracji z pliku
        streaming_config = config.get('streaming', {}).get('rtmp', {})
        self.port_start = streaming_config.get('port_start', 1935)
        self.storage_path = config.get('system', {}).get('storage_path', 'storage')

    def start_stream(self, device, stream_id, output_dir):
        """
        Uruchamia strumień RTMP z lokalnego urządzenia.

        Args:
            device: Obiekt urządzenia.
            stream_id (str): Identyfikator strumienia.
            output_dir (str): Katalog wyjściowy.

        Returns:
            str: URL do strumienia RTMP lub None w przypadku błędu.
        """
        try:
            # Wybór wolnego portu
            port = self._find_free_port(self.port_start)

            # Przygotowanie komend FFmpeg w zależności od systemu i typu urządzenia
            input_args = self._prepare_input_args(device)
            output_args = self._prepare_output_args(device, port, stream_id)

            if not input_args or not output_args:
                logger.error(f"Nie można przygotować argumentów FFmpeg dla urządzenia {device.device_id}")
                return None

            # Uruchomienie serwera RTMP (nginx z modułem RTMP)
            nginx_config_path = os.path.join(output_dir, 'nginx.conf')
            with open(nginx_config_path, 'w') as f:
                f.write(self._generate_nginx_config(port))

            # Uruchomienie nginx z konfiguracją RTMP
            nginx_process = subprocess.Popen(
                ['nginx', '-c', nginx_config_path, '-p', output_dir],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            # Krótkie oczekiwanie na uruchomienie serwera RTMP
            time.sleep(2)

            # Uruchomienie procesu FFmpeg
            cmd = ['ffmpeg', '-hide_banner'] + input_args + output_args
            logger.debug(f"Uruchamianie komendy: {' '.join(cmd)}")

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            # Krótkie oczekiwanie, aby sprawdzić, czy proces się uruchomił
            time.sleep(2)
            if process.poll() is not None:
                logger.error(f"Proces FFmpeg zakończył działanie z kodem: {process.returncode}")
                nginx_process.terminate()
                return None

            # Dodanie procesu do informacji o strumieniu
            url = f"rtmp://localhost:{port}/live/{stream_id}"
            stream_info = {
                "process": process,
                "nginx_process": nginx_process,
                "device_id": device.device_id,
                "type": device.type,
                "url": url,
                "protocol": "rtmp",
                "port": port
            }

            return url

        except Exception as e:
            logger.error(f"Błąd podczas uruchamiania strumienia RTMP: {e}")
            return None

    def proxy_stream(self, device, stream_id, source_url, output_dir, transcode=False):
        """
        Uruchamia proxy RTMP dla zdalnego strumienia.

        Args:
            device: Obiekt urządzenia sieciowego.
            stream_id (str): Identyfikator strumienia.
            source_url (str): URL źródłowy.
            output_dir (str): Katalog wyjściowy.
            transcode (bool): Czy transkodować strumień.

        Returns:
            str: URL do strumienia RTMP lub None w przypadku błędu.
        """
        try:
            # Wybór wolnego portu
            port = self._find_free_port(self.port_start)

            # Przygotowanie komend FFmpeg
            if device.protocol == 'rtsp':
                input_args = ['-rtsp_transport', 'tcp', '-i', source_url]
            else:
                input_args = ['-i', source_url]

            if transcode:
                if device.type == 'video':
                    # Transkodowanie wideo
                    output_args = [
                        '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'zerolatency',
                        '-c:a', 'aac', '-b:a', '128k',
                        '-f', 'flv', f'rtmp://localhost:{port}/live/{stream_id}'
                    ]
                else:
                    # Transkodowanie audio
                    output_args = [
                        '-c:a', 'aac', '-b:a', '128k',
                        '-f', 'flv', f'rtmp://localhost:{port}/live/{stream_id}'
                    ]
            else:
                # Bez transkodowania - przekazanie strumienia
                output_args = [
                    '-c', 'copy',
                    '-f', 'flv', f'rtmp://localhost:{port}/live/{stream_id}'
                ]

            # Uruchomienie serwera RTMP (nginx z modułem RTMP)
            nginx_config_path = os.path.join(output_dir, 'nginx.conf')
            with open(nginx_config_path, 'w') as f:
                f.write(self._generate_nginx_config(port))

            # Uruchomienie nginx z konfiguracją RTMP
            nginx_process = subprocess.Popen(
                ['nginx', '-c', nginx_config_path, '-p', output_dir],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            # Krótkie oczekiwanie na uruchomienie serwera RTMP
            time.sleep(2)

            # Uruchomienie procesu FFmpeg
            cmd = ['ffmpeg', '-hide_banner'] + input_args + output_args
            logger.debug(f"Uruchamianie komendy proxy RTMP: {' '.join(cmd)}")

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            # Krótkie oczekiwanie, aby sprawdzić, czy proces się uruchomił
            time.sleep(2)
            if process.poll() is not None:
                logger.error(f"Proces FFmpeg proxy zakończył działanie z kodem: {process.returncode}")
                nginx_process.terminate()
                return None

            # Utworzenie URL do strumienia
            url = f"rtmp://localhost:{port}/live/{stream_id}"

            return url

        except Exception as e:
            logger.error(f"Błąd podczas uruchamiania proxy RTMP: {e}")
            return None

    def _prepare_input_args(self, device):
        """
        Przygotowuje argumenty wejściowe dla FFmpeg.

        Args:
            device: Obiekt urządzenia.

        Returns:
            list: Lista argumentów wejściowych.
        """
        import platform
        system = platform.system().lower()

        if device.type == 'video':
            if system == 'linux':
                if device.driver == 'v4l2':
                    return ['-f', 'v4l2', '-i', device.system_path]
            elif system == 'darwin':  # macOS
                if device.driver == 'avfoundation':
                    return ['-f', 'avfoundation', '-framerate', '30', '-i', f"{device.system_path}:none"]
            elif system == 'windows':
                if device.driver == 'dshow':
                    return ['-f', 'dshow', '-i', f"video={device.system_path}"]
        elif device.type == 'audio':
            if system == 'linux':
                if device.driver == 'alsa':
                    return ['-f', 'alsa', '-i', device.system_path]
                elif device.driver == 'pulse':
                    return ['-f', 'pulse', '-i', device.system_path]
            elif system == 'darwin':  # macOS
                if device.driver == 'avfoundation':
                    return ['-f', 'avfoundation', '-i', f"none:{device.system_path}"]
            elif system == 'windows':
                if device.driver == 'dshow':
                    return ['-f', 'dshow', '-i', f"audio={device.system_path}"]

        logger.error(f"Nieobsługiwana platforma/sterownik: {system}/{device.driver}")
        return None

    def _prepare_output_args(self, device, port, stream_id):
        """
        Przygotowuje argumenty wyjściowe dla FFmpeg.

        Args:
            device: Obiekt urządzenia.
            port (int): Port RTMP.
            stream_id (str): Identyfikator strumienia.

        Returns:
            list: Lista argumentów wyjściowych.
        """
        if device.type == 'video':
            return [
                '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'zerolatency',
                '-c:a', 'aac', '-b:a', '128k',
                '-f', 'flv', f'rtmp://localhost:{port}/live/{stream_id}'
            ]
        elif device.type == 'audio':
            return [
                '-c:a', 'aac', '-b:a', '128k',
                '-f', 'flv', f'rtmp://localhost:{port}/live/{stream_id}'
            ]

        logger.error(f"Nieobsługiwany typ urządzenia: {device.type}")
        return None

    def _generate_nginx_config(self, port):
        """
        Generuje konfigurację NGINX z modułem RTMP.

        Args:
            port (int): Port RTMP.

        Returns:
            str: Konfiguracja NGINX.
        """
        return f"""
        worker_processes 1;
        events {{
            worker_connections 1024;
        }}
        rtmp {{
            server {{
                listen {port};
                chunk_size 4096;
                application live {{
                    live on;
                    record off;
                }}
            }}
        }}
        """

    async def stop_stream(self, stream_id):
        """
        Zatrzymuje strumień RTMP.

        Args:
            stream_id (str): Identyfikator strumienia.

        Returns:
            bool: True jeśli udało się zatrzymać strumień, False w przeciwnym razie.
        """
        try:
            if hasattr(self, 'process') and self.process:
                self.process.terminate()
                self.process.wait()
                self.process = None

            if hasattr(self, 'nginx_process') and self.nginx_process:
                self.nginx_process.terminate()
                self.nginx_process.wait()
                self.nginx_process = None

            return True
        except Exception as e:
            logger.error(f"Błąd podczas zatrzymywania strumienia RTMP: {e}")
            return False

    def _find_free_port(self, start_port):
        """
        Znajduje wolny port zaczynając od podanego.

        Args:
            start_port (int): Port początkowy.

        Returns:
            int: Wolny port.
        """
        port = start_port
        max_port = start_port + 1000  # Ograniczenie zakresu skanowania

        while port < max_port:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.1)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()

            if result != 0:  # Port jest wolny
                return port

            port += 1

        raise Exception(f"Nie znaleziono wolnego portu w zakresie {start_port}-{max_port}")
