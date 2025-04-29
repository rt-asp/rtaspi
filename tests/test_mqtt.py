"""Tests for MQTT integration."""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
import paho.mqtt.client as mqtt

from rtaspi.automation.mqtt import MQTTClient, MQTTTrigger, MQTTAction


@pytest.fixture
def mqtt_config():
    """Create test MQTT configuration."""
    return {
        "host": "localhost",
        "port": 1883,
        "username": "test_user",
        "password": "test_pass",
        "client_id": "test_client",
        "topic_prefix": "test",
        "qos": 1,
        "retain": True,
        "use_tls": True,
        "ca_certs": "/path/to/ca.crt",
        "certfile": "/path/to/client.crt",
        "keyfile": "/path/to/client.key",
    }


@pytest.fixture
def mock_paho():
    """Mock paho MQTT client."""
    with patch("rtaspi.automation.mqtt.mqtt") as mock_mqtt:
        # Mock client
        mock_client = Mock()
        mock_mqtt.Client.return_value = mock_client

        # Mock constants
        mock_mqtt.MQTT_ERR_SUCCESS = 0
        mock_mqtt.MQTT_ERR_NO_CONN = 1

        yield mock_mqtt


@pytest.fixture
def client(mqtt_config, mock_paho):
    """Create test MQTT client."""
    client = MQTTClient(mqtt_config)
    client.connect()
    yield client
    client.disconnect()


def test_client_init(mqtt_config, mock_paho):
    """Test client initialization."""
    client = MQTTClient(mqtt_config)

    # Check configuration
    assert client.host == mqtt_config["host"]
    assert client.port == mqtt_config["port"]
    assert client.username == mqtt_config["username"]
    assert client.password == mqtt_config["password"]
    assert client.client_id == mqtt_config["client_id"]
    assert client.topic_prefix == mqtt_config["topic_prefix"]
    assert client.qos == mqtt_config["qos"]
    assert client.retain == mqtt_config["retain"]

    # Check client setup
    mock_paho.Client.assert_called_once_with(client_id=mqtt_config["client_id"])
    mock_client = mock_paho.Client.return_value

    # Check callbacks
    assert mock_client.on_connect is not None
    assert mock_client.on_disconnect is not None
    assert mock_client.on_message is not None
    assert mock_client.on_publish is not None

    # Check authentication
    mock_client.username_pw_set.assert_called_once_with(
        mqtt_config["username"], mqtt_config["password"]
    )

    # Check TLS
    mock_client.tls_set.assert_called_once_with(
        ca_certs=mqtt_config["ca_certs"],
        certfile=mqtt_config["certfile"],
        keyfile=mqtt_config["keyfile"],
    )


def test_client_connect(client, mock_paho):
    """Test client connection."""
    mock_client = mock_paho.Client.return_value

    # Check connection
    mock_client.connect.assert_called_once_with(client.host, client.port)
    mock_client.loop_start.assert_called_once()

    # Check reconnect thread
    assert client._reconnect_thread is not None
    assert client._reconnect_thread.daemon
    assert not client._stop_reconnect.is_set()


def test_client_disconnect(client, mock_paho):
    """Test client disconnection."""
    mock_client = mock_paho.Client.return_value

    # Disconnect
    client.disconnect()

    # Check cleanup
    assert client._stop_reconnect.is_set()
    assert client._reconnect_thread is None
    mock_client.disconnect.assert_called_once()
    mock_client.loop_stop.assert_called_once()
    assert not client._connected


def test_client_publish(client, mock_paho):
    """Test message publishing."""
    mock_client = mock_paho.Client.return_value
    mock_result = Mock()
    mock_result.rc = mqtt.MQTT_ERR_SUCCESS
    mock_client.publish.return_value = mock_result

    # Test string payload
    assert client.publish("test/topic", "test message")
    mock_client.publish.assert_called_with(
        "test/test/topic", "test message", qos=client.qos, retain=client.retain
    )

    # Test dict payload
    data = {"key": "value"}
    assert client.publish("test/topic", data)
    mock_client.publish.assert_called_with(
        "test/test/topic", json.dumps(data), qos=client.qos, retain=client.retain
    )

    # Test publish failure
    mock_result.rc = mqtt.MQTT_ERR_NO_CONN
    assert not client.publish("test/topic", "test message")


def test_client_subscribe(client, mock_paho):
    """Test topic subscription."""
    mock_client = mock_paho.Client.return_value
    mock_client.subscribe.return_value = (mqtt.MQTT_ERR_SUCCESS, None)

    # Subscribe to topic
    callback = Mock()
    assert client.subscribe("test/topic", callback)
    mock_client.subscribe.assert_called_with("test/test/topic", qos=client.qos)
    assert "test/test/topic" in client._subscriptions
    assert client._subscriptions["test/test/topic"] == callback

    # Test subscribe failure
    mock_client.subscribe.return_value = (mqtt.MQTT_ERR_NO_CONN, None)
    assert not client.subscribe("test/topic", callback)


