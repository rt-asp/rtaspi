"""
rtaspi - Real-Time Annotation and Stream Processing
Device discovery module for ONVIF, UPnP, and mDNS devices.
"""

import logging
import socket
import time
import re
from typing import List, Optional
from urllib.parse import urlparse
from abc import ABC, abstractmethod

from ...constants.devices import DeviceType, DeviceCapability
from ...constants.protocols import ProtocolType
from ...schemas.device import DeviceConfig
from ..scanners import get_platform_scanner

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
    def discover(self):
        """
        Wykrywa urządzenia ONVIF w sieci.

        Returns:
            list: Lista słowników z informacjami o urządzeniach.
        """
        logger.info("Wykrywanie urządzeń ONVIF...")
        try:
            # Próba użycia biblioteki
            try:
                return self._discover_with_library()
            except ImportError:
                logger.warning(
                    "Biblioteka ONVIF nie jest dostępna. Używam alternatywnej metody."
                )
                return self._discover_alternative()
        except Exception as e:
            logger.error(f"Błąd podczas wykrywania urządzeń ONVIF: {e}")
            return []

    def _discover_with_library(self):
        """
        Wykrywa urządzenia ONVIF używając biblioteki wsdiscovery.
        """
        from wsdiscovery import WSDiscovery
        from wsdiscovery.scope import Scope
        from wsdiscovery.qname import QName

        onvif_type = QName(
            "http://www.onvif.org/ver10/network/wsdl", "NetworkVideoTransmitter"
        )
        wsd = WSDiscovery()
        wsd.start()
        ret = wsd.searchServices(types=[onvif_type])
        wsd.stop()

        discovered = []
        for service in ret:
            device_info = {
                "name": service.getEPR() or "ONVIF Camera",
                "ip": self._extract_ip_from_xaddrs(service.getXAddrs()),
                "port": self._extract_port_from_xaddrs(service.getXAddrs()),
                "type": DeviceType.IP_CAMERA.name,
                "protocol": ProtocolType.RTSP.value,
                "paths": ["/onvif-media/media.amp"],
            }
            if device_info["ip"]:
                discovered.append(device_info)

        return discovered

    def _discover_alternative(self):
        """
        Alternatywna metoda wykrywania urządzeń ONVIF bez użycia biblioteki.
        """
        discovered = []
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(5)

            msg = """<?xml version="1.0" encoding="utf-8"?>
            <Envelope xmlns:dn="http://www.onvif.org/ver10/network/wsdl">
                <Header>
                    <MessageID>uuid:84ede3de-7dec-11d0-c360-F01234567890</MessageID>
                    <To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</To>
                    <Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</Action>
                </Header>
                <Body>
                    <Probe xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                        <Types>dn:NetworkVideoTransmitter</Types>
                    </Probe>
                </Body>
            </Envelope>"""

            sock.sendto(msg.encode(), ("239.255.255.250", 3702))

            while True:
                try:
                    data, addr = sock.recvfrom(65535)
                    device_info = {
                        "name": "ONVIF Camera",
                        "ip": addr[0],
                        "port": 80,
                        "type": DeviceType.IP_CAMERA.name,
                        "protocol": ProtocolType.RTSP.value,
                        "paths": ["/onvif-media/media.amp"],
                    }
                    discovered.append(device_info)
                except socket.timeout:
                    break

        except Exception as e:
            logger.error(f"Błąd podczas alternatywnego wykrywania ONVIF: {e}")

        return discovered

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
        try:
            # Próba użycia biblioteki
            try:
                return self._discover_with_library()
            except ImportError:
                logger.warning(
                    "Biblioteka UPnP nie jest dostępna. Używam alternatywnej metody."
                )
                return self._discover_alternative()
        except Exception as e:
            logger.error(f"Błąd podczas wykrywania urządzeń UPnP: {e}")
            return []

    def _discover_with_library(self):
        """
        Wykrywa urządzenia UPnP używając biblioteki upnpclient.
        """
        import upnpclient

        devices = []
        upnp_devices = upnpclient.discover(timeout=5)

        for upnp_device in upnp_devices:
            try:
                # Sprawdź, czy to urządzenie audio/wideo
                is_av_device = False
                device_type = upnp_device.device_type.lower()

                if "camera" in device_type or "video" in device_type:
                    device_type = DeviceType.IP_CAMERA.name
                    is_av_device = True
                elif "audio" in device_type or "sound" in device_type:
                    device_type = DeviceType.USB_MICROPHONE.name
                    is_av_device = True

                if not is_av_device:
                    continue

                # Ekstrakcja informacji o urządzeniu
                name = upnp_device.friendly_name
                url_parts = urlparse(upnp_device.location)
                ip = url_parts.hostname
                port = url_parts.port or 80

                # Dodanie urządzenia do listy
                devices.append(
                    {
                        "name": name,
                        "ip": ip,
                        "port": port,
                        "type": device_type,
                        "protocol": ProtocolType.HTTP.value,
                    }
                )

            except Exception as e:
                logger.warning(f"Błąd podczas przetwarzania urządzenia UPnP: {e}")

        return devices

    def _discover_alternative(self):
        """
        Alternatywna metoda wykrywania urządzeń UPnP bez użycia biblioteki.
        """
        devices = []
        try:
            msg = """M-SEARCH * HTTP/1.1
Host: 239.255.255.250:1900
Man: "ssdp:discover"
ST: ssdp:all
MX: 5
"""
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(5)
            sock.sendto(msg.encode(), ("239.255.255.250", 1900))

            while True:
                try:
                    data, addr = sock.recvfrom(10240)
                    response = data.decode("utf-8")

                    location_match = re.search(
                        r"LOCATION: (.*)", response, re.IGNORECASE
                    )
                    if location_match:
                        location = location_match.group(1).strip()
                        url_parts = urlparse(location)
                        ip = url_parts.hostname
                        port = url_parts.port or 80

                        device_type = DeviceType.IP_CAMERA.name
                        if "audio" in response.lower() or "sound" in response.lower():
                            device_type = DeviceType.USB_MICROPHONE.name

                        devices.append(
                            {
                                "name": f"UPnP Device ({ip})",
                                "ip": ip,
                                "port": port,
                                "type": device_type,
                                "protocol": "http",
                            }
                        )
                except socket.timeout:
                    break

        except Exception as e:
            logger.warning(f"Błąd podczas alternatywnego wykrywania UPnP: {e}")

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
        try:
            # Próba użycia biblioteki
            try:
                return self._discover_with_library()
            except ImportError:
                logger.warning(
                    "Biblioteka mDNS nie jest dostępna. Używam alternatywnej metody."
                )
                return self._discover_alternative()
        except Exception as e:
            logger.error(f"Błąd podczas wykrywania urządzeń mDNS: {e}")
            return []

    def _discover_with_library(self):
        """
        Wykrywa urządzenia mDNS używając biblioteki zeroconf.
        """
        from zeroconf import ServiceBrowser, Zeroconf

        class MDNSListener:
            def __init__(self):
                self.found_devices = []

            def add_service(self, zc, type, name):
                info = zc.get_service_info(type, name)
                if not info or not info.addresses:
                    return

                ip = socket.inet_ntoa(info.addresses[0])
                port = info.port
                device_name = name.split(".")[0]

                device_type = DeviceType.IP_CAMERA.name
                if "camera" in type.lower() or "video" in type.lower():
                    device_type = DeviceType.IP_CAMERA.name
                elif "audio" in type.lower() or "sound" in type.lower():
                    device_type = DeviceType.USB_MICROPHONE.name

                protocol = "http"
                if "rtsp" in type.lower():
                    protocol = "rtsp"
                elif "rtmp" in type.lower():
                    protocol = "rtmp"

                self.found_devices.append(
                    {
                        "name": device_name,
                        "ip": ip,
                        "port": port,
                        "type": device_type,
                        "protocol": protocol,
                    }
                )

            def remove_service(self, zc, type, name):
                pass

            def update_service(self, zc, type, name):
                pass

        zeroconf = Zeroconf()
        listener = MDNSListener()

        service_types = [
            "_rtsp._tcp.local.",
            "_http._tcp.local.",
            "_vzocam._tcp.local.",
            "_axis-video._tcp.local.",
            "_daap._tcp.local.",
            "_airplay._tcp.local.",
        ]

        browsers = []
        for service_type in service_types:
            browsers.append(ServiceBrowser(zeroconf, service_type, listener))

        time.sleep(5)
        devices = listener.found_devices
        zeroconf.close()

        return devices

    def _discover_alternative(self):
        """
        Alternatywna metoda wykrywania urządzeń mDNS bez użycia biblioteki.
        """
        devices = []
        try:
            multicast_group = "224.0.0.251"
            port = 5353

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)

            queries = [
                b"\x00\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x05_rtsp\x04_tcp\x05local\x00\x00\x0c\x00\x01",
                b"\x00\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x05_http\x04_tcp\x05local\x00\x00\x0c\x00\x01",
            ]

            for query in queries:
                try:
                    sock.sendto(query, (multicast_group, port))

                    while True:
                        try:
                            data, addr = sock.recvfrom(1024)
                            response = data.decode("utf-8", errors="ignore")
                            ip = addr[0]

                            devices.append(
                                {
                                    "name": f"mDNS Device ({ip})",
                                    "ip": ip,
                                    "port": port,
                                    "type": DeviceType.IP_CAMERA.name,
                                    "protocol": (
                                        "rtsp" if "_rtsp._tcp" in response else "http"
                                    ),
                                }
                            )
                        except socket.timeout:
                            break
                except Exception as e:
                    logger.warning(f"Błąd podczas alternatywnego wykrywania mDNS: {e}")

            sock.close()

        except Exception as e:
            logger.warning(f"Błąd podczas alternatywnego wykrywania mDNS: {e}")

        return devices

