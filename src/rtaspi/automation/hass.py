"""Home Assistant integration."""

import logging
import json
import time
import re
import uuid
from typing import Dict, Any, Optional, List, Callable
import requests
import websocket
from threading import Thread, Event

from ..core.logging import get_logger

logger = get_logger(__name__)


class HomeAssistant:
    """Home Assistant integration."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize Home Assistant client.

        Args:
            config: Home Assistant configuration
        """
        self.config = config
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 8123)
        self.token = config.get("token")
        self.use_ssl = config.get("use_ssl", True)
        self.verify_ssl = config.get("verify_ssl", True)

        # API settings
        self.api_url = (
            f"{'https' if self.use_ssl else 'http'}://{self.host}:{self.port}/api"
        )
        self.ws_url = (
            f"{'wss' if self.use_ssl else 'ws'}://{self.host}:{self.port}/api/websocket"
        )
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        # WebSocket
        self._ws: Optional[websocket.WebSocketApp] = None
        self._ws_thread: Optional[Thread] = None
        self._ws_connected = False
        self._ws_authenticated = False
        self._ws_stop = Event()
        self._ws_message_id = 0
        self._ws_callbacks: Dict[int, Callable] = {}

        # State
        self._devices: Dict[str, Dict] = {}
        self._entities: Dict[str, Dict] = {}

    def connect(self) -> bool:
        """Connect to Home Assistant.

        Returns:
            bool: True if connection successful
        """
        try:
            # Test API connection
            response = requests.get(
                f"{self.api_url}/", headers=self.headers, verify=self.verify_ssl
            )
            response.raise_for_status()

            # Start WebSocket connection
            self._ws_stop.clear()
            self._ws = websocket.WebSocketApp(
                self.ws_url,
                on_open=self._on_ws_open,
                on_message=self._on_ws_message,
                on_error=self._on_ws_error,
                on_close=self._on_ws_close,
            )

            self._ws_thread = Thread(target=self._ws.run_forever)
            self._ws_thread.daemon = True
            self._ws_thread.start()

            # Wait for authentication
            timeout = time.time() + 10
            while not self._ws_authenticated and time.time() < timeout:
                time.sleep(0.1)

            return self._ws_authenticated

        except Exception as e:
            logger.error(f"Error connecting to Home Assistant: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from Home Assistant."""
        try:
            if self._ws:
                self._ws_stop.set()
                self._ws.close()
                self._ws = None

            if self._ws_thread:
                self._ws_thread.join()
                self._ws_thread = None

            self._ws_connected = False
            self._ws_authenticated = False

        except Exception as e:
            logger.error(f"Error disconnecting from Home Assistant: {e}")

    def register_device(self, device_info: Dict[str, Any]) -> Optional[str]:
        """Register device with Home Assistant.

        Args:
            device_info: Device information

        Returns:
            Optional[str]: Device ID if successful
        """
        try:
            # Generate device ID
            device_id = device_info.get("id", str(uuid.uuid4()))

            # Create device registry entry
            payload = {
                "type": "config/device_registry/create",
                "device_id": device_id,
                "name": device_info.get("name", device_id),
                "manufacturer": device_info.get("manufacturer", "rtaspi"),
                "model": device_info.get("model", ""),
                "sw_version": device_info.get("sw_version", ""),
                "identifiers": [device_id],
                "connections": device_info.get("connections", []),
            }

            response = self._send_ws_message(payload)
            if response and response.get("success"):
                self._devices[device_id] = device_info
                return device_id

            return None

        except Exception as e:
            logger.error(f"Error registering device: {e}")
            return None

    def register_entity(self, entity_info: Dict[str, Any]) -> Optional[str]:
        """Register entity with Home Assistant.

        Args:
            entity_info: Entity information

        Returns:
            Optional[str]: Entity ID if successful
        """
        try:
            # Generate entity ID
            domain = entity_info.get("domain", "sensor")
            name = entity_info.get("name", "").lower().replace(" ", "_")
            entity_id = entity_info.get("id", f"{domain}.rtaspi_{name}")

            # Create entity registry entry
            payload = {
                "type": "config/entity_registry/create",
                "entity_id": entity_id,
                "name": entity_info.get("name", entity_id),
                "device_id": entity_info.get("device_id"),
                "platform": "rtaspi",
                "unique_id": entity_info.get("unique_id", entity_id),
                "device_class": entity_info.get("device_class"),
                "unit_of_measurement": entity_info.get("unit"),
                "icon": entity_info.get("icon"),
            }

            response = self._send_ws_message(payload)
            if response and response.get("success"):
                self._entities[entity_id] = entity_info
                return entity_id

            return None

        except Exception as e:
            logger.error(f"Error registering entity: {e}")
            return None

    def update_state(
        self, entity_id: str, state: Any, attributes: Optional[Dict] = None
    ) -> bool:
        """Update entity state.

        Args:
            entity_id: Entity ID
            state: New state value
            attributes: State attributes

        Returns:
            bool: True if update successful
        """
        try:
            payload = {"type": "state/update", "entity_id": entity_id, "state": state}
            if attributes:
                payload["attributes"] = attributes

            response = self._send_ws_message(payload)
            return response and response.get("success", False)

        except Exception as e:
            logger.error(f"Error updating state: {e}")
            return False

    def subscribe_events(
        self, event_type: str, callback: Callable[[Dict], None]
    ) -> bool:
        """Subscribe to Home Assistant events.

        Args:
            event_type: Event type to subscribe to
            callback: Function to call with events

        Returns:
            bool: True if subscription successful
        """
        try:
            payload = {"type": "subscribe_events", "event_type": event_type}

            def handle_event(msg):
                if (
                    msg.get("type") == "event"
                    and msg.get("event", {}).get("event_type") == event_type
                ):
                    callback(msg["event"])

            response = self._send_ws_message(payload, handle_event)
            return response and response.get("success", False)

        except Exception as e:
            logger.error(f"Error subscribing to events: {e}")
            return False

    def call_service(
        self, domain: str, service: str, data: Optional[Dict] = None
    ) -> bool:
        """Call Home Assistant service.

        Args:
            domain: Service domain
            service: Service name
            data: Service data

        Returns:
            bool: True if service call successful
        """
        try:
            payload = {"type": "call_service", "domain": domain, "service": service}
            if data:
                payload["service_data"] = data

            response = self._send_ws_message(payload)
            return response and response.get("success", False)

        except Exception as e:
            logger.error(f"Error calling service: {e}")
            return False

    def _send_ws_message(
        self, message: Dict, callback: Optional[Callable] = None
    ) -> Optional[Dict]:
        """Send WebSocket message.

        Args:
            message: Message to send
            callback: Optional callback for response

        Returns:
            Optional[Dict]: Response message if no callback
        """
        if not self._ws_authenticated:
            logger.error("Not authenticated")
            return None

        try:
            # Add message ID
            self._ws_message_id += 1
            message["id"] = self._ws_message_id

            # Store callback
            if callback:
                self._ws_callbacks[message["id"]] = callback
            else:
                # Create response event
                response_event = Event()
                response: Dict[str, Any] = {}

                def handle_response(msg):
                    response.update(msg)
                    response_event.set()

                self._ws_callbacks[message["id"]] = handle_response

            # Send message
            self._ws.send(json.dumps(message))

            # Wait for response if no callback
            if not callback:
                if response_event.wait(timeout=10):
                    return response
                logger.error("Timeout waiting for response")
                return None

            return {"success": True}

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return None

    def _on_ws_open(self, ws: websocket.WebSocketApp) -> None:
        """Handle WebSocket connection opened.

        Args:
            ws: WebSocket instance
        """
        logger.info("Connected to Home Assistant WebSocket")
        self._ws_connected = True

        # Send auth message
        auth_message = {"type": "auth", "access_token": self.token}
        ws.send(json.dumps(auth_message))

    def _on_ws_message(self, ws: websocket.WebSocketApp, message: str) -> None:
        """Handle WebSocket message received.

        Args:
            ws: WebSocket instance
            message: Received message
        """
        try:
            msg = json.loads(message)
            msg_type = msg.get("type")

            if msg_type == "auth_required":
                pass  # Already handled in _on_ws_open

            elif msg_type == "auth_ok":
                logger.info("Authenticated with Home Assistant")
                self._ws_authenticated = True

            elif msg_type == "auth_invalid":
                logger.error("Authentication failed")
                self._ws_authenticated = False
                ws.close()

            else:
                # Handle message callback
                msg_id = msg.get("id")
                if msg_id in self._ws_callbacks:
                    callback = self._ws_callbacks[msg_id]
                    if not msg.get("success", True):
                        logger.error(
                            f"Error in message {msg_id}: {msg.get('error', {}).get('message')}"
                        )
                    callback(msg)
                    if msg.get("type") != "event":
                        del self._ws_callbacks[msg_id]

        except Exception as e:
            logger.error(f"Error handling message: {e}")

    def _on_ws_error(self, ws: websocket.WebSocketApp, error: Exception) -> None:
        """Handle WebSocket error.

        Args:
            ws: WebSocket instance
            error: Error that occurred
        """
        logger.error(f"WebSocket error: {error}")

    def _on_ws_close(self, ws: websocket.WebSocketApp) -> None:
        """Handle WebSocket connection closed.

        Args:
            ws: WebSocket instance
        """
        logger.info("Disconnected from Home Assistant WebSocket")
        self._ws_connected = False
        self._ws_authenticated = False

        # Attempt reconnection if not stopping
        if not self._ws_stop.is_set():

            def reconnect():
                time.sleep(5)
                if not self._ws_stop.is_set():
                    logger.info("Attempting to reconnect")
                    self.connect()

            Thread(target=reconnect).start()
