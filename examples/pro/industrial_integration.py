#!/usr/bin/env python3
"""
Advanced industrial integration example demonstrating OPC UA and Modbus
communication with industrial equipment, data logging, and visualization.
"""

from rtaspi.device_managers.industrial.opcua import OPCUADevice
from rtaspi.device_managers.industrial.modbus import ModbusDevice
from rtaspi.processing.pipeline_executor import PipelineExecutor
from rtaspi.streaming.output import DataOutput
from rtaspi.automation.mqtt import MQTTClient
import json
import time
from datetime import datetime

class IndustrialMonitor:
    def __init__(self):
        # Initialize OPC UA connection to PLC
        self.plc = OPCUADevice(
            url="opc.tcp://plc.factory.local:4840",
            username="operator",
            password="plc123",
            security_mode="SignAndEncrypt"
        )
        
        # Initialize Modbus connection to sensors
        self.temp_sensor = ModbusDevice(
            host="192.168.1.10",
            port=502,
            unit=1,
            timeout=1.0
        )
        
        self.pressure_sensor = ModbusDevice(
            host="192.168.1.11",
            port=502,
            unit=2,
            timeout=1.0
        )
        
        # Setup data pipeline
        self.pipeline = PipelineExecutor()
        
        # Setup MQTT for data publishing
        self.mqtt = MQTTClient(
            broker="mqtt.factory.local",
            port=8883,
            username="monitor",
            password="mqtt123",
            use_ssl=True
        )
        
        # Initialize data output
        self.data_output = DataOutput(
            format="json",
            compression="gzip",
            retention_days=30
        )
    
    def setup_monitoring(self):
        # Define PLC tags to monitor
        plc_tags = [
            "Production.Line1.Speed",
            "Production.Line1.Temperature",
            "Tank1.Level",
            "Tank1.Pressure",
            "System.Status"
        ]
        
        # Subscribe to PLC tags
        for tag in plc_tags:
            self.plc.subscribe(
                tag,
                callback=self.handle_plc_data,
                sampling_interval=100
            )
        
        # Setup Modbus register monitoring
        self.pipeline.add_task(
            self.read_modbus_data,
            interval=1.0
        )
        
        # Setup data logging
        self.pipeline.add_task(
            self.log_data,
            interval=5.0
        )
    
    def handle_plc_data(self, tag, value, timestamp):
        """Handle data updates from PLC."""
        data = {
            "source": "plc",
            "tag": tag,
            "value": value,
            "timestamp": timestamp
        }
        
        # Publish to MQTT
        self.mqtt.publish(
            f"factory/plc/{tag}",
            json.dumps(data)
        )
        
        # Check for alerts
        self.check_alerts(tag, value)
    
    def read_modbus_data(self):
        """Read data from Modbus sensors."""
        try:
            # Read temperature (scaled value)
            temp = self.temp_sensor.read_holding_registers(
                address=0,
                count=2
            )
            temp_value = temp[0] + temp[1] / 10.0
            
            # Read pressure (raw value)
            pressure = self.pressure_sensor.read_holding_registers(
                address=0,
                count=1
            )[0]
            
            data = {
                "temperature": temp_value,
                "pressure": pressure,
                "timestamp": datetime.now().isoformat()
            }
            
            # Publish sensor data
            self.mqtt.publish(
                "factory/sensors",
                json.dumps(data)
            )
            
            return data
            
        except Exception as e:
            print(f"Error reading Modbus data: {e}")
            return None
    
    def check_alerts(self, tag, value):
        """Check for alert conditions."""
        alerts = {
            "Production.Line1.Temperature": (50, 80),  # (warning, critical)
            "Tank1.Pressure": (800, 1000)
        }
        
        if tag in alerts:
            warning, critical = alerts[tag]
            if value >= critical:
                self.send_alert("CRITICAL", f"{tag} at {value}")
            elif value >= warning:
                self.send_alert("WARNING", f"{tag} at {value}")
    
    def send_alert(self, level, message):
        """Send alert through multiple channels."""
        alert = {
            "level": level,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        self.mqtt.publish("factory/alerts", json.dumps(alert))
        print(f"ALERT [{level}]: {message}")
    
    def log_data(self):
        """Log collected data to storage."""
        data = {
            "plc_data": self.plc.get_all_values(),
            "sensor_data": self.read_modbus_data(),
            "timestamp": datetime.now().isoformat()
        }
        
        self.data_output.write(
            data,
            filename=f"factory_data_{datetime.now().strftime('%Y%m%d')}.json"
        )
    
    def run(self):
        """Start the industrial monitoring system."""
        print("Starting industrial monitoring...")
        self.setup_monitoring()
        self.mqtt.connect()
        self.pipeline.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            self.pipeline.stop()
            self.mqtt.disconnect()
            self.plc.disconnect()

if __name__ == "__main__":
    monitor = IndustrialMonitor()
    monitor.run()
