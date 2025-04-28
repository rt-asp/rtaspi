"""
config.py
"""

# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rtaspi - Real-Time Annotation and Stream Processing
Moduł obsługi konfiguracji
"""

import os
import logging
import yaml
from pathlib import Path

logger = logging.getLogger("Config")


class ConfigManager:
    """Klasa zarządzająca konfiguracją systemu."""

    def __init__(self, config_path=None):
        """
        Inicjalizacja menedżera konfiguracji.

        Args:
            config_path (str, optional): Ścieżka do pliku konfiguracyjnego.
        """
        self.config_path = config_path or os.environ.get('rtaspi_CONFIG', 'config.yaml')
        self.config = self.load_config()

    def load_config(self):
        """
        Ładuje konfigurację z pliku.

        Returns:
            dict: Słownik konfiguracji.
        """
        # Domyślna konfiguracja
        default_config = {
            'system': {
                'storage_path': 'storage',
                'log_level': 'INFO'
            },
            'local_devices': {
                'enable_video': True,
                'enable_audio': True,
                'auto_start': False,
                'scan_interval': 60,
                'rtsp_port_start': 8554,
                'rtmp_port_start': 1935,
                'webrtc_port_start': 8080
            },
            'network_devices': {
                'enable': True,
                'scan_interval': 60,
                'discovery_enabled': True,
                'discovery_methods': ['onvif', 'upnp', 'mdns'],
                'rtsp_port_start': 8654,
                'rtmp_port_start': 2935,
                'webrtc_port_start': 9080
            },
            'streaming': {
                'rtsp': {
                    'port_start': 8554
                },
                'rtmp': {
                    'port_start': 1935
                },
                'webrtc': {
                    'port_start': 8080,
                    'stun_server': 'stun://stun.l.google.com:19302',
                    'turn_server': '',
                    'turn_username': '',
                    'turn_password': ''
                }
            }
        }

        config = default_config.copy()

        try:
            # Sprawdź, czy plik konfiguracyjny istnieje
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    loaded_config = yaml.safe_load(f)

                # Aktualizacja konfiguracji
                if loaded_config:
                    self._update_dict(config, loaded_config)

                logger.info(f"Załadowano konfigurację z pliku: {self.config_path}")
            else:
                logger.warning(
                    f"Nie znaleziono pliku konfiguracyjnego: {self.config_path}, używam domyślnej konfiguracji")

                # Zapisz domyślną konfigurację
                self.save_config(config)

        except Exception as e:
            logger.error(f"Błąd podczas ładowania konfiguracji: {e}")

        return config

    def save_config(self, config=None):
        """
        Zapisuje konfigurację do pliku.

        Args:
            config (dict, optional): Konfiguracja do zapisania. Jeśli None, używa bieżącej konfiguracji.

        Returns:
            bool: True jeśli zapisano pomyślnie, False w przeciwnym razie.
        """
        try:
            # Użyj bieżącej konfiguracji, jeśli nie podano innej
            config = config or self.config

            # Utwórz katalogi, jeśli nie istnieją
            os.makedirs(os.path.dirname(os.path.abspath(self.config_path)), exist_ok=True)

            # Zapisz konfigurację do pliku
            with open(self.config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)

            logger.info(f"Zapisano konfigurację do pliku: {self.config_path}")
            return True

        except Exception as e:
            logger.error(f"Błąd podczas zapisywania konfiguracji: {e}")
            return False

    def get(self, key, default=None):
        """
        Pobiera wartość z konfiguracji.

        Args:
            key (str): Klucz konfiguracji, może zawierać kropki dla zagnieżdżonych słowników.
            default: Wartość domyślna, jeśli klucz nie istnieje.

        Returns:
            Wartość konfiguracji lub default, jeśli klucz nie istnieje.
        """
        value = self.config

        # Obsługa zagnieżdżonych słowników
        for part in key.split('.'):
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default

        return value

    def set(self, key, value):
        """
        Ustawia wartość w konfiguracji.

        Args:
            key (str): Klucz konfiguracji, może zawierać kropki dla zagnieżdżonych słowników.
            value: Wartość do ustawienia.

        Returns:
            bool: True jeśli ustawiono pomyślnie, False w przeciwnym razie.
        """
        try:
            # Obsługa zagnieżdżonych słowników
            parts = key.split('.')
            current = self.config

            # Przejdź do odpowiedniego zagnieżdżenia
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]

            # Ustaw wartość
            current[parts[-1]] = value

            return True

        except Exception as e:
            logger.error(f"Błąd podczas ustawiania konfiguracji: {e}")
            return False

    def _update_dict(self, dest, source):
        """
        Aktualizuje słownik docelowy wartościami ze słownika źródłowego.

        Args:
            dest (dict): Słownik docelowy.
            source (dict): Słownik źródłowy.
        """
        for key, value in source.items():
            if key in dest and isinstance(dest[key], dict) and isinstance(value, dict):
                self._update_dict(dest[key], value)
            else:
                dest[key] = value