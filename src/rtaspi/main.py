#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rtaspi - Real-Time Annotation and Stream Processing
Główny plik uruchomieniowy systemu
"""

import os
import sys
import time
import signal
import argparse
import logging

from .core.config import ConfigManager
from .core.logging import LoggingManager
from .core.mcp import MCPBroker, MCPClient
from .core.utils import check_dependencies, get_system_info, ensure_dir

from .device_managers.local_devices import LocalDevicesManager
from .device_managers.network_devices import NetworkDevicesManager

logger = logging.getLogger("rtaspi")


class rtaspi:
    """Główna klasa systemu rtaspi."""

    def __init__(self, config_path=None):
        """
        Inicjalizacja systemu rtaspi.

        Args:
            config_path (str, optional): Ścieżka do pliku konfiguracyjnego.
        """
        self.running = False
        self.managers = {}

        # Inicjalizacja konfiguracji
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.config

        # Inicjalizacja logowania
        self.logging_manager = LoggingManager(self.config)

        # Inicjalizacja katalogu przechowywania
        storage_path = self.config.get("system", {}).get("storage_path", "storage")
        ensure_dir(storage_path)

        # Sprawdzenie zależności
        dependencies = check_dependencies()
        if not dependencies.get("ffmpeg", {}).get("installed", False):
            logger.warning(
                "FFmpeg nie jest zainstalowany, niektóre funkcje mogą nie działać"
            )

        # Inicjalizacja brokera MCP
        self.mcp_broker = MCPBroker()
        self.mcp_client = MCPClient(self.mcp_broker, client_id="rtaspi_main")

        # Rejestracja handlera do obsługi sygnałów
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("System rtaspi zainicjalizowany")

    def start(self):
        """Uruchamia system rtaspi."""
        if self.running:
            logger.warning("System rtaspi już jest uruchomiony")
            return

        logger.info("Uruchamianie systemu rtaspi...")
        self.running = True

        try:
            # Inicjalizacja i uruchomienie menedżera lokalnych urządzeń
            local_devices_manager = LocalDevicesManager(self.config, self.mcp_broker)
            local_devices_manager.start()
            self.managers["local_devices"] = local_devices_manager

            # Inicjalizacja i uruchomienie menedżera zdalnych urządzeń
            network_devices_manager = NetworkDevicesManager(
                self.config, self.mcp_broker
            )
            network_devices_manager.start()
            self.managers["network_devices"] = network_devices_manager

            # Publikacja informacji o uruchomieniu systemu
            self.mcp_client.publish(
                "system/status",
                {
                    "status": "started",
                    "timestamp": time.time(),
                    "info": get_system_info(),
                },
            )

            logger.info("System rtaspi uruchomiony")

        except Exception as e:
            logger.error(f"Błąd podczas uruchamiania systemu rtaspi: {e}")
            self.stop()

    def stop(self):
        """Zatrzymuje system rtaspi."""
        if not self.running:
            return

        logger.info("Zatrzymywanie systemu rtaspi...")
        self.running = False

        # Zatrzymanie wszystkich menedżerów
        for name, manager in self.managers.items():
            try:
                logger.info(f"Zatrzymywanie menedżera: {name}")
                manager.stop()
            except Exception as e:
                logger.error(f"Błąd podczas zatrzymywania menedżera {name}: {e}")

        # Publikacja informacji o zatrzymaniu systemu
        self.mcp_client.publish(
            "system/status", {"status": "stopped", "timestamp": time.time()}
        )

        # Zamknięcie klienta MCP
        self.mcp_client.close()

        logger.info("System rtaspi zatrzymany")

    def _signal_handler(self, sig, frame):
        """
        Obsługuje sygnały systemowe.

        Args:
            sig: Sygnał.
            frame: Ramka stosu.
        """
        logger.info(f"Otrzymano sygnał {sig}, zatrzymywanie...")
        self.stop()
        sys.exit(0)

    def run(self):
        """Uruchamia system rtaspi w pętli głównej."""
        self.start()

        try:
            # Pętla główna
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Przerwano działanie systemu")
        finally:
            self.stop()


def parse_args():
    """
    Parsuje argumenty wiersza poleceń.

    Returns:
        argparse.Namespace: Sparsowane argumenty.
    """
    parser = argparse.ArgumentParser(
        description="rtaspi - Real-Time Annotation and Stream Processing"
    )
    parser.add_argument("-c", "--config", help="Ścieżka do pliku konfiguracyjnego")
    return parser.parse_args()


if __name__ == "__main__":
    # Parsowanie argumentów
    args = parse_args()

    # Uruchomienie systemu
    rtaspi = rtaspi(config_path=args.config)
    rtaspi.run()