def test_client_unsubscribe(client, mock_paho):
    """Test topic unsubscription."""
    mock_client = mock_paho.Client.return_value
    mock_client.unsubscribe.return_value = (mqtt.MQTT_ERR_SUCCESS, None)

    # Subscribe and unsubscribe
    callback = Mock()
    client.subscribe("test/topic", callback)
    assert client.unsubscribe("test/topic")
    mock_client.unsubscribe.assert_called_with("test/test/topic")
    assert "test/test/topic" not in client._subscriptions

    # Test unsubscribe failure
    mock_client.unsubscribe.return_value = (mqtt.MQTT_ERR_NO_CONN, None)
    assert not client.unsubscribe("test/topic")


def test_client_callbacks(client, mock_paho):
    """Test client callbacks."""
    mock_client = mock_paho.Client.return_value

    # Test connection callback
    client._on_connect(mock_client, None, None, mqtt.MQTT_ERR_SUCCESS)
    assert client._connected

    client._on_connect(mock_client, None, None, mqtt.MQTT_ERR_NO_CONN)
    assert not client._connected

    # Test disconnection callback
    client._connected = True
    client._on_disconnect(mock_client, None, 0)
    assert not client._connected

    # Test message callback
    callback = Mock()
    client.subscribe("test/topic", callback)

    message = Mock()
    message.topic = "test/test/topic"
    message.payload = b"test message"
    client._on_message(mock_client, None, message)
    callback.assert_called_with("test/test/topic", "test message")

    # Test JSON message
    message.payload = b'{"key": "value"}'
    client._on_message(mock_client, None, message)
    callback.assert_called_with("test/test/topic", {"key": "value"})


def test_mqtt_trigger(client):
    """Test MQTT trigger."""
    # Create trigger
    trigger = MQTTTrigger(client, "test/trigger")

    # Add callback
    callback = Mock()
    trigger.add_callback(callback)

    # Initialize trigger
    assert trigger.initialize()
    assert "test/test/trigger" in client._subscriptions

    # Test message handling
    client._subscriptions["test/test/trigger"]("test/test/trigger", "test message")
    callback.assert_called_once()
    data = callback.call_args[0][0]
    assert data["type"] == "mqtt_message"
    assert data["topic"] == "test/test/trigger"
    assert data["payload"] == "test message"
    assert "timestamp" in data

    # Remove callback
    trigger.remove_callback(callback)
    client._subscriptions["test/test/trigger"]("test/test/trigger", "test message")
    assert callback.call_count == 1  # Not called again

    # Cleanup trigger
    trigger.cleanup()
    assert "test/test/trigger" not in client._subscriptions


def test_mqtt_action(client):
    """Test MQTT action."""
    # Create action
    action = MQTTAction(
        client, "test/action", "Value: {data.value}, Time: {data.timestamp}"
    )

    # Initialize action
    assert action.initialize()

    # Execute action
    data = {"value": 42, "timestamp": "2025-04-29T12:00:00Z"}
    assert action.execute(data)

    # Check published message
    mock_client = client._client
    mock_client.publish.assert_called_with(
        "test/test/action",
        "Value: 42, Time: 2025-04-29T12:00:00Z",
        qos=client.qos,
        retain=client.retain,
    )


def test_reconnection(client, mock_paho):
    """Test reconnection behavior."""
    mock_client = mock_paho.Client.return_value

    # Simulate disconnection
    client._connected = False
    time.sleep(0.1)  # Let reconnect thread run

    # Check reconnection attempt
    mock_client.reconnect.assert_called()

    # Stop reconnection
    client.disconnect()
    assert client._stop_reconnect.is_set()
    assert client._reconnect_thread is None


def test_error_handling(client, mock_paho):
    """Test error handling."""
    mock_client = mock_paho.Client.return_value

    # Test connection error
    mock_client.connect.side_effect = Exception("Connection failed")
    assert not client.connect()

    # Test publish error
    mock_client.publish.side_effect = Exception("Publish failed")
    assert not client.publish("test/topic", "test message")

    # Test subscribe error
    mock_client.subscribe.side_effect = Exception("Subscribe failed")
    assert not client.subscribe("test/topic", Mock())

    # Test unsubscribe error
    mock_client.unsubscribe.side_effect = Exception("Unsubscribe failed")
    assert not client.unsubscribe("test/topic")

    # Test message handling error
    callback = Mock(side_effect=Exception("Callback failed"))
    client._subscriptions["test/topic"] = callback
    message = Mock()
    message.topic = "test/topic"
    message.payload = b"test message"
    client._on_message(mock_client, None, message)  # Should not raise
