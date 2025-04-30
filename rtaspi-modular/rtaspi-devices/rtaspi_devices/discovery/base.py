"""
Base classes for device discovery functionality.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
import logging

logger = logging.getLogger(__name__)

class ProtocolHandler(ABC):
    """Base class for protocol-specific device discovery handlers."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize protocol handler.

        Args:
            config: Protocol-specific configuration.
        """
        self.config = config

    @abstractmethod
    async def discover(self, ip: str, port: int) -> Optional[Dict[str, Any]]:
        """
        Discover devices using this protocol.

        Args:
            ip: IP address to scan.
            port: Port to scan.

        Returns:
            Device information if found, None otherwise.
        """
        pass

class DiscoveryService:
    """Service for discovering network devices."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize discovery service.

        Args:
            config: Discovery configuration.
        """
        self.config = config
        self.protocol_handlers: Dict[str, ProtocolHandler] = {}
        self.filters: List[Callable] = []

    def register_protocol_handler(self, protocol: str, handler: ProtocolHandler) -> None:
        """
        Register a protocol handler.

        Args:
            protocol: Protocol name.
            handler: Protocol handler instance.
        """
        self.protocol_handlers[protocol] = handler
        logger.debug(f"Registered protocol handler for {protocol}")

    def add_filter(self, filter_func: Callable) -> None:
        """
        Add a device filter.

        Args:
            filter_func: Filter function that takes device info and returns bool.
        """
        self.filters.append(filter_func)

    async def scan(self) -> List[Dict[str, Any]]:
        """
        Scan for devices using registered protocol handlers.

        Returns:
            List of discovered devices.
        """
        discovered_devices = []

        # Get scan ranges from config
        scan_ranges = self.config.get("scan_ranges", [])
        protocols = self.config.get("protocols", [])
        ports = self.config.get("ports", {})

        # For each protocol and IP range
        for protocol in protocols:
            if protocol not in self.protocol_handlers:
                logger.warning(f"No handler registered for protocol {protocol}")
                continue

            handler = self.protocol_handlers[protocol]
            protocol_ports = ports.get(protocol, [])

            # Discover devices
            for ip_range in scan_ranges:
                # In a real implementation, we would iterate over the IP range
                # For now, just use a placeholder discovery
                device = await handler.discover("192.168.1.100", protocol_ports[0] if protocol_ports else 0)
                if device:
                    # Apply filters
                    if all(f(device) for f in self.filters):
                        discovered_devices.append(device)

        return discovered_devices
