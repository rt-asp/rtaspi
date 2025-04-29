#!/usr/bin/env python3
"""
Advanced camera stream example demonstrating complex video processing pipeline
with motion detection, object tracking, and multiple output streams.
"""

from rtaspi.quick.camera import Camera
from rtaspi.processing.video.detection import MotionDetector
from rtaspi.processing.video.filters import VideoFilter
from rtaspi.streaming.rtmp import RTMPOutput
from rtaspi.streaming.rtsp import RTSPOutput
from rtaspi.security.analysis.motion import MotionAnalyzer

def setup_advanced_camera():
    # Initialize camera with high resolution and framerate
    camera = Camera.create(
        resolution=(1920, 1080),
        framerate=30,
        format='h264'
    )
    
    # Create video processing pipeline
    motion_detector = MotionDetector(
        sensitivity=0.8,
        min_area=500,
        blur_size=5
    )
    
    # Add various video filters
    filters = [
        VideoFilter.denoise(strength=3),
        VideoFilter.sharpen(amount=1.5),
        VideoFilter.contrast(factor=1.2)
    ]
    
    # Setup motion analysis
    analyzer = MotionAnalyzer(
        zones=[
            {"name": "entrance", "coords": [(0, 0), (640, 0), (640, 480), (0, 480)]},
            {"name": "parking", "coords": [(640, 0), (1280, 0), (1280, 480), (640, 480)]}
        ],
        trigger_threshold=0.3
    )
    
    # Configure multiple output streams
    rtmp_output = RTMPOutput(
        server="rtmp://streaming.example.com/live",
        stream_key="camera1",
        bitrate="2M"
    )
    
    rtsp_output = RTSPOutput(
        port=8554,
        path="/camera1",
        authentication={"username": "admin", "password": "secure123"}
    )
    
    def on_motion(zone, confidence):
        print(f"Motion detected in {zone} with confidence {confidence:.2f}")
    
    # Start streaming with all components
    camera.start_streaming(
        motion_detector=motion_detector,
        filters=filters,
        analyzer=analyzer,
        outputs=[rtmp_output, rtsp_output],
        on_motion=on_motion
    )

if __name__ == "__main__":
    setup_advanced_camera()
