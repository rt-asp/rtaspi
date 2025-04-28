#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rtaspi - Real-Time Annotation and Stream Processing
Menedżer lokalnych urządzeń (kamery, mikrofony)
"""

import os
import logging
import platform
import re
import subprocess
import uuid
import shlex
import json
import time
from pathlib import Path

from ..device_managers.base import DeviceManager
from ..device_managers.utils.device import LocalDevice
from ..streaming.rtsp import RTSPServer
from ..streaming.rtmp import RTMPServer
from ..streaming.webrtc import WebRTCServer

logger = logging.getLogger("LocalDevices")


class LocalDevicesManager(DeviceManager):
    """Klasa zarządzająca lokalnymi urządzeniami wideo i audio."""

    def __init__(self, config, mcp_broker):
        """
        Inicjalizacja menedżera lokalnych urządzeń.

        Args:
            config (dict): Konfiguracja menedżera.
            mcp_broker (MCPBroker): Broker protokołu MCP.
        """
        super().__init__(config, mcp_broker)

        # Pobranie konfiguracji z pliku
        local_devices_config = config.get('local_devices', {})
        self.enable_video = local_devices_config.get('enable_video', True)
        self.enable_audio = local_devices_config.get('enable_audio', True)
        self.auto_start = local_devices_config.get('auto_start', False)
        self.scan_interval = local_devices_config.get('scan_interval', 60)  # sekund
        self.rtsp_port_start = local_devices_config.get('rtsp_port_start', 8554)
        self.rtmp_port_start = local_devices_config.get('rtmp_port_start', 1935)
        self.webrtc_port_start = local_devices_config.get('webrtc_port_start', 8080)

        # Inicjalizacja serwerów streamingu
        self.rtsp_server = RTSPServer(config)
        self.rtmp_server = RTMPServer(config)
        self.webrtc_server = WebRTCServer(config)

        # Zmienne stanu
        self.devices = {
            'video': {},  # device_id -> LocalDevice
            'audio': {}  # device_id -> LocalDevice
        }

        # Przygotowanie katalogów
        self.local_streams_path = os.path.join(self.storage_path, 'local_streams')
        os.makedirs(self.local_streams_path, exist_ok=True)

    def _get_client_id(self):
        """
        Zwraca identyfikator klienta MCP.

        Returns:
            str: Identyfikator klienta MCP.
        """
        return "local_devices_manager"

    def _get_scan_interval(self):
        """
        Zwraca interwał skanowania w sekundach.

        Returns:
            int: Interwał skanowania w sekundach.
        """
        return self.scan_interval

    def _subscribe_to_events(self):
        """Subskrybuje zdarzenia MCP."""
        self.mcp_client.subscribe("command/local_devices/#", self._handle_command)

    def _publish_devices_info(self):
        """Publikuje informacje o urządzeniach."""
        # Konwersja obiektów urządzeń do słowników
        devices_dict = {
            'video': {dev_id: dev.to_dict() for dev_id, dev in self.devices['video'].items()},
            'audio': {dev_id: dev.to_dict() for dev_id, dev in self.devices['audio'].items()}
        }

        self.mcp_client.publish("local_devices/devices", devices_dict)

    def _publish_stream_stopped(self, stream_id, stream_info):
        """
        Publikuje informację o zatrzymaniu strumienia.

        Args:
            stream_id (str): Identyfikator strumienia.
            stream_info (dict): Informacje o strumieniu.
        """
        self.mcp_client.publish("local_devices/stream/stopped", {
            "stream_id": stream_id,
            "device_id": stream_info["device_id"],
            "type": stream_info["type"]
        })

    def _scan_devices(self):
        """Skanuje lokalne urządzenia."""
        # Skanowanie urządzeń wideo
        if self.enable_video:
            self._scan_video_devices()

        # Skanowanie urządzeń audio
        if self.enable_audio:
            self._scan_audio_devices()

        # Automatyczne uruchamianie strumieni
        if self.auto_start:
            self._auto_start_streams()

    def _scan_video_devices(self):
        """Skanuje lokalne urządzenia wideo."""
        # Wykrywanie w zależności od platformy
        system = platform.system().lower()

        if system == 'linux':
            self._scan_linux_video_devices()
        elif system == 'darwin':  # macOS
            self._scan_macos_video_devices()
        elif system == 'windows':
            self._scan_windows_video_devices()
        else:
            logger.warning(f"Nieobsługiwana platforma: {system}")

    def _scan_audio_devices(self):
        """Skanuje lokalne urządzenia audio."""
        # Wykrywanie w zależności od platformy
        system = platform.system().lower()

        if system == 'linux':
            self._scan_linux_audio_devices()
        elif system == 'darwin':  # macOS
            self._scan_macos_audio_devices()
        elif system == 'windows':
            self._scan_windows_audio_devices()
        else:
            logger.warning(f"Nieobsługiwana platforma: {system}")

    def _scan_linux_video_devices(self):
        """Skanuje urządzenia wideo w systemie Linux."""
        try:
            # Skanowanie urządzeń /dev/video*
            video_devices = {}
            dev_video_paths = sorted(Path('/dev').glob('video*'))

            for path in dev_video_paths:
                system_path = str(path)

                # Generowanie unikalnego ID dla urządzenia
                device_id = f"video:{system_path}"

                # Sprawdzenie, czy urządzenie jest już znane
                if device_id in self.devices['video']:
                    video_devices[device_id] = self.devices['video'][device_id]
                    continue

                # Próba uzyskania informacji o urządzeniu
                try:
                    output = subprocess.check_output(['v4l2-ctl', '--device', system_path, '--all'],
                                                     stderr=subprocess.STDOUT, universal_newlines=True)

                    # Parsowanie wyjścia, aby uzyskać nazwę urządzenia
                    name_match = re.search(r'Card type\s+:\s+(.+)', output)
                    name = name_match.group(1).strip() if name_match else f"Kamera {system_path}"

                    # Pobranie obsługiwanych formatów
                    formats_output = subprocess.check_output(
                        ['v4l2-ctl', '--device', system_path, '--list-formats-ext'],
                        stderr=subprocess.STDOUT, universal_newlines=True)
                    formats = []

                    for format_match in re.finditer(r'PixelFormat\s+:\s+\'(\w+)\'', formats_output):
                        formats.append(format_match.group(1))

                    # Pobranie obsługiwanych rozdzielczości
                    resolutions = []
                    for res_match in re.finditer(r'Size: Discrete (\d+)x(\d+)', formats_output):
                        resolutions.append(f"{res_match.group(1)}x{res_match.group(2)}")

                    # Utworzenie obiektu urządzenia
                    device = LocalDevice(
                        device_id=device_id,
                        name=name,
                        type='video',
                        system_path=system_path,
                        driver='v4l2'
                    )
                    device.formats = formats
                    device.resolutions = resolutions
                    device.status = 'online'

                    # Dodanie urządzenia do listy
                    video_devices[device_id] = device

                except subprocess.CalledProcessError as e:
                    logger.warning(f"Błąd podczas sprawdzania urządzenia {system_path}: {e}")
                    continue

            # Aktualizacja listy urządzeń
            self.devices['video'] = video_devices

        except Exception as e:
            logger.error(f"Błąd podczas skanowania urządzeń wideo w systemie Linux: {e}")

    def _scan_linux_audio_devices(self):
        """Skanuje urządzenia audio w systemie Linux."""
        try:
            # Skanowanie urządzeń audio przy użyciu ALSA
            audio_devices = {}

            try:
                # Pobranie listy urządzeń audio
                output = subprocess.check_output(['arecord', '-l'], stderr=subprocess.STDOUT, universal_newlines=True)

                # Parsowanie wyjścia
                for line in output.splitlines():
                    if not line.startswith('card '):
                        continue

                    match = re.match(r'card (\d+): (.+), device (\d+): (.+)', line)
                    if match:
                        card_id = match.group(1)
                        card_name = match.group(2)
                        device_num = match.group(3)
                        device_name = match.group(4)

                        # Tworzenie identyfikatora urządzenia
                        alsa_id = f"hw:{card_id},{device_num}"
                        device_id = f"alsa:{alsa_id}"

                        # Utworzenie obiektu urządzenia
                        device = LocalDevice(
                            device_id=device_id,
                            name=f"{card_name} - {device_name}",
                            type='audio',
                            system_path=alsa_id,
                            driver='alsa'
                        )
                        device.status = 'online'

                        # Dodanie urządzenia do listy
                        audio_devices[device_id] = device

            except subprocess.CalledProcessError as e:
                logger.warning(f"Błąd podczas skanowania urządzeń ALSA: {e}")

            # Skanowanie urządzeń PulseAudio
            try:
                # Pobranie listy urządzeń PulseAudio
                output = subprocess.check_output(['pactl', 'list', 'sources'],
                                                 stderr=subprocess.STDOUT, universal_newlines=True)

                # Parsowanie wyjścia
                current_device = {}
                for line in output.splitlines():
                    line = line.strip()

                    if line.startswith('Source #'):
                        # Nowe urządzenie
                        if current_device and 'name' in current_device:
                            device_id = f"pulse:{current_device['name']}"

                            # Utworzenie obiektu urządzenia
                            device = LocalDevice(
                                device_id=device_id,
                                name=current_device.get('description', current_device['name']),
                                type='audio',
                                system_path=current_device['name'],
                                driver='pulse'
                            )
                            device.status = 'online'

                            # Dodanie urządzenia do listy
                            audio_devices[device_id] = device

                        # Reset dla nowego urządzenia
                        current_device = {}
                    elif ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip().lower()
                        value = value.strip()

                        if key == 'name' or key == 'description':
                            current_device[key] = value

                # Dodanie ostatniego urządzenia
                if current_device and 'name' in current_device:
                    device_id = f"pulse:{current_device['name']}"

                    # Utworzenie obiektu urządzenia
                    device = LocalDevice(
                        device_id=device_id,
                        name=current_device.get('description', current_device['name']),
                        type='audio',
                        system_path=current_device['name'],
                        driver='pulse'
                    )
                    device.status = 'online'

                    # Dodanie urządzenia do listy
                    audio_devices[device_id] = device

            except subprocess.CalledProcessError as e:
                logger.warning(f"Błąd podczas skanowania urządzeń PulseAudio: {e}")

            # Aktualizacja listy urządzeń
            self.devices['audio'] = audio_devices

        except Exception as e:
            logger.error(f"Błąd podczas skanowania urządzeń audio w systemie Linux: {e}")

    def _scan_macos_video_devices(self):
        """Skanuje urządzenia wideo w systemie macOS."""
        try:
            # Użycie ffmpeg do wykrycia kamer w macOS
            output = subprocess.check_output(['ffmpeg', '-f', 'avfoundation', '-list_devices', 'true', '-i', ''],
                                             stderr=subprocess.STDOUT, universal_newlines=True)

            video_devices = {}
            capture_next = False

            for line in output.splitlines():
                if 'AVFoundation video devices:' in line:
                    capture_next = True
                    continue
                elif 'AVFoundation audio devices:' in line:
                    break

                if capture_next and ']' in line:
                    match = re.search(r'\[(\d+)\]\s+(.+)', line)
                    if match:
                        index = match.group(1)
                        name = match.group(2).strip()
                        device_id = f"avfoundation:video:{index}"

                        # Utworzenie obiektu urządzenia
                        device = LocalDevice(
                            device_id=device_id,
                            name=name,
                            type='video',
                            system_path=index,
                            driver='avfoundation'
                        )
                        device.status = 'online'

                        # Dodanie urządzenia do listy
                        video_devices[device_id] = device

            # Aktualizacja listy urządzeń
            self.devices['video'] = video_devices

        except Exception as e:
            logger.error(f"Błąd podczas skanowania urządzeń wideo w systemie macOS: {e}")

    def _scan_macos_audio_devices(self):
        """Skanuje urządzenia audio w systemie macOS."""
        try:
            # Użycie ffmpeg do wykrycia mikrofonów w macOS
            output = subprocess.check_output(['ffmpeg', '-f', 'avfoundation', '-list_devices', 'true', '-i', ''],
                                             stderr=subprocess.STDOUT, universal_newlines=True)

            audio_devices = {}
            capture_next = False

            for line in output.splitlines():
                if 'AVFoundation audio devices:' in line:
                    capture_next = True
                    continue

                if capture_next and ']' in line:
                    match = re.search(r'\[(\d+)\]\s+(.+)', line)
                    if match:
                        index = match.group(1)
                        name = match.group(2).strip()
                        device_id = f"avfoundation:audio:{index}"

                        # Utworzenie obiektu urządzenia
                        device = LocalDevice(
                            device_id=device_id,
                            name=name,
                            type='audio',
                            system_path=index,
                            driver='avfoundation'
                        )
                        device.status = 'online'

                        # Dodanie urządzenia do listy
                        audio_devices[device_id] = device

            # Aktualizacja listy urządzeń
            self.devices['audio'] = audio_devices

        except Exception as e:
            logger.error(f"Błąd podczas skanowania urządzeń audio w systemie macOS: {e}")

    def _scan_windows_video_devices(self):
        """Skanuje urządzenia wideo w systemie Windows."""
        try:
            # Użycie ffmpeg do wykrycia kamer w Windows
            output = subprocess.check_output(['ffmpeg', '-list_devices', 'true', '-f', 'dshow', '-i', 'dummy'],
                                             stderr=subprocess.STDOUT, universal_newlines=True)

            video_devices = {}
            capture_section = False

            for line in output.splitlines():
                if 'DirectShow video devices' in line:
                    capture_section = True
                    continue
                elif 'DirectShow audio devices' in line:
                    break

                if capture_section and 'Alternative name' in line:
                    match = re.search(r'"(.+)"', line)
                    if match:
                        name = match.group(1)
                        device_id = f"dshow:video:{name}"

                        # Utworzenie obiektu urządzenia
                        device = LocalDevice(
                            device_id=device_id,
                            name=name,
                            type='video',
                            system_path=name,
                            driver='dshow'
                        )
                        device.status = 'online'

                        # Dodanie urządzenia do listy
                        video_devices[device_id] = device

            # Aktualizacja listy urządzeń
            self.devices['video'] = video_devices

        except Exception as e:
            logger.error(f"Błąd podczas skanowania urządzeń wideo w systemie Windows: {e}")

    def _scan_windows_audio_devices(self):
        """Skanuje urządzenia audio w systemie Windows."""
        try:
            # Użycie ffmpeg do wykrycia mikrofonów w Windows
            output = subprocess.check_output(['ffmpeg', '-list_devices', 'true', '-f', 'dshow', '-i', 'dummy'],
                                             stderr=subprocess.STDOUT, universal_newlines=True)

            audio_devices = {}
            capture_section = False

            for line in output.splitlines():
                if 'DirectShow audio devices' in line:
                    capture_section = True
                    continue

                if capture_section and 'Alternative name' in line:
                    match = re.search(r'"(.+)"', line)
                    if match:
                        name = match.group(1)
                        device_id = f"dshow:audio:{name}"

                        # Utworzenie obiektu urządzenia
                        device = LocalDevice(
                            device_id=device_id,
                            name=name,
                            type='audio',
                            system_path=name,
                            driver='dshow'
                        )
                        device.status = 'online'

                        # Dodanie urządzenia do listy
                        audio_devices[device_id] = device

            # Aktualizacja listy urządzeń
            self.devices['audio'] = audio_devices

        except Exception as e:
            logger.error(f"Błąd podczas skanowania urządzeń audio w systemie Windows: {e}")

    def _auto_start_streams(self):
        """Automatycznie uruchamia strumienie dla wykrytych urządzeń."""
        # Automatyczne uruchamianie strumieni wideo
        if self.enable_video:
            for device_id, device in self.devices['video'].items():
                # Sprawdzenie, czy strumień już istnieje
                device_has_stream = False
                for stream_info in self.streams.values():
                    if stream_info["device_id"] == device_id:
                        device_has_stream = True
                        break

                # Uruchomienie strumienia RTSP, jeśli nie istnieje
                if not device_has_stream:
                    logger.info(f"Automatyczne uruchamianie strumienia dla urządzenia wideo {device_id}")
                    self.start_stream(device_id, protocol="rtsp")

        # Automatyczne uruchamianie strumieni audio
        if self.enable_audio:
            for device_id, device in self.devices['audio'].items():
                # Sprawdzenie, czy strumień już istnieje
                device_has_stream = False
                for stream_info in self.streams.values():
                    if stream_info["device_id"] == device_id:
                        device_has_stream = True
                        break

                # Uruchomienie strumienia RTSP, jeśli nie istnieje
                if not device_has_stream:
                    logger.info(f"Automatyczne uruchamianie strumienia dla urządzenia audio {device_id}")
                    self.start_stream(device_id, protocol="rtsp")

    def start_stream(self, device_id, protocol='rtsp'):
        """
        Uruchamia strumień z lokalnego urządzenia.

        Args:
            device_id (str): Identyfikator urządzenia.
            protocol (str): Protokół streamingu ('rtsp', 'rtmp', 'webrtc').

        Returns:
            str: URL do strumienia lub None w przypadku błędu.
        """
        # Określenie typu urządzenia na podstawie identyfikatora
        device_type = None
        device = None

        if device_id in self.devices['video']:
            device_type = 'video'
            device = self.devices['video'][device_id]
        elif device_id in self.devices['audio']:
            device_type = 'audio'
            device = self.devices['audio'][device_id]

        if not device:
            logger.error(f"Nieznane urządzenie: {device_id}")
            return None

        # Sprawdzenie, czy strumień już istnieje
        for stream_id, stream_info in self.streams.items():
            if stream_info["device_id"] == device_id:
                logger.info(f"Strumień już istnieje: {stream_id}")
                return stream_info["url"]

        # Tworzenie identyfikatora strumienia
        stream_id = str(uuid.uuid4())

        # Przygotowanie ścieżki wyjściowej
        output_dir = os.path.join(self.local_streams_path, stream_id)
        os.makedirs(output_dir, exist_ok=True)

        try:
            # Uruchomienie odpowiedniego serwera streamingu
            if protocol == 'rtsp':
                url = self.rtsp_server.start_stream(device, stream_id, output_dir)
            elif protocol == 'rtmp':
                url = self.rtmp_server.start_stream(device, stream_id, output_dir)
            elif protocol == 'webrtc':
                url = self.webrtc_server.start_stream(device, stream_id, output_dir)
            else:
                logger.error(f"Nieobsługiwany protokół: {protocol}")
                return None

            if url:
                logger.info(f"Uruchomiono strumień {protocol} dla urządzenia {device_id}: {url}")

                # Publikacja informacji o nowym strumieniu
                self.mcp_client.publish(f"local_devices/stream/started", {
                    "stream_id": stream_id,
                    "device_id": device_id,
                    "type": device_type,
                    "protocol": protocol,
                    "url": url
                })

                return url
            else:
                logger.error(f"Nie można uruchomić strumienia {protocol} dla urządzenia {device_id}")
                return None

        except Exception as e:
            logger.error(f"Błąd podczas uruchamiania strumienia {protocol} dla urządzenia {device_id}: {e}")
            return None

    def _handle_command(self, topic, message):
        """
        Obsługuje komendy MCP dla menedżera lokalnych urządzeń.

        Args:
            topic (str): Temat MCP.
            message (dict): Treść wiadomości.
        """
        try:
            # Parsowanie tematu
            parts = topic.split('/')
            if len(parts) < 3:
                logger.warning(f"Nieprawidłowy format tematu: {topic}")
                return

            command = parts[2]

            if command == "scan":
                # Ręczne skanowanie urządzeń
                logger.info("Otrzymano polecenie skanowania urządzeń")
                self._scan_devices()

                # Publikacja informacji o urządzeniach
                self._publish_devices_info()

            elif command == "start_stream":
                # Uruchomienie strumienia
                device_id = message.get("device_id")
                protocol = message.get("protocol", "rtsp")

                if not device_id:
                    logger.warning("Brak wymaganego parametru device_id dla komendy start_stream")
                    return

                logger.info(f"Otrzymano polecenie uruchomienia strumienia {protocol} dla urządzenia {device_id}")
                url = self.start_stream(device_id, protocol)

                # Publikacja odpowiedzi
                self.mcp_client.publish("local_devices/command/result", {
                    "command": "start_stream",
                    "device_id": device_id,
                    "protocol": protocol,
                    "success": bool(url),
                    "url": url
                })

            elif command == "stop_stream":
                # Zatrzymanie strumienia
                stream_id = message.get("stream_id")

                if not stream_id:
                    logger.warning("Brak wymaganego parametru stream_id dla komendy stop_stream")
                    return

                logger.info(f"Otrzymano polecenie zatrzymania strumienia {stream_id}")
                success = self.stop_stream(stream_id)

                # Publikacja odpowiedzi
                self.mcp_client.publish("local_devices/command/result", {
                    "command": "stop_stream",
                    "stream_id": stream_id,
                    "success": success
                })

            elif command == "get_devices":
                # Pobranie listy urządzeń
                logger.info("Otrzymano polecenie pobrania listy urządzeń")

                # Konwersja obiektów urządzeń do słowników
                devices_dict = {
                    'video': {dev_id: dev.to_dict() for dev_id, dev in self.devices['video'].items()},
                    'audio': {dev_id: dev.to_dict() for dev_id, dev in self.devices['audio'].items()}
                }

                # Publikacja odpowiedzi
                self.mcp_client.publish("local_devices/command/result", {
                    "command": "get_devices",
                    "devices": devices_dict
                })

            elif command == "get_streams":
                # Pobranie listy strumieni
                logger.info("Otrzymano polecenie pobrania listy strumieni")

                # Publikacja odpowiedzi
                self.mcp_client.publish("local_devices/command/result", {
                    "command": "get_streams",
                    "streams": self.get_streams()
                })

            else:
                logger.warning(f"Nieznana komenda: {command}")

        except Exception as e:
            logger.error(f"Błąd podczas obsługi komendy MCP: {e}")