#!/usr/bin/env python3
"""
Example demonstrating RTASPI's Home Assistant integration capabilities.
Shows how to integrate devices with Home Assistant, handle state changes,
and respond to Home Assistant events.
"""

import argparse
import asyncio
import json
import signal
import sys
from rtaspi.automation.hass import HomeAssistantClient
from rtaspi.device_managers.base import DeviceManager
from rtaspi.device_managers.utils.discovery import DeviceDiscovery

class HomeAssistantExample:
    def __init__(self, host, token=None):
        self.host = host
        self.token = token
        self.device_manager = DeviceManager()
        self.discovery = DeviceDiscovery()
        self.hass_client = None
        self.running = False

    async def setup(self):
        """Set up Home Assistant client and device discovery."""
        print("Setting up Home Assistant integration...")
        
        # Initialize Home Assistant client
        self.hass_client = HomeAssistantClient(
            host=self.host,
            token=self.token,
            device_ready_callback=self.on_device_ready,
            state_changed_callback=self.on_state_changed,
            event_callback=self.on_event
        )

        # Discover local devices
        devices = await self.discovery.discover_devices()
        print(f"Discovered {len(devices)} local devices")

        # Register devices with Home Assistant
        for device in devices:
            await self.register_device(device)

    async def register_device(self, device):
        """Register a device with Home Assistant."""
        try:
            # Create device configuration
            device_config = {
                'name': device.name,
                'identifiers': [device.id],
                'manufacturer': device.manufacturer,
                'model': device.model,
                'sw_version': device.version
            }

            # Register device capabilities
            if hasattr(device, 'camera'):
                await self.register_camera(device, device_config)
            if hasattr(device, 'sensor'):
                await self.register_sensor(device, device_config)
            if hasattr(device, 'switch'):
                await self.register_switch(device, device_config)

            print(f"Registered device: {device.name}")

        except Exception as e:
            print(f"Error registering device {device.name}: {e}")

    async def register_camera(self, device, config):
        """Register camera capabilities with Home Assistant."""
        await self.hass_client.register_camera(
            unique_id=f"{device.id}_camera",
            name=f"{device.name} Camera",
            device_info=config,
            stream_source=device.camera.stream_url,
            still_image_url=device.camera.snapshot_url
        )

    async def register_sensor(self, device, config):
        """Register sensor capabilities with Home Assistant."""
        for sensor in device.sensor.get_sensors():
            await self.hass_client.register_sensor(
                unique_id=f"{device.id}_{sensor.type}",
                name=f"{device.name} {sensor.type.title()}",
                device_info=config,
                device_class=sensor.type,
                unit_of_measurement=sensor.unit,
                state_class="measurement"
            )

    async def register_switch(self, device, config):
        """Register switch capabilities with Home Assistant."""
        await self.hass_client.register_switch(
            unique_id=f"{device.id}_switch",
            name=f"{device.name} Switch",
            device_info=config,
            state_topic=f"home/switch/{device.id}/state",
            command_topic=f"home/switch/{device.id}/set",
            state_handler=lambda: self.get_switch_state(device),
            command_handler=lambda state: self.set_switch_state(device, state)
        )

    def get_switch_state(self, device):
        """Get current state of a switch device."""
        try:
            return device.switch.get_state()
        except Exception as e:
            print(f"Error getting switch state for {device.name}: {e}")
            return None

    def set_switch_state(self, device, state):
        """Set state of a switch device."""
        try:
            device.switch.set_state(state)
            # Update Home Assistant state
            asyncio.create_task(
                self.hass_client.update_entity_state(f"{device.id}_switch", state)
            )
        except Exception as e:
            print(f"Error setting switch state for {device.name}: {e}")

    async def on_device_ready(self, device_id):
        """Handle device ready events."""
        print(f"Device {device_id} is ready")
        device = self.device_manager.get_device(device_id)
        if device:
            # Initialize device state
            if hasattr(device, 'switch'):
                state = self.get_switch_state(device)
                await self.hass_client.update_entity_state(f"{device_id}_switch", state)

    async def on_state_changed(self, entity_id, new_state, old_state):
        """Handle state change events from Home Assistant."""
        print(f"State changed for {entity_id}: {old_state} -> {new_state}")
        
        # Extract device ID from entity ID
        device_id = entity_id.split('_')[0]
        device = self.device_manager.get_device(device_id)
        
        if device:
            if entity_id.endswith('_switch'):
                self.set_switch_state(device, new_state)
            # Handle other entity types as needed

    async def on_event(self, event_type, event_data):
        """Handle events from Home Assistant."""
        print(f"Received event: {event_type}")
        print(f"Event data: {json.dumps(event_data, indent=2)}")

        if event_type == 'call_service':
            await self.handle_service_call(event_data)

    async def handle_service_call(self, event_data):
        """Handle service calls from Home Assistant."""
        domain = event_data.get('domain')
        service = event_data.get('service')
        
        if domain == 'camera' and service == 'snapshot':
            await self.handle_camera_snapshot(event_data)
        elif domain == 'switch' and service in ['turn_on', 'turn_off']:
            await self.handle_switch_command(event_data)

    async def handle_camera_snapshot(self, event_data):
        """Handle camera snapshot requests."""
        entity_id = event_data.get('target', {}).get('entity_id')
        if entity_id:
            device_id = entity_id.split('_')[0]
            device = self.device_manager.get_device(device_id)
            if device and hasattr(device, 'camera'):
                try:
                    snapshot = await device.camera.take_snapshot()
                    await self.hass_client.update_camera_image(entity_id, snapshot)
                except Exception as e:
                    print(f"Error taking snapshot: {e}")

    async def handle_switch_command(self, event_data):
        """Handle switch commands."""
        entity_id = event_data.get('target', {}).get('entity_id')
        if entity_id:
            device_id = entity_id.split('_')[0]
            device = self.device_manager.get_device(device_id)
            if device and hasattr(device, 'switch'):
                state = event_data.get('service') == 'turn_on'
                self.set_switch_state(device, state)

    async def start(self):
        """Start the Home Assistant integration."""
        self.running = True
        print("Starting Home Assistant integration...")
        await self.setup()
        await self.hass_client.connect()

    async def stop(self):
        """Stop the Home Assistant integration."""
        self.running = False
        print("\nStopping Home Assistant integration...")
        if self.hass_client:
            await self.hass_client.disconnect()

async def main():
    parser = argparse.ArgumentParser(description='RTASPI Home Assistant Integration Example')
    parser.add_argument('--host', required=True, help='Home Assistant host URL')
    parser.add_argument('--token', help='Long-lived access token')
    args = parser.parse_args()

    hass_example = HomeAssistantExample(args.host, args.token)

    # Handle graceful shutdown
    def signal_handler(signum, frame):
        print("\nSignal received, shutting down...")
        asyncio.create_task(hass_example.stop())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await hass_example.start()
        # Keep the main loop running
        while hass_example.running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await hass_example.stop()

if __name__ == '__main__':
    asyncio.run(main())
