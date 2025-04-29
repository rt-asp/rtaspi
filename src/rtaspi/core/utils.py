#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rtaspi - Real-Time Annotation and Stream Processing
Narzędzia pomocnicze
"""

import os
import sys
import psutil
import platform
import socket
import uuid
import time
import json
import logging
import subprocess
import shutil
from pathlib import Path

logger = logging.getLogger("Utils")


def get_system_info():
    """
    Pobiera informacje o systemie.

    Returns:
        dict: Słownik z informacjami o systemie.
    """
    info = {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "hostname": socket.gethostname(),
        "ip_address": get_local_ip(),
        "python_version": sys.version,
        "cpu_count": psutil.cpu_count(),
        "memory_total": psutil.virtual_memory().total,
        "memory_available": psutil.virtual_memory().available,
        "disk_total": psutil.disk_usage("/").total,
        "disk_free": psutil.disk_usage("/").free,
        "mac_address": get_mac_address(),
        "timestamp": time.time(),
    }

    return info


def get_local_ip():
    """
    Pobiera lokalny adres IP.

    Returns:
        str: Lokalny adres IP.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        logger.warning(f"Błąd podczas pobierania lokalnego adresu IP: {e}")
        return "127.0.0.1"


def get_mac_address():
    """
    Pobiera adres MAC.

    Returns:
        str: Adres MAC.
    """
    try:
        return ":".join(
            [
                "{:02x}".format((uuid.getnode() >> elements) & 0xFF)
                for elements in range(0, 48, 8)
            ][::-1]
        )
    except Exception as e:
        logger.warning(f"Błąd podczas pobierania adresu MAC: {e}")
        return "00:00:00:00:00:00"


def check_command_exists(command):
    """
    Sprawdza czy komenda istnieje w systemie.

    Args:
        command (str): Nazwa komendy.

    Returns:
        bool: True jeśli komenda istnieje, False w przeciwnym razie.
    """
    return shutil.which(command) is not None


def check_ffmpeg():
    """
    Sprawdza czy FFmpeg jest zainstalowany i zwraca informacje o wersji.

    Returns:
        dict: Słownik z informacjami o FFmpeg lub None, jeśli nie jest zainstalowany.
    """
    if not check_command_exists("ffmpeg"):
        logger.warning("FFmpeg nie jest zainstalowany")
        return None

    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        output = result.stdout.decode("utf-8")

        info = {"installed": True, "version": output.split("\n")[0]}

        # Sprawdzenie obsługiwanych kodeków
        result = subprocess.run(
            ["ffmpeg", "-codecs"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        output = result.stdout.decode("utf-8")

        codecs = {"video": [], "audio": []}

        for line in output.split("\n"):
            if line.startswith(" D") or line.startswith(" E"):
                parts = line.split()
                if len(parts) > 2:
                    codec_type = parts[0]
                    codec_name = parts[1]

                    if "V" in codec_type:
                        codecs["video"].append(codec_name)
                    elif "A" in codec_type:
                        codecs["audio"].append(codec_name)

        info["codecs"] = codecs

        return info

    except Exception as e:
        logger.warning(f"Błąd podczas sprawdzania FFmpeg: {e}")
        return None


def check_gstreamer():
    """
    Sprawdza czy GStreamer jest zainstalowany i zwraca informacje o wersji.

    Returns:
        dict: Słownik z informacjami o GStreamer lub None, jeśli nie jest zainstalowany.
    """
    if not check_command_exists("gst-launch-1.0"):
        logger.warning("GStreamer nie jest zainstalowany")
        return None

    try:
        result = subprocess.run(
            ["gst-launch-1.0", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        output = result.stdout.decode("utf-8")

        info = {"installed": True, "version": output.split("\n")[0]}

        # Sprawdzenie dostępnych pluginów
        result = subprocess.run(
            ["gst-inspect-1.0"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        output = result.stdout.decode("utf-8")

        plugins = []
        for line in output.split("\n"):
            if line and not line.startswith("Blacklisted"):
                parts = line.split(":")
                if len(parts) > 1:
                    plugins.append(parts[0].strip())

        info["plugins"] = plugins

        return info

    except Exception as e:
        logger.warning(f"Błąd podczas sprawdzania GStreamer: {e}")
        return None


def check_nginx():
    """
    Sprawdza czy NGINX jest zainstalowany i zwraca informacje o wersji.

    Returns:
        dict: Słownik z informacjami o NGINX lub None, jeśli nie jest zainstalowany.
    """
    if not check_command_exists("nginx"):
        logger.warning("NGINX nie jest zainstalowany")
        return None

    try:
        result = subprocess.run(
            ["nginx", "-v"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        output = result.stderr.decode("utf-8")  # nginx -v wypisuje wersję na stderr

        info = {"installed": True, "version": output.strip()}

        # Sprawdzenie, czy ma moduł RTMP
        result = subprocess.run(
            ["nginx", "-V"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        output = result.stderr.decode(
            "utf-8"
        )  # nginx -V wypisuje konfigurację na stderr

        has_rtmp = "rtmp" in output.lower()
        info["rtmp_module"] = has_rtmp

        return info

    except Exception as e:
        logger.warning(f"Błąd podczas sprawdzania NGINX: {e}")
        return None


def check_dependencies():
    """
    Sprawdza wszystkie zależności systemu rtaspi.

    Returns:
        dict: Słownik z informacjami o zależnościach.
    """
    dependencies = {
        "ffmpeg": check_ffmpeg(),
        "gstreamer": check_gstreamer(),
        "nginx": check_nginx(),
        "system": get_system_info(),
    }

    return dependencies


def generate_unique_id():
    """
    Generuje unikalny identyfikator.

    Returns:
        str: Unikalny identyfikator.
    """
    return str(uuid.uuid4())


def ensure_dir(path):
    """
    Tworzy katalog, jeśli nie istnieje.

    Args:
        path (str): Ścieżka do katalogu.

    Returns:
        bool: True jeśli katalog istnieje lub został utworzony, False w przeciwnym razie.
    """
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Błąd podczas tworzenia katalogu {path}: {e}")
        return False


def write_json(data, path):
    """
    Zapisuje dane do pliku JSON.

    Args:
        data: Dane do zapisania.
        path (str): Ścieżka do pliku.

    Returns:
        bool: True jeśli zapisano pomyślnie, False w przeciwnym razie.
    """
    try:
        # Utwórz katalog, jeśli nie istnieje
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

        # Zapisz dane do pliku
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return True

    except Exception as e:
        logger.error(f"Błąd podczas zapisywania pliku JSON {path}: {e}")
        return False


def read_json(path):
    """
    Wczytuje dane z pliku JSON.

    Args:
        path (str): Ścieżka do pliku.

    Returns:
        Wczytane dane lub None, jeśli wystąpił błąd.
    """
    try:
        if not os.path.exists(path):
            return None

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception as e:
        logger.error(f"Błąd podczas wczytywania pliku JSON {path}: {e}")
        return None


def get_version():
    """
    Get the package version from _version.py.

    Returns:
        str: The package version.
    """
    try:
        version_file = Path(__file__).parent.parent / "_version.py"
        with open(version_file, "r") as f:
            version_content = {}
            exec(f.read(), version_content)
            return version_content.get("__version__", "unknown")
    except Exception as e:
        logger.error(f"Error reading version: {e}")
        return "unknown"
