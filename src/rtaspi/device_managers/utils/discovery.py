#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rtaspi - Real-Time Annotation and Stream Processing
Wykrywanie zdalnych urządzeń (ONVIF, UPnP, mDNS)
"""

import logging
import socket
import time
import re
from urllib.parse import urlparse
from abc import ABC, abstractmethod

logger = logging.getLogger("Discovery")


class DiscoveryModule(ABC):
    """Klasa bazowa dla modułów wykrywania urządzeń."""

    @abstractmethod
    def discover(self):
        """
        Wykrywa urządzenia w sieci.

        Returns:
            list: Lista słowników z informacjami o urządzeniach.
        """
        pass


class ONVIFDiscovery:
    def discover(self):
        try:
            logger.info("Wykrywanie urządzeń ONVIF...")

            # Import inside method to avoid circular imports
            from wsdiscovery import WSDiscovery
            from wsdiscovery.scope import Scope
            from wsdiscovery.qname import QName

            # Create proper QName objects instead of strings
            onvif_type = QName("http://www.onvif.org/ver10/network/wsdl", "NetworkVideoTransmitter")

            # Initialize discovery client
            wsd = WSDiscovery()
            wsd.start()

            # Search for ONVIF devices using the QName object
            ret = wsd.searchServices(types=[onvif_type])

            # Stop discovery client
            wsd.stop()

            # Process found devices
            discovered = []
            for service in ret:
                # Extract device information
                device_info = {
                    'name': service.getEPR() or 'ONVIF Camera',
                    'ip': self._extract_ip_from_xaddrs(service.getXAddrs()),
                    'port': self._extract_port_from_xaddrs(service.getXAddrs()),
                    'type': 'video',
                    'protocol': 'rtsp',
                    'paths': ['/onvif-media/media.amp']  # Default ONVIF path
                }

                if device_info['ip']:
                    discovered.append(device_info)

            logger.info(f"Wykryto {len(discovered)} urządzeń ONVIF")
            return discovered

        except Exception as e:
            logger.error(f"Błąd podczas wykrywania urządzeń ONVIF: {e}")
            return []

    def _extract_ip_from_xaddrs(self, xaddrs):
        """Extract IP address from ONVIF XAddrs."""
        if not xaddrs:
            return None

        try:
            url = xaddrs[0]
            parsed = urlparse(url)
            return parsed.hostname
        except Exception:
            return None

    def _extract_port_from_xaddrs(self, xaddrs):
        """Extract port from ONVIF XAddrs."""
        if not xaddrs:
            return 80

        try:
            url = xaddrs[0]
            parsed = urlparse(url)
            return parsed.port or 80
        except Exception:
            return 80


class UPnPDiscovery(DiscoveryModule):
    """Klasa do wykrywania urządzeń UPnP."""

    def discover(self):
        """
        Wykrywa urządzenia UPnP w sieci.

        Returns:
            list: Lista słowników z informacjami o urządzeniach.
        """
        logger.info("Wykrywanie urządzeń UPnP...")
        devices = []

        try:
            # Próba importu biblioteki upnpclient
            try:
                import upnpclient

                upnp_devices = upnpclient.discover(timeout=5)

                for upnp_device in upnp_devices:
                    try:
                        # Sprawdź, czy to urządzenie audio/wideo
                        is_av_device = False
                        device_type = upnp_device.device_type.lower()

                        if 'camera' in device_type or 'video' in device_type:
                            device_type = 'video'
                            is_av_device = True
                        elif 'audio' in device_type or 'sound' in device_type:
                            device_type = 'audio'
                            is_av_device = True

                        if not is_av_device:
                            continue

                        # Ekstrakcja informacji o urządzeniu
                        name = upnp_device.friendly_name
                        url_parts = urlparse(upnp_device.location)
                        ip = url_parts.hostname
                        port = url_parts.port or 80

                        # Dodanie urządzenia do listy
                        devices.append({
                            'name': name,
                            'ip': ip,
                            'port': port,
                            'type': device_type,
                            'protocol': 'http'
                        })

                    except Exception as e:
                        logger.warning(f"Błąd podczas przetwarzania urządzenia UPnP: {e}")

            except ImportError:
                logger.warning("Biblioteka upnpclient nie jest zainstalowana. Wykrywanie UPnP wyłączone.")

                # Alternatywna metoda - wysłanie wiadomości SSDP bez biblioteki
                try:
                    # Implementacja prostego wykrywania SSDP za pomocą socketa
                    msg = '''M-SEARCH * HTTP/1.1
Host: 239.255.255.250:1900
Man: "ssdp:discover"
ST: ssdp:all
MX: 5
'''

                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                    sock.settimeout(5)
                    sock.sendto(msg.encode(), ('239.255.255.250', 1900))

                    # Odbieranie odpowiedzi
                    while True:
                        try:
                            data, addr = sock.recvfrom(10240)
                            response = data.decode('utf-8')

                            # Parsowanie odpowiedzi
                            ip = addr[0]

                            # Ekstrakcja informacji o urządzeniu
                            location_match = re.search(r'LOCATION: (.*)', response, re.IGNORECASE)
                            if location_match:
                                location = location_match.group(1).strip()
                                url_parts = urlparse(location)
                                ip = url_parts.hostname
                                port = url_parts.port or 80

                                # Sprawdź, czy to urządzenie audio/wideo
                                device_type = 'video'  # Domyślnie zakładamy, że to urządzenie wideo
                                if 'audio' in response.lower() or 'sound' in response.lower():
                                    device_type = 'audio'

                                # Dodanie urządzenia do listy
                                devices.append({
                                    'name': f"UPnP Device ({ip})",
                                    'ip': ip,
                                    'port': port,
                                    'type': device_type,
                                    'protocol': 'http'
                                })
                        except socket.timeout:
                            break

                except Exception as e:
                    logger.warning(f"Błąd podczas alternatywnego wykrywania UPnP: {e}")

        except Exception as e:
            logger.error(f"Błąd podczas wykrywania urządzeń UPnP: {e}")

        logger.info(f"Wykryto {len(devices)} urządzeń UPnP")
        return devices


class MDNSDiscovery(DiscoveryModule):
    """Klasa do wykrywania urządzeń mDNS/Bonjour."""

    def discover(self):
        """
        Wykrywa urządzenia mDNS w sieci.

        Returns:
            list: Lista słowników z informacjami o urządzeniach.
        """
        logger.info("Wykrywanie urządzeń mDNS...")
        devices = []

        try:
            # Próba importu biblioteki zeroconf
            try:
                from zeroconf import ServiceBrowser, Zeroconf

                class MDNSListener:
                    def __init__(self):
                        self.found_devices = []

                    def add_service(self, zc, type, name):
                        info = zc.get_service_info(type, name)
                        if not info:
                            return

                        addresses = info.addresses
                        if not addresses:
                            return

                        ip = socket.inet_ntoa(addresses[0])
                        port = info.port
                        device_name = name.split('.')[0]

                        # Identyfikacja typu urządzenia
                        device_type = "video"  # Domyślnie video
                        if "camera" in type.lower() or "video" in type.lower():
                            device_type = "video"
                        elif "audio" in type.lower() or "sound" in type.lower():
                            device_type = "audio"

                        # Identyfikacja protokołu
                        protocol = "http"  # Domyślnie HTTP
                        if "rtsp" in type.lower():
                            protocol = "rtsp"
                        elif "rtmp" in type.lower():
                            protocol = "rtmp"

                        # Dodanie urządzenia do listy
                        self.found_devices.append({
                            'name': device_name,
                            'ip': ip,
                            'port': port,
                            'type': device_type,
                            'protocol': protocol
                        })

                    def remove_service(self, zc, type, name):
                        pass

                    def update_service(self, zc, type, name):
                        pass

                # Tworzenie przeszukiwacza mDNS
                zeroconf = Zeroconf()
                listener = MDNSListener()

                # Lista typów usług do monitorowania
                service_types = [
                    "_rtsp._tcp.local.",
                    "_http._tcp.local.",
                    "_vzocam._tcp.local.",
                    "_axis-video._tcp.local.",
                    "_daap._tcp.local.",
                    "_airplay._tcp.local."
                ]

                browsers = []
                for service_type in service_types:
                    browsers.append(ServiceBrowser(zeroconf, service_type, listener))

                # Czekaj na wyniki
                time.sleep(5)

                # Pobranie znalezionych urządzeń
                devices = listener.found_devices

                # Sprzątanie
                zeroconf.close()

            except ImportError:
                logger.warning("Biblioteka zeroconf nie jest zainstalowana. Wykrywanie mDNS wyłączone.")

                # Alternatywna metoda - inny pakiet do mDNS
                try:
                    import socket
                    import struct

                    # Implementacja prostego wykrywania mDNS za pomocą socketa
                    # To jest bardzo uproszczona implementacja i może nie działać poprawnie
                    multicast_group = '224.0.0.251'
                    port = 5353

                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock.settimeout(5)

                    # Przygotowanie zapytania mDNS
                    # Zapytanie o usługi _rtsp._tcp.local, _http._tcp.local
                    queries = [
                        b"\x00\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x05_rtsp\x04_tcp\x05local\x00\x00\x0c\x00\x01",
                        b"\x00\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x05_http\x04_tcp\x05local\x00\x00\x0c\x00\x01"
                    ]

                    for query in queries:
                        try:
                            sock.sendto(query, (multicast_group, port))

                            # Odbieranie odpowiedzi
                            while True:
                                try:
                                    data, addr = sock.recvfrom(1024)
                                    response = data.decode('utf-8', errors='ignore')

                                    # Ekstrakcja informacji o urządzeniu
                                    ip = addr[0]

                                    # Dodanie urządzenia do listy
                                    devices.append({
                                        'name': f"mDNS Device ({ip})",
                                        'ip': ip,
                                        'port': port,
                                        'type': 'video',  # Domyślnie video
                                        'protocol': 'rtsp' if '_rtsp._tcp' in response else 'http'
                                    })
                                except socket.timeout:
                                    break
                                    # Replace the incomplete try-except block at the end of the MDNSDiscovery.discover() method with:

                                except Exception as e:
                                    logger.warning(f"Błąd podczas alternatywnego wykrywania mDNS: {e}")

                        except Exception as e:
                            logger.warning(f"Błąd podczas alternatywnego wykrywania mDNS: {e}")

                        # Close the socket properly
                        try:
                            sock.close()
                        except Exception as e:
                            logger.warning(f"Error closing mDNS socket: {e}")

                except Exception as e:
                    logger.warning(f"Błąd podczas alternatywnego wykrywania mDNS: {e}")

        except Exception as e:
            logger.error(f"Błąd podczas wykrywania urządzeń mDNS: {e}")

        logger.info(f"Wykryto {len(devices)} urządzeń mDNS")
        return devices
