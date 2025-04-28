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

from device_managers.base import DeviceManager
from device_managers.utils.device import NetworkDevice
from device_managers.utils.discovery import ONVIFDiscovery, UPnPDiscovery, MDNSDiscovery
from streaming.rtsp import RTSPServer
from streaming.rtmp import RTMPServer
from streaming.webrtc import WebRTCServer

logger = logging.getLogger("NetworkDevices")

class NetworkDevicesManager(DeviceManager):
    """Klasa zarządzająca zdalnymi urządzeniami sieciowymi."""
    
    def __init__(self, config, mcp_broker):
        """
        Inicjalizacja menedżera zdalnych urządzeń.
        
        Args:
            config (dict): Konfiguracja menedżera.
            mcp_broker (MCPBroker): Broker protokołu MCP.
        """
        super().__init__(config, mcp_broker)
        
        # Pobranie konfiguracji z pliku
        network_devices_config = config.get('network_devices', {})
        self.enable = network_devices_config.get('enable', True)
        self.scan_interval = network_devices_config.get('scan_interval', 60)  # sekund
        self.discovery_enabled = network_devices_config.get('discovery_enabled', True)
        self.discovery_methods = network_devices_config.get('discovery_methods', ['onvif', 'upnp', 'mdns'])
        self.rtsp_port_start = network_devices_config.get('rtsp_port_start', 8554)
        self.rtmp_port_start = network_devices_config.get('rtmp_port_start', 1935)
        self.webrtc_port_start = network_devices_config.get('webrtc_port_start', 8080)
        
        # Inicjalizacja modułów wykrywania
        self.discovery_modules = {
            'onvif': ONVIFDiscovery(),
            'upnp': UPnPDiscovery(),
            'mdns': MDNSDiscovery()
        }
        
        # Inicjalizacja serwerów streamingu
        self.rtsp_server = RTSPServer(config)
        self.rtmp_server = RTMPServer(config)
        self.webrtc_server = WebRTCServer(config)
        
        # Przygotowanie katalogów
        self.network_streams_path = os.path.join(self.storage_path, 'network_streams')
        os.makedirs(self.network_streams_path, exist_ok=True)
        
        # Ścieżka do pliku z zapisanymi urządzeniami
        self.devices_file = os.path.join(self.storage_path, 'network_devices.json')
        
        # Ładowanie zapisanych urządzeń
        self._load_saved_devices()
        
    def _get_client_id(self):
        """
        Zwraca identyfikator klienta MCP.
        
        Returns:
            str: Identyfikator klienta MCP.
        """
        return "network_devices_manager"
        
    def _get_scan_interval(self):
        """
        Zwraca interwał skanowania w sekundach.
        
        Returns:
            int: Interwał skanowania w sekundach.
        """
        return self.scan_interval
        
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
        """Wykrywa nowe urządzenia sieciowe."""
        try:
            for method in self.discovery_methods:
                if method in self.discovery_modules:
                    logger.debug(f"Uruchamianie wykrywania urządzeń metodą {method}")
                    discovered_devices = self.discovery_modules[method].discover()
                    
                    # Dodanie nowych urządzeń
                    for device_info in discovered_devices:
                        # Sprawdzenie, czy urządzenie już istnieje
                        ip = device_info.get('ip')
                        port = device_info.get('port')
                        
                        device_exists = False
                        for device in self.devices.values():
                            if device.ip == ip and device.port == port:
                                device_exists = True
                                break
                                
                        if not device_exists:
                            # Dodanie nowego urządzenia
                            self.add_device(
                                name=device_info.get('name', f"Urządzenie {ip}"),
                                ip=ip,
                                port=port,
                                type=device_info.get('type', 'video'),
                                protocol=device_info.get('protocol', 'rtsp'),
                                username=device_info.get('username', ''),
                                password=device_info.get('password', ''),
                                paths=device_info.get('paths', [])
                            )
                            
        except Exception as e:
            logger.error(f"Błąd podczas wykrywania urządzeń: {e}")
            
    def add_device(self, name, ip, port, username="", password="", type="video", protocol="rtsp", paths=None):
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
            bool: True jeśli usun