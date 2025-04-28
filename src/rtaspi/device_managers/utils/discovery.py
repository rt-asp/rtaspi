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


class ONVIFDiscovery(DiscoveryModule):
    """Klasa do wykrywania urządzeń ONVIF."""

    def discover(self):
        """
        Wykrywa urządzenia ONVIF w sieci.

        Returns:
            list: Lista słowników z informacjami o urządzeniach.
        """
        logger.info("Wykrywanie urządzeń ONVIF...")
        devices = []

        try:
            # Próba importu biblioteki ONVIF
            try:
                # Import biblioteki onvif-zeep
                from onvif import ONVIFCamera, ONVIFService
                import zeep

                # Wykrywanie urządzeń za pomocą WS-Discovery
                from wsdiscovery.discovery import ThreadedWSDiscovery
                from wsdiscovery.scope import Scope

                wsd = ThreadedWSDiscovery()
                wsd.start()

                # Szukaj urządzeń ONVIF
                ttype = "http://www.onvif.org/ver10/device/wsdl"
                scopes = [Scope("onvif://www.onvif.org")]
                discovered = wsd.searchServices(types=[ttype], scopes=scopes, timeout=5)
                wsd.stop()

                for service in discovered:
                    # Ekstrakcja informacji o urządzeniu
                    xaddrs = service.getXAddrs()
                    if not xaddrs:
                        continue

                    xaddr = xaddrs[0]
                    try:
                        # Parsuj adres
                        url_parts = urlparse(xaddr)
                        ip = url_parts.hostname
                        port = url_parts.port or 80

                        # Tworzenie nazwy
                        name = f"ONVIF Camera ({ip})"

                        # Spróbuj połączyć się z urządzeniem, aby uzyskać więcej informacji
                        try:
                            cam = ONVIFCamera(ip, port, '', '')
                            device_info = cam.devicemgmt.GetDeviceInformation()
                            if device_info.Manufacturer or device_info.Model:
                                name = f"{device_info.Manufacturer} {device_info.Model}"

                            # Pobranie profili mediów, aby uzyskać ścieżki RTSP
                            media_service = cam.create_media_service()
                            profiles = media_service.GetProfiles()

                            # Ścieżki RTSP
                            paths = []
                            for profile in profiles:
                                try:
                                    params = {
                                        'ProfileToken': profile.token,
                                        'Protocol': 'RTSP'
                                    }
                                    uri = media_service.GetStreamUri(params)
                                    if uri and uri.Uri:
                                        # Ekstrakcja ścieżki z pełnego URI
                                        uri_parts = urlparse(uri.Uri)
                                        path = uri_parts.path
                                        if path.startswith('/'):
                                            path = path[1:]  # Usuń początkowy ukośnik
                                        paths.append(path)
                                except Exception as e:
                                    logger.warning(f"Błąd podczas pobierania URI strumienia: {e}")
                        except Exception as e:
                            logger.warning(f"Nie można uzyskać informacji o urządzeniu ONVIF: {e}")
                            paths = ["onvif1"]  # Domyślna ścieżka

                        # Dodanie urządzenia do listy
                        devices.append({
                            'name': name,
                            'ip': ip,
                            'port': port,
                            'type': 'video',
                            'protocol': 'rtsp',
                            'paths': paths
                        })

                    except Exception as e:
                        logger.warning(f"Błąd podczas przetwarzania urządzenia ONVIF: {e}")

            except ImportError:
                logger.warning(
                    "Biblioteka python-onvif lub wsdiscovery nie jest zainstalowana. Wykrywanie ONVIF wyłączone.")

                # Alternatywna metoda - wysłanie wiadomości WS-Discovery bez biblioteki
                try:
                    # Implementacja prostego wykrywania WS-Discovery za pomocą socketa
                    msg = '''<?xml version="1.0" encoding="UTF-8"?>
                    <e:Envelope xmlns:e="http://www.w3.org/2003/05/soap-envelope" xmlns:w="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:d="http://schemas.xmlsoap.org/ws/2005/04/discovery" xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
                        <e:Header>
                            <w:MessageID>uuid:84ede3de-7dec-11d0-c360-F01234567890</w:MessageID>
                            <w:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</w:To>
                            <w:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</w:Action>
                        </e:Header>
                        <e:Body>
                            <d:Probe>
                                <d:Types>tds:Device</d:Types>
                            </d:Probe>
                        </e:Body>
                    </e:Envelope>'''

                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                    sock.settimeout(5)
                    sock.sendto(msg.encode(), ('239.255.255.250', 3702))

                    # Odbieranie odpowiedzi
                    while True:
                        try:
                            data, addr = sock.recvfrom(10240)
                            response = data.decode('utf-8')

                            # Parsowanie odpowiedzi
                            ip = addr[0]

                            # Ekstrakcja XAddrs z odpowiedzi
                            xaddrs_match = re.search(r'<d:XAddrs>(.*?)</d:XAddrs>', response)
                            if xaddrs_match:
                                xaddrs = xaddrs_match.group(1).split()
                                for xaddr in xaddrs:
                                    try:
                                        url_parts = urlparse(xaddr)
                                        ip = url_parts.hostname
                                        port = url_parts.port or 80

                                        # Dodanie urządzenia do listy
                                        devices.append({
                                            'name': f"ONVIF Camera ({ip})",
                                            'ip': ip,
                                            'port': port,
                                            'type': 'video',
                                            'protocol': 'rtsp',
                                            'paths': ["onvif1"]  # Domyślna ścieżka
                                        })
                                    except Exception as e:
                                        logger.warning(f"Błąd podczas parsowania XAddr: {e}")
                        except socket.timeout:
                            break

                except Exception as e:
                    logger.warning(f"Błąd podczas alternatywnego wykrywania ONVIF: {e}")

        except Exception as e:
            logger.error(f"Błąd podczas wykrywania urządzeń ONVIF: {e}")

        logger.info(f"Wykryto {len(devices)} urządzeń ONVIF")
        return devices


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
                        b"\x00\x01\x00\x00\x00\x01\x00\x00\x00\x