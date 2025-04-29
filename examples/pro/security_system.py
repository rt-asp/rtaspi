#!/usr/bin/env python3
"""
Advanced security system integration example demonstrating multi-camera
surveillance, alarm system integration, and automated security responses.
"""

from rtaspi.quick.camera import Camera
from rtaspi.security.analysis.motion import MotionAnalyzer
from rtaspi.security.alarms.dsc import DSCAlarmPanel
from rtaspi.security.alarms.honeywell import HoneywellPanel
from rtaspi.device_managers.intercom.device import IntercomDevice
from rtaspi.processing.video.detection import MotionDetector
from rtaspi.streaming.webrtc import WebRTCServer
from rtaspi.automation.mqtt import MQTTClient
from rtaspi.processing.pipeline_executor import PipelineExecutor
import json
from datetime import datetime, time
import asyncio
import logging

class SecuritySystem:
    def __init__(self):
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("SecuritySystem")
        
        # Initialize cameras
        self.cameras = {
            "entrance": Camera.create(
                resolution=(1920, 1080),
                framerate=30,
                night_mode=True
            ),
            "parking": Camera.create(
                resolution=(1920, 1080),
                framerate=30,
                night_mode=True
            ),
            "warehouse": Camera.create(
                resolution=(2560, 1440),
                framerate=15,
                night_mode=True
            )
        }
        
        # Initialize alarm panels
        self.dsc_panel = DSCAlarmPanel(
            port="/dev/ttyUSB0",
            code="5678"
        )
        
        self.honeywell_panel = HoneywellPanel(
            address="192.168.1.100",
            username="admin",
            password="secure456"
        )
        
        # Initialize intercom
        self.intercom = IntercomDevice(
            address="192.168.1.101",
            username="admin",
            password="intercom789"
        )
        
        # Setup WebRTC streaming server
        self.webrtc = WebRTCServer(
            port=8443,
            ssl_cert="security.crt",
            ssl_key="security.key"
        )
        
        # Initialize MQTT client
        self.mqtt = MQTTClient(
            broker="mqtt.security.local",
            port=8883,
            username="security",
            password="mqtt789",
            use_ssl=True
        )
        
        # Setup pipeline executor
        self.pipeline = PipelineExecutor()
        
        # Initialize motion analyzers
        self.motion_analyzers = {}
        
    def setup_camera_monitoring(self):
        """Setup camera monitoring with motion detection."""
        for camera_id, camera in self.cameras.items():
            # Create motion detector
            detector = MotionDetector(
                sensitivity=0.7,
                min_area=1000,
                blur_size=5
            )
            
            # Create motion analyzer with zones
            analyzer = MotionAnalyzer(
                zones=self.get_zones_for_camera(camera_id),
                trigger_threshold=0.4
            )
            
            self.motion_analyzers[camera_id] = analyzer
            
            # Start camera stream with motion detection
            camera.start_streaming(
                motion_detector=detector,
                analyzer=analyzer,
                callback=lambda frame, motion: self.handle_camera_frame(
                    camera_id, frame, motion
                )
            )
            
            # Add stream to WebRTC server
            self.webrtc.add_stream(
                f"camera_{camera_id}",
                camera.get_stream()
            )
    
    def get_zones_for_camera(self, camera_id):
        """Define motion detection zones for each camera."""
        zones = {
            "entrance": [
                {
                    "name": "door",
                    "coords": [(800, 400), (1120, 400), (1120, 680), (800, 680)]
                },
                {
                    "name": "lobby",
                    "coords": [(400, 200), (1520, 200), (1520, 880), (400, 880)]
                }
            ],
            "parking": [
                {
                    "name": "gate",
                    "coords": [(960, 0), (1280, 0), (1280, 300), (960, 300)]
                },
                {
                    "name": "vehicles",
                    "coords": [(0, 300), (1920, 300), (1920, 1080), (0, 1080)]
                }
            ],
            "warehouse": [
                {
                    "name": "entrance",
                    "coords": [(1200, 600), (1360, 600), (1360, 840), (1200, 840)]
                },
                {
                    "name": "storage",
                    "coords": [(400, 200), (2160, 200), (2160, 1240), (400, 1240)]
                }
            ]
        }
        return zones.get(camera_id, [])
    
    def handle_camera_frame(self, camera_id, frame, motion_data):
        """Handle incoming camera frames with motion data."""
        if motion_data and motion_data.get("motion_detected"):
            # Get motion details
            zones = motion_data.get("active_zones", [])
            confidence = motion_data.get("confidence", 0)
            
            # Log motion event
            self.logger.info(
                f"Motion detected on {camera_id} - Zones: {zones}, "
                f"Confidence: {confidence:.2f}"
            )
            
            # Check if during non-business hours
            if not self.is_business_hours():
                self.handle_security_event(camera_id, zones, confidence)
    
    def handle_security_event(self, camera_id, zones, confidence):
        """Handle security events based on motion detection."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "camera": camera_id,
            "zones": zones,
            "confidence": confidence
        }
        
        # Publish event
        self.mqtt.publish(
            "security/events",
            json.dumps(event)
        )
        
        # Check alarm status
        if self.dsc_panel.is_armed() or self.honeywell_panel.is_armed():
            # Trigger alarm if confidence is high
            if confidence > 0.8:
                self.trigger_alarm(camera_id, event)
            
            # Start recording
            self.cameras[camera_id].start_recording(
                filename=f"security_{camera_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                duration=300  # 5 minutes
            )
    
    def trigger_alarm(self, camera_id, event):
        """Trigger alarm and notify security."""
        self.logger.warning(f"Triggering alarm for camera {camera_id}")
        
        # Trigger both alarm panels
        self.dsc_panel.trigger_alarm()
        self.honeywell_panel.trigger_alarm()
        
        # Send notifications
        self.mqtt.publish(
            "security/alerts",
            json.dumps({
                "level": "CRITICAL",
                "message": f"Security breach detected on {camera_id}",
                "event": event
            })
        )
        
        # Activate security measures
        self.intercom.play_warning_message()
        self.activate_security_lights()
    
    def is_business_hours(self):
        """Check if current time is within business hours."""
        now = datetime.now().time()
        return time(8, 0) <= now <= time(18, 0)
    
    def activate_security_lights(self):
        """Activate security lighting system."""
        self.mqtt.publish(
            "security/lights",
            json.dumps({"command": "activate_all"})
        )
    
    async def run(self):
        """Start the security system."""
        self.logger.info("Starting security system...")
        
        # Setup all components
        self.setup_camera_monitoring()
        await self.webrtc.start()
        self.mqtt.connect()
        
        # Start monitoring pipeline
        self.pipeline.start()
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Shutting down security system...")
            # Cleanup
            for camera in self.cameras.values():
                camera.stop_streaming()
            await self.webrtc.stop()
            self.mqtt.disconnect()
            self.pipeline.stop()

if __name__ == "__main__":
    security = SecuritySystem()
    asyncio.run(security.run())
