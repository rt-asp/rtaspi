"""
Example of implementing a surveillance system with RTASPI
Demonstrates advantages over commercial solutions like Milestone XProtect
"""

from rtaspi.core import rtaspi
from rtaspi.device_managers.network_devices import NetworkDevicesManager
from rtaspi.processing.video.pipeline import VideoPipeline

def setup_surveillance_system():
    # Configuration with unlimited cameras (no per-camera licensing)
    config = {
        "system": {
            "storage_path": "/var/surveillance/recordings",
            "log_level": "INFO"
        },
        "recording": {
            "retention_days": 30,
            "motion_only": True
        }
    }

    # Initialize system
    app = rtaspi(config=config)
    network_manager = NetworkDevicesManager(app.config, app.mcp_broker)

    # Add cameras from different manufacturers (no vendor lock-in)
    cameras = [
        {"name": "Entrance", "ip": "192.168.1.100", "protocol": "rtsp", "username": "admin", "password": "pass"},
        {"name": "Parking", "ip": "192.168.1.101", "protocol": "rtsp", "username": "admin", "password": "pass"},
        {"name": "Office", "type": "usb", "device_path": "/dev/video0"}
    ]

    # Add all cameras to the system
    for camera in cameras:
        if camera.get("type") == "usb":
            app.add_local_device(camera["device_path"], camera["name"])
        else:
            network_manager.add_device(
                name=camera["name"],
                ip=camera["ip"],
                protocol=camera["protocol"],
                username=camera.get("username"),
                password=camera.get("password")
            )

    # Configure recording with motion detection for all cameras
    for device_id in app.get_all_devices():
        pipeline = VideoPipeline()
        
        # Add advanced video processing stages
        pipeline.add_stage("motion_detection", {
            "sensitivity": 0.7,
            "min_area": 500,
            "zones": [  # Define motion detection zones
                {"name": "entrance", "coordinates": [(0, 0), (300, 0), (300, 400), (0, 400)]},
                {"name": "restricted", "coordinates": [(500, 200), (800, 200), (800, 600), (500, 600)]}
            ]
        })
        
        # Add AI-powered object detection
        pipeline.add_stage("object_detection", {
            "model": "yolov5",
            "confidence_threshold": 0.6,
            "classes": ["person", "vehicle", "bag"]
        })

        # Configure smart recording
        pipeline.add_output("record", {
            "when_motion": True,
            "pre_buffer": 5,  # Record 5 seconds before motion
            "post_buffer": 10,  # Record 10 seconds after motion
            "metadata": {  # Store detection results with recordings
                "include_motion": True,
                "include_objects": True
            }
        })

        # Add real-time streaming output
        pipeline.add_output("rtsp", {
            "path": f"/{device_id}",
            "overlay": {
                "show_datetime": True,
                "show_camera_name": True,
                "show_detections": True
            }
        })
        
        # Run the pipeline
        app.run_pipeline(pipeline, device_id)

    # Start web interface
    app.start_web_server(port=8080)

    return app

if __name__ == "__main__":
    # Start the surveillance system
    app = setup_surveillance_system()
    
    # Keep the application running
    try:
        app.run_forever()
    except KeyboardInterrupt:
        app.shutdown()
