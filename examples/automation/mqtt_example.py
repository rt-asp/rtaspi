#!/usr/bin/env python3
"""
Example demonstrating RTASPI's MQTT integration capabilities.
Shows how to connect to an MQTT broker, subscribe to topics,
handle messages, and control devices.
"""

import argparse
import yaml
import os
import json
import signal
import sys
from rtaspi.automation.mqtt import MQTTClient
from rtaspi.device_managers.base import DeviceManager

class MQTTExample:
    def __init__(self, config_path):
        self.config = self._load_config(config_path)
        self.device_manager = DeviceManager()
        self.mqtt_client = None
        self.running = False

    def _load_config(self, config_path):
        """Load MQTT configuration from YAML file."""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
            # Handle environment variables in config
            if 'broker' in config:
                for key, value in config['broker'].items():
                    if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                        env_var = value[2:-1]
                        config['broker'][key] = os.environ.get(env_var)
            
            return config

    def setup_mqtt(self):
        """Set up MQTT client with configuration."""
        broker_config = self.config['broker']
        
        self.mqtt_client = MQTTClient(
            host=broker_config['host'],
            port=broker_config['port'],
            username=broker_config.get('username'),
            password=broker_config.get('password')
        )

        # Set up message handlers
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.on_disconnect = self.on_disconnect

        # Configure QoS and retain flag
        self.mqtt_client.default_qos = self.config.get('qos', 0)
        self.mqtt_client.default_retain = self.config.get('retain', False)

    def on_connect(self, client, userdata, flags, rc):
        """Handle connection to MQTT broker."""
        if rc == 0:
            print("Connected to MQTT broker")
            # Subscribe to configured topics
            for topic in self.config['topics']['subscribe']:
                print(f"Subscribing to {topic}")
                self.mqtt_client.subscribe(topic)
        else:
            print(f"Failed to connect to MQTT broker with code: {rc}")

    def on_message(self, client, userdata, message):
        """Handle incoming MQTT messages."""
        try:
            payload = json.loads(message.payload.decode())
            print(f"Received message on {message.topic}: {payload}")

            # Handle different message types
            if message.topic.startswith('home/sensors/'):
                self._handle_sensor_message(message.topic, payload)
            elif message.topic.startswith('home/cameras/'):
                self._handle_camera_message(message.topic, payload)
            elif message.topic.startswith('home/controls/'):
                self._handle_control_message(message.topic, payload)

        except json.JSONDecodeError:
            print(f"Failed to parse message payload: {message.payload}")
        except Exception as e:
            print(f"Error handling message: {e}")

    def _handle_sensor_message(self, topic, payload):
        """Handle sensor data messages."""
        sensor_id = topic.split('/')[-1]
        if 'value' in payload:
            print(f"Sensor {sensor_id} value: {payload['value']}")
            # Example: Publish status update
            self.publish_status(sensor_id, payload)

    def _handle_camera_message(self, topic, payload):
        """Handle camera-related messages."""
        camera_id = topic.split('/')[-1]
        if 'event' in payload:
            print(f"Camera {camera_id} event: {payload['event']}")
            # Example: Handle motion detection
            if payload['event'] == 'motion_detected':
                self.handle_motion_event(camera_id, payload)

    def _handle_control_message(self, topic, payload):
        """Handle device control messages."""
        device_id = topic.split('/')[-1]
        if 'command' in payload:
            print(f"Control command for {device_id}: {payload['command']}")
            # Example: Execute device command
            self.device_manager.execute_command(device_id, payload['command'])

    def publish_status(self, device_id, data):
        """Publish device status updates."""
        topic = f"home/status/{device_id}"
        self.mqtt_client.publish(topic, json.dumps(data))

    def handle_motion_event(self, camera_id, data):
        """Handle motion detection events."""
        # Example: Trigger recording and notification
        print(f"Motion detected on camera {camera_id}")
        self.publish_status(camera_id, {
            'event': 'motion_detected',
            'timestamp': data.get('timestamp'),
            'confidence': data.get('confidence', 1.0)
        })

    def on_disconnect(self, client, userdata, rc):
        """Handle disconnection from MQTT broker."""
        print("Disconnected from MQTT broker")
        if rc != 0:
            print(f"Unexpected disconnection. RC: {rc}")

    def start(self):
        """Start the MQTT client and message processing."""
        self.running = True
        print("Starting MQTT client...")
        self.mqtt_client.connect()
        self.mqtt_client.loop_start()

    def stop(self):
        """Stop the MQTT client and cleanup."""
        self.running = False
        print("\nStopping MQTT client...")
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()

def main():
    parser = argparse.ArgumentParser(description='RTASPI MQTT Integration Example')
    parser.add_argument('--config', required=True, help='Path to MQTT configuration YAML file')
    args = parser.parse_args()

    mqtt_example = MQTTExample(args.config)
    mqtt_example.setup_mqtt()

    # Handle graceful shutdown
    def signal_handler(signum, frame):
        print("\nSignal received, shutting down...")
        mqtt_example.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        mqtt_example.start()
        # Keep the main thread running
        while mqtt_example.running:
            signal.pause()
    except KeyboardInterrupt:
        mqtt_example.stop()

if __name__ == '__main__':
    main()
