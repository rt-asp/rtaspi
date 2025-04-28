#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rtaspi - Real-Time Annotation and Stream Processing
Menedżer zdalnych urządzeń sieciowych (kamery IP, mikrofony IP)
"""

import os
import logging
import json
import time
import uuid
import socket
import subprocess
import re
import shlex
import platform
from urllib.parse import urlparse
from pathlib import Path

from ..core.mcp import MCPClient
from ..device_managers.base import DeviceManager
from ..device_managers.utils.device import NetworkDevice
from ..device_managers.utils.discovery import ONVIFDiscovery, UPnPDiscovery, MDNSDiscovery
from ..streaming.rtsp import RTSPServer
from ..streaming.rtmp import RTMPServer
from ..streaming.webrtc import WebRTCServer

logger = logging.getLogger("NetworkDevices")


class NetworkDevicesManager:
    """Menedżer zdalnych urządzeń sieciowych (kamery IP, mikrofony IP)."""
    def __init__(self, config, mcp_broker):
        self.config = config
        self.mcp_broker = mcp_broker
        self.running = False
        self.devices = {}  # device_id -> NetworkDevice
        self.streams = {}  # stream_id -> stream_info
        self.discovery_methods = ['onvif', 'upnp', 'mdns']
        self.discovery_modules = {
            'onvif': ONVIFDiscovery(),
            'upnp': UPnPDiscovery(),
            'mdns': MDNSDiscovery(),
        }
        self.scan_interval = config.get('network_devices', {}).get('scan_interval', 60)
        self.devices_file = os.path.join(config.get('system', {}).get('storage_path', 'storage'), 'network_devices.json')
        self.mcp_client = MCPClient(mcp_broker, client_id=self._get_client_id())

    def start(self):
        logger.info("Uruchamianie menedżera urządzeń sieciowych...")
        self.running = True
        self._load_saved_devices()
        self._subscribe_to_events()
        self._discover_devices()
        logger.info("Menedżer urządzeń sieciowych uruchomiony")

    def stop(self):
        logger.info("Zatrzymywanie menedżera urządzeń sieciowych...")
        self.running = False
        self.mcp_client.close()
        logger.info("Menedżer urządzeń sieciowych zatrzymany")

    def _get_client_id(self):
        return "network_devices_manager"

    def _handle_command(self, topic, payload):
        """
        Obsługuje komendy przychodzące przez MCP.

        Args:
            topic (str): Temat wiadomości MCP.
            payload (dict): Zawartość wiadomości.
        """
        try:
            # Wyodrębnienie nazwy komendy z tematu (np. command/network_devices/add → add)
            parts = topic.split('/')
            if len(parts) < 3:
                logger.warning(f"Nieprawidłowy format tematu komendy: {topic}")
                return

            command = parts[2]

            if command == "add":
                # Dodanie nowego urządzenia
                self.add_device(
                    name=payload.get('name', 'Nowe urządzenie'),
                    ip=payload.get('ip', ''),
                    port=payload.get('port', 80),
                    username=payload.get('username', ''),
                    password=payload.get('password', ''),
                    type=payload.get('type', 'video'),
                    protocol=payload.get('protocol', 'rtsp'),
                    paths=payload.get('paths', [])
                )

            elif command == "remove":
                # Usunięcie urządzenia
                device_id = payload.get('device_id')
                if device_id:
                    self.remove_device(device_id)

            elif command == "start_stream":
                # Implementacja uruchamiania strumienia
                device_id = payload.get('device_id')
                stream_path = payload.get('stream_path')
                # Tutaj implementacja uruchamiania strumienia

            elif command == "stop_stream":
                # Implementacja zatrzymywania strumienia
                stream_id = payload.get('stream_id')
                # Tutaj implementacja zatrzymywania strumienia

            elif command == "scan":
                # Ręczne wywołanie skanowania urządzeń
                self._scan_devices()

            else:
                logger.warning(f"Nieznana komenda: {command}")

        except Exception as e:
            logger.error(f"Błąd podczas przetwarzania komendy {topic}: {e}")

    def _subscribe_to_events(self):
        """Subskrybuje zdarzenia MCP."""
        self.mcp_client.subscribe("command/network_devices/#", self._handle_command)

    def _publish_devices_info(self):
        """Publikuje informacje o urządzeniach."""
        devices_dict = {device_id: device.to_dict() for device_id, device in self.devices.items()}
        self.mcp_client.publish("network_devices/devices", devices_dict)

    def _publish_stream_stopped(self, stream_id, stream_info):
        """
        Publikuje informację o zatrzymaniu strumienia.
        
        Args:
            stream_id (str): Identyfikator strumienia.
            stream_info (dict): Informacje o strumieniu.
        """
        self.mcp_client.publish("network_devices/stream/stopped", {
            "stream_id": stream_id,
            "device_id": stream_info["device_id"]
        })

    def _load_saved_devices(self):
        """Ładuje zapisane urządzenia z pliku."""
        try:
            if os.path.exists(self.devices_file):
                with open(self.devices_file, 'r') as f:
                    devices_data = json.load(f)

                for device_data in devices_data:
                    try:
                        device_id = device_data.get('id')
                        if not device_id:
                            continue

                        # Utworzenie obiektu urządzenia
                        device = NetworkDevice(
                            device_id=device_id,
                            name=device_data.get('name', 'Nieznane urządzenie'),
                            type=device_data.get('type', 'video'),
                            ip=device_data.get('ip', ''),
                            port=device_data.get('port', 80),
                            username=device_data.get('username', ''),
                            password=device_data.get('password', ''),
                            protocol=device_data.get('protocol', 'rtsp')
                        )

                        # Dodanie ścieżek strumieni
                        if 'streams' in device_data:
                            device.streams = device_data['streams']

                        # Dodanie urządzenia do listy
                        self.devices[device_id] = device

                    except Exception as e:
                        logger.error(f"Błąd podczas ładowania urządzenia: {e}")

                logger.info(f"Załadowano {len(self.devices)} zapisanych urządzeń")

        except Exception as e:
            logger.error(f"Błąd podczas ładowania zapisanych urządzeń: {e}")

    def _save_devices(self):
        """Zapisuje urządzenia do pliku."""
        try:
            devices_data = []

            for device_id, device in self.devices.items():
                # Utworzenie słownika z danymi urządzenia
                device_data = device.to_dict()
                device_data['username'] = device.username
                device_data['password'] = device.password
                devices_data.append(device_data)

            # Zapisanie do pliku
            with open(self.devices_file, 'w') as f:
                json.dump(devices_data, f, indent=2)

            logger.debug(f"Zapisano {len(devices_data)} urządzeń do pliku")

        except Exception as e:
            logger.error(f"Błąd podczas zapisywania urządzeń: {e}")

    def _scan_devices(self):
        """Skanuje zdalne urządzenia."""
        # Sprawdzenie stanu znanych urządzeń
        for device_id, device in list(self.devices.items()):
            self._check_device_status(device)

        # Wykrywanie nowych urządzeń
        if self.discovery_enabled:
            self._discover_devices()

    def _check_device_status(self, device):
        """
        Sprawdza stan zdalnego urządzenia.
        
        Args:
            device (NetworkDevice): Urządzenie do sprawdzenia.
        """
        try:
            # Sprawdzenie, czy minął wystarczający czas od ostatniego sprawdzenia
            current_time = time.time()
            if current_time - device.last_check < self.scan_interval / 2:
                return

            device.last_check = current_time

            # Prosty test dostępności poprzez ping (sprawdzenie portu)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((device.ip, device.port))
            sock.close()

            if result != 0:
                device.status = "offline"
                return

            # Próba połączenia z urządzeniem w zależności od protokołu
            if device.protocol == "rtsp":
                # RTSP jest trudny do sprawdzenia bez specjalnych bibliotek
                # Używamy prostego socketa
                device.status = "online"
            elif device.protocol == "http":
                # Dla HTTP można użyć biblioteki requests, ale tutaj używamy socketa
                device.status = "online"
            elif device.protocol == "rtmp":
                # RTMP jest trudny do sprawdzenia, uznajemy za online jeśli port jest otwarty
                device.status = "online"
            else:
                # Domyślnie uznajemy za online jeśli port jest otwarty
                device.status = "online"

        except Exception as e:
            logger.warning(f"Błąd podczas sprawdzania stanu urządzenia {device.name}: {e}")
            device.status = "offline"

    def _discover_devices(self):
        """Wykrywa nowe urządzenia sieciowe i lokalne."""
        try:
            # Discover network devices
            for method in self.discovery_methods:
                if method in self.discovery_modules:
                    logger.info(f"Wykrywanie urządzeń metodą {method}...")
                    discovered_devices = self.discovery_modules[method].discover()

                    # Add discovered network devices
                    self._process_discovered_devices(discovered_devices)

            # Discover local media devices
            local_devices = self._discover_local_media_devices()
            self._process_discovered_devices(local_devices)

        except Exception as e:
            logger.error(f"Błąd podczas wykrywania urządzeń: {e}")

    def _process_discovered_devices(self, discovered_devices):
        """Process discovered devices and add new ones to the system."""
        for device_info in discovered_devices:
            try:
                # Check if device already exists
                ip = device_info.get('ip')
                port = device_info.get('port')
                device_index = device_info.get('device_index')

                device_exists = False
                for device in self.devices.values():
                    if device.ip == ip and device.port == port:
                        # For network devices, check IP and port
                        if device_index is None:
                            device_exists = True
                            break
                        # For local devices, also check device index
                        elif hasattr(device, 'device_index') and device.device_index == device_index:
                            device_exists = True
                            break

                if not device_exists:
                    # Add new device
                    self.add_device(
                        name=device_info.get('name', f"Urządzenie {ip}"),
                        ip=ip,
                        port=port,
                        type=device_info.get('type', 'video'),
                        protocol=device_info.get('protocol', 'rtsp'),
                        username=device_info.get('username', ''),
                        password=device_info.get('password', ''),
                        paths=device_info.get('paths', []),
                        device_index=device_info.get('device_index'),
                        device_path=device_info.get('device_path', None),
                        is_input=device_info.get('is_input', None),
                        is_output=device_info.get('is_output', None)
                    )
            except Exception as e:
                logger.error(f"Błąd podczas przetwarzania wykrytego urządzenia: {e}")

    def _discover_local_media_devices(self):
        """Discover local media devices connected to the system."""
        logger.info("Wykrywanie lokalnych urządzeń audio/wideo...")

        discovered = []

        try:
            # Try to import necessary libraries
            import pyaudio
            import cv2

            # Discover audio devices using PyAudio
            try:
                p = pyaudio.PyAudio()
                info = p.get_host_api_info_by_index(0)
                num_devices = info.get('deviceCount')

                for i in range(num_devices):
                    device_info = p.get_device_info_by_index(i)

                    # Check if it's input (microphone) or output (speaker) device
                    is_input = device_info.get('maxInputChannels') > 0
                    is_output = device_info.get('maxOutputChannels') > 0

                    if is_input:
                        discovered.append({
                            'name': f"Mikrofon: {device_info.get('name')}",
                            'ip': '127.0.0.1',
                            'port': 0,
                            'type': 'audio',
                            'protocol': 'local',
                            'device_index': i,
                            'is_input': True
                        })

                    if is_output:
                        discovered.append({
                            'name': f"Głośnik: {device_info.get('name')}",
                            'ip': '127.0.0.1',
                            'port': 0,
                            'type': 'audio',
                            'protocol': 'local',
                            'device_index': i,
                            'is_output': True
                        })

                p.terminate()
            except Exception as e:
                logger.warning(f"Nie udało się wykryć urządzeń audio: {e}")

            # Discover camera devices using OpenCV
            try:
                # On Linux, check /dev/video* devices
                if platform.system() == 'Linux':
                    import glob
                    video_devices = glob.glob('/dev/video*')

                    for i, device_path in enumerate(video_devices):
                        try:
                            # Try to open the device to check if it's a camera
                            cap = cv2.VideoCapture(i)
                            if cap.isOpened():
                                discovered.append({
                                    'name': f"Kamera: {device_path}",
                                    'ip': '127.0.0.1',
                                    'port': 0,
                                    'type': 'video',
                                    'protocol': 'local',
                                    'device_index': i,
                                    'device_path': device_path
                                })
                                cap.release()
                        except:
                            pass
                else:
                    # For other platforms, try the first few indexes
                    for i in range(5):  # Try first 5 possible cameras
                        try:
                            cap = cv2.VideoCapture(i)
                            if cap.isOpened():
                                discovered.append({
                                    'name': f"Kamera {i}",
                                    'ip': '127.0.0.1',
                                    'port': 0,
                                    'type': 'video',
                                    'protocol': 'local',
                                    'device_index': i
                                })
                                cap.release()
                        except:
                            pass
            except Exception as e:
                logger.warning(f"Nie udało się wykryć kamer: {e}")

        except ImportError as e:
            logger.warning(f"Nie można importować bibliotek do wykrywania lokalnych urządzeń: {e}")

        logger.info(f"Wykryto {len(discovered)} lokalnych urządzeń audio/wideo")
        return discovered

    def add_device(self, name, ip, port, username="", password="",
                   type="video", protocol="rtsp", paths=None,
                   device_index=None, device_path=None,
                   is_input=None, is_output=None):
        """
        Dodaje nowe zdalne urządzenie.
        
        Args:
            name (str): Nazwa urządzenia.
            ip (str): Adres IP urządzenia.
            port (int): Port urządzenia.
            username (str): Nazwa użytkownika do uwierzytelnienia.
            password (str): Hasło do uwierzytelnienia.
            type (str): Typ urządzenia ('video' lub 'audio').
            protocol (str): Protokół ('rtsp', 'rtmp', 'http', etc.).
            paths (list): Lista ścieżek do zasobów w urządzeniu.
            
        Returns:
            str: Identyfikator dodanego urządzenia lub None w przypadku błędu.
        """
        try:
            # Tworzenie identyfikatora urządzenia
            device_id = str(uuid.uuid4())

            # Utworzenie obiektu urządzenia sieciowego
            device = NetworkDevice(
                device_id=device_id,
                name=name,
                type=type,
                ip=ip,
                port=port,
                username=username,
                password=password,
                protocol=protocol
            )

            # Dodanie ścieżek do urządzenia
            if paths:
                for i, path in enumerate(paths):
                    stream_id = f"{device_id}_{i}"
                    device.streams[stream_id] = f"{device.get_base_url()}/{path}"

            # Sprawdzenie stanu urządzenia
            self._check_device_status(device)

            # Dodanie urządzenia do listy
            self.devices[device_id] = device

            # Zapisanie urządzeń
            self._save_devices()

            # Publikacja informacji o nowym urządzeniu
            self.mcp_client.publish("network_devices/device/added", device.to_dict())

            logger.info(f"Dodano zdalne urządzenie: {name} ({ip}:{port})")
            return device_id

        except Exception as e:
            logger.error(f"Błąd podczas dodawania zdalnego urządzenia: {e}")
            return None

    def remove_device(self, device_id):
        """
        Usuwa zdalne urządzenie.

        Args:
            device_id (str): Identyfikator urządzenia.

        Returns:
            bool: True jeśli usunięto urządzenie, False w przeciwnym przypadku.
        """
        try:
            if device_id not in self.devices:
                logger.warning(f"Próba usunięcia nieistniejącego urządzenia: {device_id}")
                return False

            # Zatrzymanie wszystkich strumieni urządzenia
            for stream_id, stream_info in list(self.streams.items()):
                if stream_info.get("device_id") == device_id:
                    self.stop_stream(stream_id)

            # Usunięcie urządzenia
            del self.devices[device_id]

            # Zapisanie urządzeń
            self._save_devices()

            # Publikacja informacji o usunięciu urządzenia
            self.mcp_client.publish("network_devices/device/removed", {
                "device_id": device_id
            })

            logger.info(f"Usunięto zdalne urządzenie: {device_id}")
            return True

        except Exception as e:
            logger.error(f"Błąd podczas usuwania zdalnego urządzenia: {e}")
            return False
