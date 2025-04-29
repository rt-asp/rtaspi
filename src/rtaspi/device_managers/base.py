"""
base.py
"""

# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rtaspi - Real-Time Annotation and Stream Processing
Podstawowa klasa menedżera urządzeń i urządzenia
"""

import os
import json
import logging
import threading
import time
import socket
import subprocess
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from ..core.mcp import MCPClient


logger = logging.getLogger("NetworkDevices")


class BaseDevice(ABC):
    """Base class for all devices."""

    def __init__(self, device_id: str, name: str, device_type: str):
        """
        Initialize base device.

        Args:
            device_id (str): Unique device identifier
            name (str): Human-readable device name
            device_type (str): Type of device (e.g. 'video', 'audio', etc.)
        """
        self.device_id = device_id
        self.name = name
        self.type = device_type
        self.connected = False
        self.error = None
        self.metadata: Dict[str, Any] = {}

    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to the device.

        Returns:
            bool: True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """
        Disconnect from the device.

        Returns:
            bool: True if disconnection successful, False otherwise
        """
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Get current device status.

        Returns:
            dict: Dictionary containing device status information
        """
        pass

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert device information to dictionary.

        Returns:
            dict: Dictionary containing device information
        """
        return {
            "device_id": self.device_id,
            "name": self.name,
            "type": self.type,
            "connected": self.connected,
            "error": str(self.error) if self.error else None,
            "metadata": self.metadata
        }

    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Update device metadata.

        Args:
            metadata (dict): New metadata to update/add
        """
        self.metadata.update(metadata)


class DeviceManager(ABC):
    """Klasa bazowa dla menedżerów urządzeń."""

    def __init__(self, config, mcp_broker):
        """
        Inicjalizacja menedżera urządzeń.

        Args:
            config (dict): Konfiguracja menedżera.
            mcp_broker (MCPBroker): Broker komunikacji.
        """
        self.config = config
        self.mcp_broker = mcp_broker
        self.running = False
        self.scan_thread = None
        self.devices = {}  # device_id -> device_info
        self.streams = {}  # stream_id -> stream_info

        # Przygotowanie katalogów
        self.storage_path = config.get("system", {}).get("storage_path", "storage")
        os.makedirs(self.storage_path, exist_ok=True)

        # Utworzenie klienta MCP
        self.mcp_client = MCPClient(mcp_broker, client_id=self._get_client_id())

    @abstractmethod
    def _get_client_id(self):
        """
        Zwraca identyfikator klienta MCP.

        Returns:
            str: Identyfikator klienta MCP.
        """
        pass

    @abstractmethod
    def _scan_devices(self):
        """Skanuje urządzenia."""
        pass

    def start_stream(self, device_id, stream_path=None):
        """
        Starts a stream from the specified device.

        Args:
            device_id (str): The ID of the device to stream from.
            stream_path (str, optional): The specific stream path to use.

        Returns:
            bool: True if the stream was started successfully, False otherwise.
        """
        # Implementation logic here
        # This is just a placeholder implementation
        logger.info(f"Starting stream from device {device_id}")
        # Your actual implementation would connect to the device and start streaming
        return True

    def start(self):
        """Uruchamia menedżer urządzeń."""
        if self.running:
            return

        self.running = True
        logger.info(f"Uruchamianie menedżera urządzeń: {self._get_client_id()}")

        # Subskrypcja zdarzeń MCP
        self._subscribe_to_events()

        # Uruchomienie wątku skanowania
        self.scan_thread = threading.Thread(target=self._scan_loop)
        self.scan_thread.daemon = True
        self.scan_thread.start()

        logger.info(f"Menedżer urządzeń uruchomiony: {self._get_client_id()}")

    def stop(self):
        """Zatrzymuje menedżer urządzeń."""
        if not self.running:
            return

        self.running = False
        logger.info(f"Zatrzymywanie menedżera urządzeń: {self._get_client_id()}")

        # Zatrzymanie wszystkich strumieni
        for stream_id in list(self.streams.keys()):
            self.stop_stream(stream_id)

        # Zatrzymanie wątku skanowania
        if self.scan_thread:
            self.scan_thread.join(timeout=5)

        # Wyrejestrowanie z MCP
        self.mcp_client.close()

        logger.info(f"Menedżer urządzeń zatrzymany: {self._get_client_id()}")

    def _subscribe_to_events(self):
        """Subskrybuje zdarzenia MCP."""
        pass  # Do implementacji w klasach pochodnych

    def _scan_loop(self):
        """Główna pętla skanowania urządzeń."""
        while self.running:
            logger.debug(f"Skanowanie urządzeń: {self._get_client_id()}")

            try:
                # Skanowanie urządzeń
                self._scan_devices()

                # Publikacja informacji o urządzeniach
                self._publish_devices_info()

            except Exception as e:
                logger.error(f"Błąd podczas skanowania urządzeń: {e}")

            # Oczekiwanie na następne skanowanie
            for _ in range(self._get_scan_interval()):
                if not self.running:
                    break
                time.sleep(1)

    def _get_scan_interval(self):
        """
        Zwraca interwał skanowania w sekundach.

        Returns:
            int: Interwał skanowania w sekundach.
        """
        return 60  # Domyślny interwał

    def _publish_devices_info(self):
        """Publikuje informacje o urządzeniach."""
        pass  # Do implementacji w klasach pochodnych

    def get_devices(self):
        """
        Zwraca listę urządzeń.

        Returns:
            dict: Słownik urządzeń.
        """
        return self.devices

    def get_streams(self):
        """
        Zwraca listę strumieni.

        Returns:
            dict: Słownik strumieni.
        """
        return {
            stream_id: {k: v for k, v in info.items() if k != "process"}
            for stream_id, info in self.streams.items()
        }

    def stop_stream(self, stream_id):
        """
        Zatrzymuje strumień.

        Args:
            stream_id (str): Identyfikator strumienia.

        Returns:
            bool: True jeśli zatrzymano pomyślnie, False w przeciwnym razie.
        """
        if stream_id not in self.streams:
            logger.error(f"Nieznany strumień: {stream_id}")
            return False

        try:
            # Pobranie informacji o strumieniu
            stream_info = self.streams[stream_id]

            # Zatrzymanie procesu
            process = stream_info.get("process")
            if process:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()

            # Zatrzymanie dodatkowych procesów
            for key in [
                "rtsp_process",
                "rtmp_process",
                "http_process",
                "nginx_process",
            ]:
                proc = stream_info.get(key)
                if proc:
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()

            # Usunięcie strumienia z listy
            self.streams.pop(stream_id)

            logger.info(f"Zatrzymano strumień {stream_id}")

            # Publikacja informacji o zatrzymaniu strumienia
            self._publish_stream_stopped(stream_id, stream_info)

            return True

        except Exception as e:
            logger.error(f"Błąd podczas zatrzymywania strumienia {stream_id}: {e}")
            return False

    def _publish_stream_stopped(self, stream_id, stream_info):
        """
        Publikuje informację o zatrzymaniu strumienia.

        Args:
            stream_id (str): Identyfikator strumienia.
            stream_info (dict): Informacje o strumieniu.
        """
        pass  # Do implementacji w klasach pochodnych

    def find_free_port(self, start_port):
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
            result = sock.connect_ex(("127.0.0.1", port))
            sock.close()

            if result != 0:  # Port jest wolny
                return port

            port += 1

        raise Exception(
            f"Nie znaleziono wolnego portu w zakresie {start_port}-{max_port}"
        )
