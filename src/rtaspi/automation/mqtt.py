"""MQTT integration for automation."""

import logging
import json
import threading
import time
from typing import Dict, Any, Optional, Callable
import paho.mqtt.client as mqtt

from ..core.logging import get_logger

logger = get_logger(__name__)

class MQTTClient:
    """MQTT client for automation."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize MQTT client.
        
        Args:
            config: MQTT configuration
        """
        self.config = config
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 1883)
        self.username = config.get('username')
        self.password = config.get('password')
        self.client_id = config.get('client_id', 'rtaspi')
        self.topic_prefix = config.get('topic_prefix', 'rtaspi')
        self.qos = config.get('qos', 0)
        self.retain = config.get('retain', False)

        # MQTT client
        self._client = mqtt.Client(client_id=self.client_id)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message
        self._client.on_publish = self._on_publish

        # Authentication
        if self.username:
            self._client.username_pw_set(self.username, self.password)

        # TLS
        if config.get('use_tls'):
            self._client.tls_set(
                ca_certs=config.get('ca_certs'),
                certfile=config.get('certfile'),
                keyfile=config.get('keyfile')
            )

        # State
        self._connected = False
        self._subscriptions: Dict[str, Callable] = {}
        self._reconnect_thread: Optional[threading.Thread] = None
        self._stop_reconnect = threading.Event()

    def connect(self) -> bool:
        """Connect to MQTT broker.
        
        Returns:
            bool: True if connection successful
        """
        try:
            # Connect to broker
            self._client.connect(self.host, self.port)

            # Start network loop
            self._client.loop_start()

            # Start reconnect thread
            self._stop_reconnect.clear()
            self._reconnect_thread = threading.Thread(target=self._reconnect_loop)
            self._reconnect_thread.daemon = True
            self._reconnect_thread.start()

            return True

        except Exception as e:
            logger.error(f"Error connecting to MQTT broker: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from MQTT broker."""
        try:
            # Stop reconnect thread
            if self._reconnect_thread:
                self._stop_reconnect.set()
                self._reconnect_thread.join()
                self._reconnect_thread = None

            # Disconnect from broker
            self._client.disconnect()
            self._client.loop_stop()
            self._connected = False

        except Exception as e:
            logger.error(f"Error disconnecting from MQTT broker: {e}")

    def publish(self, topic: str, payload: Any) -> bool:
        """Publish message to topic.
        
        Args:
            topic: Topic to publish to
            payload: Message payload
            
        Returns:
            bool: True if publish successful
        """
        try:
            # Add topic prefix
            full_topic = f"{self.topic_prefix}/{topic}"

            # Convert payload to JSON
            if not isinstance(payload, str):
                payload = json.dumps(payload)

            # Publish message
            result = self._client.publish(
                full_topic,
                payload,
                qos=self.qos,
                retain=self.retain
            )

            return result.rc == mqtt.MQTT_ERR_SUCCESS

        except Exception as e:
            logger.error(f"Error publishing to MQTT topic: {e}")
            return False

    def subscribe(self, topic: str, callback: Callable[[str, Any], None]) -> bool:
        """Subscribe to topic.
        
        Args:
            topic: Topic to subscribe to
            callback: Function to call with received messages
            
        Returns:
            bool: True if subscription successful
        """
        try:
            # Add topic prefix
            full_topic = f"{self.topic_prefix}/{topic}"

            # Subscribe to topic
            result = self._client.subscribe(full_topic, qos=self.qos)
            if result[0] != mqtt.MQTT_ERR_SUCCESS:
                return False

            # Store callback
            self._subscriptions[full_topic] = callback
            return True

        except Exception as e:
            logger.error(f"Error subscribing to MQTT topic: {e}")
            return False

    def unsubscribe(self, topic: str) -> bool:
        """Unsubscribe from topic.
        
        Args:
            topic: Topic to unsubscribe from
            
        Returns:
            bool: True if unsubscribe successful
        """
        try:
            # Add topic prefix
            full_topic = f"{self.topic_prefix}/{topic}"

            # Unsubscribe from topic
            result = self._client.unsubscribe(full_topic)
            if result[0] != mqtt.MQTT_ERR_SUCCESS:
                return False

            # Remove callback
            if full_topic in self._subscriptions:
                del self._subscriptions[full_topic]

            return True

        except Exception as e:
            logger.error(f"Error unsubscribing from MQTT topic: {e}")
            return False

    def _on_connect(self, client: mqtt.Client, userdata: Any, flags: Dict, rc: int) -> None:
        """Handle connection established.
        
        Args:
            client: MQTT client instance
            userdata: User data
            flags: Connection flags
            rc: Result code
        """
        if rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info("Connected to MQTT broker")
            self._connected = True

            # Resubscribe to topics
            for topic in self._subscriptions:
                self._client.subscribe(topic, qos=self.qos)
        else:
            logger.error(f"Failed to connect to MQTT broker: {rc}")
            self._connected = False

    def _on_disconnect(self, client: mqtt.Client, userdata: Any, rc: int) -> None:
        """Handle connection lost.
        
        Args:
            client: MQTT client instance
            userdata: User data
            rc: Result code
        """
        logger.warning("Disconnected from MQTT broker")
        self._connected = False

    def _on_message(self, client: mqtt.Client, userdata: Any, message: mqtt.MQTTMessage) -> None:
        """Handle received message.
        
        Args:
            client: MQTT client instance
            userdata: User data
            message: Received message
        """
        try:
            # Get topic and payload
            topic = message.topic
            payload = message.payload.decode()

            # Parse JSON payload
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                pass  # Keep payload as string

            # Call topic callback
            if topic in self._subscriptions:
                self._subscriptions[topic](topic, payload)

        except Exception as e:
            logger.error(f"Error handling MQTT message: {e}")

    def _on_publish(self, client: mqtt.Client, userdata: Any, mid: int) -> None:
        """Handle message published.
        
        Args:
            client: MQTT client instance
            userdata: User data
            mid: Message ID
        """
        logger.debug(f"Published MQTT message: {mid}")

    def _reconnect_loop(self) -> None:
        """Reconnection loop."""
        while not self._stop_reconnect.is_set():
            try:
                if not self._connected:
                    logger.info("Attempting to reconnect to MQTT broker")
                    self._client.reconnect()
                time.sleep(5)
            except Exception as e:
                logger.error(f"Error in MQTT reconnect loop: {e}")
                time.sleep(30)  # Longer delay on error


class MQTTTrigger:
    """MQTT message trigger."""

    def __init__(self, mqtt_client: MQTTClient, topic: str):
        """Initialize MQTT trigger.
        
        Args:
            mqtt_client: MQTT client instance
            topic: Topic to subscribe to
        """
        self.mqtt_client = mqtt_client
        self.topic = topic
        self._callbacks: List[Callable[[Dict[str, Any]], None]] = []

    def initialize(self) -> bool:
        """Initialize trigger.
        
        Returns:
            bool: True if initialization successful
        """
        return self.mqtt_client.subscribe(self.topic, self._handle_message)

    def cleanup(self) -> None:
        """Clean up trigger resources."""
        self.mqtt_client.unsubscribe(self.topic)

    def add_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Add trigger callback.
        
        Args:
            callback: Function to call when trigger fires
        """
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Remove trigger callback.
        
        Args:
            callback: Callback to remove
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def _handle_message(self, topic: str, payload: Any) -> None:
        """Handle MQTT message.
        
        Args:
            topic: Message topic
            payload: Message payload
        """
        # Create event data
        data = {
            'type': 'mqtt_message',
            'topic': topic,
            'payload': payload,
            'timestamp': time.time()
        }

        # Call callbacks
        for callback in self._callbacks:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Error in MQTT trigger callback: {e}")


class MQTTAction:
    """MQTT message action."""

    def __init__(self, mqtt_client: MQTTClient, topic: str, payload_template: str):
        """Initialize MQTT action.
        
        Args:
            mqtt_client: MQTT client instance
            topic: Topic to publish to
            payload_template: Payload template
        """
        self.mqtt_client = mqtt_client
        self.topic = topic
        self.payload_template = payload_template

    def initialize(self) -> bool:
        """Initialize action.
        
        Returns:
            bool: True if initialization successful
        """
        return True

    def cleanup(self) -> None:
        """Clean up action resources."""
        pass

    def execute(self, data: Dict[str, Any]) -> bool:
        """Execute action.
        
        Args:
            data: Action input data
            
        Returns:
            bool: True if execution successful
        """
        try:
            # Process payload template
            payload = self.payload_template
            for match in re.finditer(r'\{data\.([^}]+)\}', payload):
                data_key = match.group(1)
                if data_key in data:
                    payload = payload.replace(match.group(0), str(data[data_key]))

            # Publish message
            return self.mqtt_client.publish(self.topic, payload)

        except Exception as e:
            logger.error(f"Error executing MQTT action: {e}")
            return False
