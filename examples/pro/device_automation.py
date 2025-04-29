#!/usr/bin/env python3
"""
Advanced device automation example showing integration between multiple
device types with complex automation rules and MQTT/Home Assistant integration.
"""

from rtaspi.device_managers.base import DeviceManager
from rtaspi.automation.rules import RuleEngine
from rtaspi.automation.mqtt import MQTTClient
from rtaspi.automation.hass import HomeAssistant
from rtaspi.device_managers.intercom.device import IntercomDevice
from rtaspi.security.alarms.dsc import DSCAlarmPanel
from rtaspi.device_managers.voip.sip import SIPPhone
from rtaspi.automation.triggers.device import DeviceTrigger
from rtaspi.automation.actions.device import DeviceAction
from rtaspi.device_managers.industrial.modbus import ModbusDevice

class AutomationSystem:
    def __init__(self):
        # Initialize device manager
        self.device_manager = DeviceManager()
        
        # Initialize automation components
        self.rule_engine = RuleEngine()
        self.mqtt = MQTTClient(
            broker="mqtt.example.com",
            port=1883,
            username="admin",
            password="secure123"
        )
        
        self.hass = HomeAssistant(
            url="http://homeassistant.local:8123",
            token="your_long_lived_access_token"
        )
        
        # Initialize various devices
        self.intercom = IntercomDevice(
            address="192.168.1.100",
            username="admin",
            password="intercom123"
        )
        
        self.alarm = DSCAlarmPanel(
            port="/dev/ttyUSB0",
            code="1234"
        )
        
        self.phone = SIPPhone(
            server="sip.example.com",
            username="office",
            password="sip123"
        )
        
        self.gate_control = ModbusDevice(
            host="192.168.1.200",
            port=502,
            unit=1
        )
        
    def setup_automation_rules(self):
        # Rule 1: When intercom button is pressed during business hours,
        # call office phone and open gate if call is answered
        self.rule_engine.add_rule(
            trigger=DeviceTrigger(
                device=self.intercom,
                event="button_press",
                conditions=[
                    lambda: self.is_business_hours(),
                    lambda: not self.alarm.is_armed()
                ]
            ),
            actions=[
                DeviceAction(
                    device=self.phone,
                    action="dial",
                    params={"number": "101"}  # Office extension
                ),
                DeviceAction(
                    device=self.gate_control,
                    action="write_coil",
                    params={"address": 0, "value": True}
                )
            ]
        )
        
        # Rule 2: When alarm is triggered, start recording on all cameras
        # and send notifications
        self.rule_engine.add_rule(
            trigger=DeviceTrigger(
                device=self.alarm,
                event="alarm_triggered"
            ),
            actions=[
                lambda: self.device_manager.start_recording_all(),
                lambda: self.send_notifications("Alarm triggered!")
            ]
        )
        
        # Rule 3: Sync device states with Home Assistant
        for device in self.device_manager.get_all_devices():
            self.hass.register_device(device)
            self.mqtt.subscribe(f"home/devices/{device.id}/command")
    
    def is_business_hours(self):
        """Check if current time is within business hours."""
        from datetime import datetime, time
        now = datetime.now().time()
        return time(9, 0) <= now <= time(17, 0)
    
    def send_notifications(self, message):
        """Send notifications through multiple channels."""
        self.mqtt.publish("home/notifications", message)
        self.hass.notify("security_group", message)
        self.phone.send_sms("1234567890", message)
    
    def run(self):
        """Start the automation system."""
        self.setup_automation_rules()
        self.rule_engine.start()
        self.mqtt.connect()
        print("Automation system running...")

if __name__ == "__main__":
    system = AutomationSystem()
    system.run()
