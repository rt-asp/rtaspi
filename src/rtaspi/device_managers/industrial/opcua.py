"""OPC UA protocol support."""

import logging
import time
from typing import Dict, Any, Optional, List, Union, Tuple
from asyncua import Client, Node, ua
from asyncua.common.node import Node as NodeType
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ...core.logging import get_logger
from ..base import DeviceManager

logger = get_logger(__name__)


class OPCUADevice:
    """OPC UA device implementation."""

    def __init__(self, device_id: str, config: Dict[str, Any]):
        """Initialize OPC UA device.

        Args:
            device_id: Device identifier
            config: Device configuration
        """
        self.device_id = device_id
        self.config = config

        # Connection settings
        self.url = config.get("url", "opc.tcp://localhost:4840")
        self.username = config.get("username")
        self.password = config.get("password")
        self.security_policy = config.get("security_policy", "Basic256Sha256")
        self.security_mode = config.get("security_mode", "SignAndEncrypt")
        self.certificate = config.get("certificate")
        self.private_key = config.get("private_key")

        # Node mapping
        self.nodes = config.get("nodes", {})

        # Client
        self._client: Optional[Client] = None
        self._connected = False
        self._loop = asyncio.new_event_loop()
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._subscriptions: Dict[str, Any] = {}

    def connect(self) -> bool:
        """Connect to OPC UA server.

        Returns:
            bool: True if connection successful
        """
        try:
            # Run connection in event loop
            return self._loop.run_until_complete(self._connect())

        except Exception as e:
            logger.error(f"Error connecting to OPC UA server: {e}")
            return False

    async def _connect(self) -> bool:
        """Async connect implementation."""
        try:
            # Create client
            self._client = Client(url=self.url)

            # Set security
            if self.security_policy != "None":
                if self.certificate and self.private_key:
                    await self._client.set_security(
                        certificate=self.certificate,
                        private_key=self.private_key,
                        policy=getattr(ua.SecurityPolicyType, self.security_policy),
                        mode=getattr(ua.MessageSecurityMode, self.security_mode),
                    )

            # Set authentication
            if self.username and self.password:
                await self._client.set_user(self.username)
                await self._client.set_password(self.password)

            # Connect
            await self._client.connect()
            self._connected = True
            logger.info(f"Connected to OPC UA server {self.device_id}")

            # Create subscriptions
            for node_id, node_config in self.nodes.items():
                if node_config.get("subscribe", False):
                    await self._create_subscription(node_id, node_config)

            return True

        except Exception as e:
            logger.error(f"Error connecting to OPC UA server: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from OPC UA server."""
        try:
            # Run disconnection in event loop
            self._loop.run_until_complete(self._disconnect())

        except Exception as e:
            logger.error(f"Error disconnecting from OPC UA server: {e}")

    async def _disconnect(self) -> None:
        """Async disconnect implementation."""
        try:
            if self._client:
                await self._client.disconnect()
                self._client = None
            self._connected = False
            logger.info(f"Disconnected from OPC UA server {self.device_id}")

        except Exception as e:
            logger.error(f"Error disconnecting from OPC UA server: {e}")

    def read_node(self, name: str) -> Optional[Any]:
        """Read node by name.

        Args:
            name: Node name from configuration

        Returns:
            Optional[Any]: Node value if successful
        """
        try:
            # Run read in event loop
            return self._loop.run_until_complete(self._read_node(name))

        except Exception as e:
            logger.error(f"Error reading node {name}: {e}")
            return None

    async def _read_node(self, name: str) -> Optional[Any]:
        """Async read implementation."""
        if not self._connected:
            logger.error("Device not connected")
            return None

        try:
            # Get node configuration
            node_config = self.nodes.get(name)
            if not node_config:
                logger.error(f"Node {name} not found in configuration")
                return None

            # Get node
            node_id = node_config.get("id")
            if not node_id:
                logger.error(f"Node {name} has no ID configured")
                return None

            # Read value
            node = self._client.get_node(node_id)
            value = await node.read_value()

            # Apply scaling and offset
            scale = node_config.get("scale", 1)
            offset = node_config.get("offset", 0)
            if isinstance(value, (int, float)):
                value = value * scale + offset

            return value

        except Exception as e:
            logger.error(f"Error reading node {name}: {e}")
            return None

    def write_node(self, name: str, value: Any) -> bool:
        """Write node by name.

        Args:
            name: Node name from configuration
            value: Value to write

        Returns:
            bool: True if write successful
        """
        try:
            # Run write in event loop
            return self._loop.run_until_complete(self._write_node(name, value))

        except Exception as e:
            logger.error(f"Error writing node {name}: {e}")
            return False

    async def _write_node(self, name: str, value: Any) -> bool:
        """Async write implementation."""
        if not self._connected:
            logger.error("Device not connected")
            return False

        try:
            # Get node configuration
            node_config = self.nodes.get(name)
            if not node_config:
                logger.error(f"Node {name} not found in configuration")
                return False

            # Get node
            node_id = node_config.get("id")
            if not node_id:
                logger.error(f"Node {name} has no ID configured")
                return False

            # Apply reverse scaling and offset
            scale = node_config.get("scale", 1)
            offset = node_config.get("offset", 0)
            if isinstance(value, (int, float)):
                value = (value - offset) / scale

            # Write value
            node = self._client.get_node(node_id)
            await node.write_value(value)
            return True

        except Exception as e:
            logger.error(f"Error writing node {name}: {e}")
            return False

    async def _create_subscription(
        self, node_id: str, node_config: Dict[str, Any]
    ) -> None:
        """Create subscription for node.

        Args:
            node_id: Node identifier
            node_config: Node configuration
        """
        try:
            # Get subscription parameters
            interval = node_config.get("interval", 1000)
            handler = node_config.get("handler")
            if not handler:
                return

            # Create subscription
            subscription = await self._client.create_subscription(interval, handler)
            node = self._client.get_node(node_config["id"])
            await subscription.subscribe_data_change(node)
            self._subscriptions[node_id] = subscription

        except Exception as e:
            logger.error(f"Error creating subscription for node {node_id}: {e}")

    def read_all_nodes(self) -> Dict[str, Any]:
        """Read all configured nodes.

        Returns:
            Dict[str, Any]: Node values by name
        """
        values = {}
        for name in self.nodes:
            value = self.read_node(name)
            if value is not None:
                values[name] = value
        return values

    def get_status(self) -> Dict[str, Any]:
        """Get device status.

        Returns:
            Dict[str, Any]: Status information
        """
        return {
            "id": self.device_id,
            "connected": self._connected,
            "url": self.url,
            "security_policy": self.security_policy,
            "security_mode": self.security_mode,
            "nodes": list(self.nodes.keys()),
        }


class OPCUAManager(DeviceManager):
    """Manager for OPC UA devices."""

    def __init__(self):
        """Initialize OPC UA manager."""
        super().__init__()
        self._devices: Dict[str, OPCUADevice] = {}

    def add_device(self, device_id: str, config: Dict[str, Any]) -> bool:
        """Add OPC UA device.

        Args:
            device_id: Device identifier
            config: Device configuration

        Returns:
            bool: True if device added successfully
        """
        try:
            # Create device
            device = OPCUADevice(device_id, config)
            if device.connect():
                self._devices[device_id] = device
                return True
            return False

        except Exception as e:
            logger.error(f"Error adding OPC UA device: {e}")
            return False

    def remove_device(self, device_id: str) -> bool:
        """Remove OPC UA device.

        Args:
            device_id: Device identifier

        Returns:
            bool: True if device removed
        """
        try:
            device = self._devices.get(device_id)
            if device:
                device.disconnect()
                del self._devices[device_id]
                return True
            return False

        except Exception as e:
            logger.error(f"Error removing OPC UA device: {e}")
            return False

    def get_device(self, device_id: str) -> Optional[OPCUADevice]:
        """Get OPC UA device by ID.

        Args:
            device_id: Device identifier

        Returns:
            Optional[OPCUADevice]: Device if found
        """
        return self._devices.get(device_id)

    def get_devices(self) -> List[OPCUADevice]:
        """Get all OPC UA devices.

        Returns:
            List[OPCUADevice]: List of devices
        """
        return list(self._devices.values())

    def cleanup(self) -> None:
        """Clean up manager resources."""
        for device in self._devices.values():
            device.disconnect()
        self._devices.clear()