def discover_local_devices(device_type: Optional[str] = None) -> List[DeviceConfig]:
    """
    Discover local devices of the specified type.
    
    Args:
        device_type (str, optional): Type of device to discover. If None, discovers all types.
        
    Returns:
        List[DeviceConfig]: List of discovered devices.
    """
    logger.info(f"Discovering local devices of type: {device_type or 'all'}")
    
    devices = []
    scanner = get_platform_scanner()
    
    try:
        # Scan for video devices if no type specified or type is camera/video
        if not device_type or device_type.lower() in ["camera", "video", "all"]:
            video_devices = scanner.scan_video_devices()
            for device_id, device in video_devices.items():
                devices.append(DeviceConfig(
                    id=device_id,
                    name=device.name,
                    type=DeviceType.USB_CAMERA.name,
                    capabilities=device.capabilities,
                    status=device.status
                ))
        
        # Scan for audio devices if no type specified or type is microphone/audio
        if not device_type or device_type.lower() in ["microphone", "audio", "all"]:
            audio_devices = scanner.scan_audio_devices()
            for device_id, device in audio_devices.items():
                devices.append(DeviceConfig(
                    id=device_id,
                    name=device.name,
                    type=DeviceType.USB_MICROPHONE.name,
                    capabilities=device.capabilities,
                    status=device.status
                ))
                
    except Exception as e:
        logger.error(f"Error discovering local devices: {e}")
        
    return devices

