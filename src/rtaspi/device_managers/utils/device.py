"""
device.py
"""

# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rtaspi - Real-Time Annotation and Stream Processing
Klasy bazowe dla urządzeń audio/wideo
"""

import time
import logging
from abc import ABC, abstractmethod
from enum import Enum, auto

logger = logging.getLogger("Devices")


class DeviceStatus(Enum):
    """Status urządzenia."""

    UNKNOWN = auto()
    ONLINE = auto()
    OFFLINE = auto()


class Device(ABC):
    """Klasa bazowa dla wszystkich urządzeń."""

    def __init__(self, device_id, name, type):
        """
        Inicjalizacja urządzenia.

        Args:
            device_id (str): Unikalny identyfikator urządzenia.
            name (str): Przyjazna nazwa urządzenia.
            type (str): Typ urządzenia ('video' lub 'audio').
        """
        self.device_id = device_id
        self.name = name
        self.type = type
        self.status = DeviceStatus.UNKNOWN
        self.last_check = 0  # timestamp ostatniego sprawdzenia

    @abstractmethod
    def to_dict(self):
        """
        Konwertuje obiekt na słownik do serializacji.

        Returns:
            dict: Reprezentacja urządzenia jako słownik.
        """
        return {
            "id": self.device_id,
            "name": self.name,
            "type": self.type,
            "status": self.status.name.lower(),
        }


class LocalDevice(Device):
    """Klasa reprezentująca lokalne urządzenie (kamera, mikrofon)."""

    def __init__(self, device_id, name, type, system_path, driver="default"):
        """
        Inicjalizacja lokalnego urządzenia.

        Args:
            device_id (str): Unikalny identyfikator urządzenia.
            name (str): Przyjazna nazwa urządzenia.
            type (str): Typ urządzenia ('video' lub 'audio').
            system_path (str): Ścieżka systemowa do urządzenia.
            driver (str): Sterownik urządzenia.
        """
        super().__init__(device_id, name, type)
        self.system_path = system_path
        self.driver = driver
        self.formats = []
        self.resolutions = []

    def to_dict(self):
        """
        Konwertuje obiekt na słownik do serializacji.

        Returns:
            dict: Reprezentacja urządzenia jako słownik.
        """
        result = super().to_dict()
        result.update(
            {
                "system_path": self.system_path,
                "driver": self.driver,
                "formats": self.formats,
                "resolutions": self.resolutions,
            }
        )
        return result


class NetworkDevice(Device):
    """Klasa reprezentująca zdalne urządzenie sieciowe (kamera IP, mikrofon IP)."""

    def __init__(
        self, device_id, name, type, ip, port, username="", password="", protocol="rtsp"
    ):
        """
        Inicjalizacja urządzenia sieciowego.

        Args:
            device_id (str): Unikalny identyfikator urządzenia.
            name (str): Przyjazna nazwa urządzenia.
            type (str): Typ urządzenia ('video' lub 'audio').
            ip (str): Adres IP urządzenia.
            port (int): Port urządzenia.
            username (str): Nazwa użytkownika do uwierzytelnienia.
            password (str): Hasło do uwierzytelnienia.
            protocol (str): Protokół ('rtsp', 'rtmp', 'http', etc.).
        """
        super().__init__(device_id, name, type)
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.protocol = protocol
        self.streams = {}  # stream_id -> url

    def to_dict(self):
        """
        Konwertuje obiekt na słownik do serializacji.

        Returns:
            dict: Reprezentacja urządzenia jako słownik.
        """
        result = super().to_dict()
        result.update(
            {
                "ip": self.ip,
                "port": self.port,
                "protocol": self.protocol,
                "streams": self.streams,
            }
        )
        # Nie zwracamy wrażliwych danych (username, password)
        return result

    def get_base_url(self):
        """
        Zwraca podstawowy URL urządzenia.

        Returns:
            str: Podstawowy URL urządzenia.
        """
        auth = ""
        if self.username:
            if self.password:
                auth = f"{self.username}:{self.password}@"
            else:
                auth = f"{self.username}@"

        return f"{self.protocol}://{auth}{self.ip}:{self.port}"
