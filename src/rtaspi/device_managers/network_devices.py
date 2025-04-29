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
        network_devices_config = config.get('network_devices', {})
        self.discovery_enabled = network_devices_config.get('discovery_enabled', True)
        self.discovery_methods = network_devices_config.get('discovery_methods', ['onvif', 'upnp', 'mdns'])
        self.discovery_modules = {
            'onvif': ONVIFDiscovery(),
            'upnp': UPnPDiscovery(),
            'mdns': MDNSDiscovery(),
        }
        self.scan_interval = config.get('network_devices', {}).get('scan_interval', 60)
        self.devices_file = os.path.join(config.get('system', {}).get('storage_path', 'storage'),
                                         'network_devices.json')
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

    def update_device(self, device_id, **kwargs):
        """
        Updates a network device's properties.

        Args:
            device_id (str): The ID of the device to update.
            **kwargs: Device properties to update (name, ip, port, etc.).

        Returns:
            bool: True if update was successful, False otherwise.

        Raises:
            ValueError: If device_id doesn't exist or invalid properties are provided.
        """
        if device_id not in self.devices:
            raise ValueError(f"Device {device_id} not found")

        device = self.devices[device_id]

        # Validate port if provided
        if 'port' in kwargs:
            port = kwargs['port']
            if not isinstance(port, int) or port < 1 or port > 65535:
                raise ValueError("Invalid port number")

        # Validate type if provided
        if 'type' in kwargs:
            if kwargs['type'] not in ['video', 'audio']:
                raise ValueError("Type must be 'video' or 'audio'")

        # Validate protocol if provided
        if 'protocol' in kwargs:
            if kwargs['protocol'] not in ['rtsp', 'rtmp', 'http']:
                raise ValueError("Protocol must be 'rtsp', 'rtmp', or 'http'")

        # Update device properties
        for key, value in kwargs.items():
            if hasattr(device, key):
                setattr(device, key, value)

        # Save changes
        self._save_devices()

        # Publish update event
        self.mcp_client.publish("network_devices/device/updated", {
            "device_id": device_id,
            "updates": kwargs
        })

        logger.info(f"Updated network device {device_id}")
        return True

    def _handle_command(self, topic, payload):
        """
        Obsługuje komendy przychodzące przez MCP.

        Args:
            topic (str): Temat wiadomości MCP.
            payload (dict): Zawartość wiadomości.

        Raises:
            ValueError: When command is invalid or required parameters are missing.
        """
        # Parse command from topic
        parts = topic.split('/')
        if len(parts) < 3:
            raise ValueError(f"Invalid command topic format: {topic}")

        command = parts[2]

        if command == "add":
            # Validate required fields
            if not all(key in payload for key in ['name', 'ip', 'port']):
                raise ValueError("Missing required fields for add command")

            # Add new device
            self.add_device(
                name=payload['name'],
                ip=payload['ip'],
                port=payload['port'],
                username=payload.get('username', ''),
                password=payload.get('password', ''),
                type=payload.get('type', 'video'),
                protocol=payload.get('protocol', 'rtsp'),
                paths=payload.get('paths', [])
            )

        elif command == "remove":
            # Validate required fields
            if 'device_id' not in payload:
                raise ValueError("Missing device_id for remove command")

            # Remove device
            if not self.remove_device(payload['device_id']):
                raise ValueError(f"Failed to remove device {payload['device_id']}")

        elif command == "update":
            # Validate required fields
            if 'device_id' not in payload:
                raise ValueError("Missing device_id for update command")

            # Update device
            update_data = payload.copy()
            device_id = update_data.pop('device_id')
            self.update_device(device_id, **update_data)

        elif command == "scan":
            # Manual device scan
            self._scan_devices()

        else:
            raise ValueError(f"Unknown command: {command}")

    def _subscribe_to_events(self):
        """Subskrybuje zdarzenia MCP."""
        self.mcp_client.subscribe("command/network_devices/#", self._handle_command)

    def _publish_devices_info(self):
        """Publikuje informacje o urządzeniach."""
        devices_dict = {device_id: device.to_dict() for device_id, device in self.devices.items() if isinstance(device, NetworkDevice)}
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

    def save_state(self, state_file=None):
        """
        Save the current state of devices to a file.

        Args:
            state_file (str, optional): Path to save state to. If not provided,
                                      uses the default devices_file path.

        Returns:
            bool: True if save was successful, False otherwise.
        """
        try:
            file_path = state_file or self.devices_file
            devices_data = []

            for device_id, device in self.devices.items():
                if isinstance(device, NetworkDevice):
                    device_data = device.to_dict()
                    device_data['id'] = device_id  # Ensure ID is included
                    device_data['username'] = device.username
                    device_data['password'] = device.password
                    device_data['streams'] = device.streams
                    devices_data.append(device_data)

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Save to file
            with open(file_path, 'w') as f:
                json.dump(devices_data, f, indent=2)

            logger.info(f"Saved {len(devices_data)} devices to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving devices state: {e}")
            return False

    def load_state(self, state_file=None):
        """
        Load devices state from a file.

        Args:
            state_file (str, optional): Path to load state from. If not provided,
                                      uses the default devices_file path.

        Returns:
            bool: True if load was successful, False otherwise.
        """
        try:
            file_path = state_file or self.devices_file
            if not os.path.exists(file_path):
                logger.warning(f"State file not found: {file_path}")
                return False

            with open(file_path, 'r') as f:
                devices_data = json.load(f)

            # Clear current devices
            self.devices.clear()

            # Load devices
            for device_data in devices_data:
                try:
                    device_id = device_data.get('id')
                    if not device_id:
                        continue

                    # Create device object
                    device = NetworkDevice(
                        device_id=device_id,
                        name=device_data.get('name', 'Unknown Device'),
                        type=device_data.get('type', 'video'),
                        ip=device_data.get('ip', ''),
                        port=device_data.get('port', 80),
                        username=device_data.get('username', ''),
                        password=device_data.get('password', ''),
                        protocol=device_data.get('protocol', 'rtsp')
                    )

                    # Add stream paths
                    if 'streams' in device_data:
                        device.streams = device_data['streams']

                    # Add device to list
                    self.devices[device_id] = device

                except Exception as e:
                    logger.error(f"Error loading device: {e}")
                    continue

            logger.info(f"Loaded {len(self.devices)} devices from {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error loading devices state: {e}")
            return False

    def _load_saved_devices(self):
        """Load devices from the default state file."""
        self.load_state()

    def _save_devices(self):
        """Save devices to the default state file."""
        self.save_state()

    def _scan_devices(self):
        """Skanuje zdalne urządzenia."""
        # Sprawdzenie stanu znanych urządzeń
        for device_id, device in list(self.devices.items()):
            if isinstance(device, NetworkDevice):
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

            # Network devices manager only handles network devices

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
                    if isinstance(device, NetworkDevice):
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
            str: Identyfikator dodanego urządzenia.

        Raises:
            ValueError: Gdy podane dane są nieprawidłowe lub urządzenie już istnieje.
        """
        # Validate required fields
        if not name or not ip or not port:
            raise ValueError("Name, IP, and port are required")

        # Validate port range
        if not isinstance(port, int) or port < 1 or port > 65535:
            raise ValueError("Invalid port number")

        # Validate type
        if type not in ['video', 'audio']:
            raise ValueError("Type must be 'video' or 'audio'")

        # Validate protocol
        if protocol not in ['rtsp', 'rtmp', 'http']:
            raise ValueError("Protocol must be 'rtsp', 'rtmp', or 'http'")

        # Check for duplicate device
        for device in self.devices.values():
            if device.ip == ip and device.port == port:
                raise ValueError(f"Device with IP {ip} and port {port} already exists")

        try:
            # Create device ID
            device_id = str(uuid.uuid4())

            # Create network device object
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

            # Add stream paths
            if paths:
                for i, path in enumerate(paths):
                    stream_id = f"{device_id}_{i}"
                    device.streams[stream_id] = f"{device.get_base_url()}/{path}"

            # Check device status
            self._check_device_status(device)

            # Add device to list
            self.devices[device_id] = device

            # Save devices
            self._save_devices()

            # Publish device added event
            self.mcp_client.publish("network_devices/device/added", device.to_dict())

            logger.info(f"Added network device: {name} ({ip}:{port})")
            return device_id

        except Exception as e:
            logger.error(f"Error adding network device: {e}")
            raise

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
