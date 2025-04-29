"""
logging.py

This module provides logging configuration for the rtaspi package.
"""

# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RTASP - Real-Time Annotation and Stream Processing
Moduł konfiguracji logowania
"""

import os
import logging
import logging.handlers
from datetime import datetime


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)


def setup_logging(config):
    """
    Set up logging configuration for the rtaspi package.

    Args:
        config (dict): Configuration dictionary containing logging settings.
    """
    manager = LoggingManager(config)
    return manager


class LoggingManager:
    """Klasa zarządzająca konfiguracją logowania."""

    def __init__(self, config):
        """
        Inicjalizacja menedżera logowania.

        Args:
            config (dict): Konfiguracja systemu.
        """
        self.config = config
        self.log_level = self._get_log_level()
        self.log_dir = self._get_log_dir()
        self.log_file = self._get_log_file()

        # Utwórz katalog logów, jeśli nie istnieje
        os.makedirs(self.log_dir, exist_ok=True)

        # Skonfiguruj logowanie
        self.configure_logging()

    def _get_log_level(self):
        """
        Pobiera poziom logowania z konfiguracji.

        Returns:
            int: Poziom logowania (np. logging.INFO).
        """
        log_level_str = self.config.get("system", {}).get("log_level", "INFO")

        # Konwersja stringa na poziom logowania
        log_levels = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }

        return log_levels.get(log_level_str, logging.INFO)

    def _get_log_dir(self):
        """
        Pobiera katalog logów z konfiguracji.

        Returns:
            str: Ścieżka do katalogu logów.
        """
        storage_path = self.config.get("system", {}).get("storage_path", "storage")
        return os.path.join(storage_path, "logs")

    def _get_log_file(self):
        """
        Tworzy nazwę pliku logu na podstawie aktualnej daty.

        Returns:
            str: Ścieżka do pliku logu.
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.log_dir, f"rtasp_{date_str}.log")

    def configure_logging(self):
        """Konfiguruje system logowania."""
        # Utwórz formatery
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        )

        # Utwórz handlary
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(console_formatter)

        file_handler = logging.handlers.TimedRotatingFileHandler(
            self.log_file,
            when="midnight",
            backupCount=30,  # Przechowuj logi z ostatnich 30 dni
        )
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(file_formatter)

        # Skonfiguruj root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)

        # Usuń istniejące handlary, aby uniknąć duplikacji
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Dodaj nowe handlary
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

        # Skonfiguruj logger dla bibliotek zewnętrznych
        for logger_name in ["urllib3", "requests", "werkzeug"]:
            logging.getLogger(logger_name).setLevel(logging.WARNING)

        logging.info(
            f"Skonfigurowano logowanie, poziom: {logging.getLevelName(self.log_level)}, plik: {self.log_file}"
        )