def discover_network_devices(device_type: Optional[str] = None, timeout: int = 5) -> List[DeviceConfig]:
    """
    Discover network devices using various protocols.
    
    Args:
        device_type (str, optional): Type of device to discover. If None, discovers all types.
        timeout (int): Discovery timeout in seconds.
        
    Returns:
        List[DeviceConfig]: List of discovered devices.
    """
    logger.info(f"Discovering network devices of type: {device_type or 'all'}")
    
    devices = []
    discoverers = [
        ONVIFDiscovery(),
        UPnPDiscovery(),
        MDNSDiscovery()
    ]
    
    for discoverer in discoverers:
        try:
            discovered = discoverer.discover()
            for device_info in discovered:
                # Skip if device type doesn't match requested type
                if device_type and device_info["type"].lower() != device_type.lower():
                    continue
                    
                # Convert to DeviceConfig
                device = DeviceConfig(
                    id=f"{device_info['protocol']}_{device_info['ip']}_{device_info['port']}",
                    name=device_info["name"],
                    type=device_info["type"],
                    network_info={
                        "ip": device_info["ip"],
                        "port": device_info["port"],
                        "protocol": device_info["protocol"]
                    },
                    capabilities={},
                    status={"online": True}
                )
                devices.append(device)
                
        except Exception as e:
            logger.error(f"Error in {discoverer.__class__.__name__}: {e}")
            
    return devices
