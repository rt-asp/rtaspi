#!/usr/bin/env python3
"""
Motion Detection Pipeline Example
Shows how to use RTASPI for motion detection and tracking
"""

import argparse
import logging
import sys
from typing import Optional

from rtaspi.quick import camera
from rtaspi.core import logging as rtaspi_logging
from rtaspi.processing.video.detection import detect_motion
from rtaspi.security.analysis.motion import analyze_motion

# Configure logging
logger = logging.getLogger(__name__)

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Motion Detection Pipeline")
    
    parser.add_argument(
        "--device",
        type=str,
        default="0",
        help="Camera device (number or path, default: 0)"
    )
    
    parser.add_argument(
        "--sensitivity",
        type=float,
        default=0.8,
        help="Motion detection sensitivity (0-1)"
    )
    
    parser.add_argument(
        "--min-area",
        type=int,
        default=500,
        help="Minimum motion area in pixels"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="motion_output.mp4",
        help="Output file path"
    )
    
    parser.add_argument(
        "--rtsp-port",
        type=int,
        default=8554,
        help="RTSP server port (default: 8554)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()

def setup_motion_detection(args: argparse.Namespace) -> Optional[str]:
    """Initialize and configure the motion detection pipeline."""
    try:
        # Configure stream URLs
        rtsp_url = f"rtsp://localhost:{args.rtsp_port}/motion"
        rtmp_url = f"file://{args.output}"
        
        # Start camera stream
        stream_name = camera.start_camera(
            name=args.device,
            type="USB_CAMERA",
            resolution="1280x720",
            framerate=30,
            rtsp_url=rtsp_url,
            rtmp_url=rtmp_url
        )
        
        # Configure motion detection
        detect_motion(
            stream_name,
            sensitivity=args.sensitivity,
            min_area=args.min_area,
            blur_size=5
        )
        
        # Setup motion analysis zones
        analyze_motion(
            stream_name,
            zones=[
                {"name": "full_frame", "coords": [(0, 0), (1280, 0), (1280, 720), (0, 720)]}
            ],
            trigger_threshold=args.sensitivity,
            callback=lambda zone, conf: logger.info(f"Motion detected in {zone} with confidence {conf:.2f}")
        )
            
        return stream_name
    
    except Exception as e:
        logger.error(f"Failed to setup motion detection: {e}")
        return None

def main() -> int:
    """Main function."""
    args = parse_args()
    
    # Configure logging
    log_level = "DEBUG" if args.verbose else "INFO"
    logging_config = {
        "system": {
            "log_level": log_level,
            "storage_path": "storage"
        }
    }
    rtaspi_logging.setup_logging(logging_config)
    
    # Initialize motion detection
    stream_name = setup_motion_detection(args)
    if not stream_name:
        return 1
    
    try:
        # Print stream URLs
        rtsp_url = f"rtsp://localhost:{args.rtsp_port}/motion"
        logger.info(f"RTSP stream available at: {rtsp_url}")
        logger.info(f"Recording motion to: {args.output}")
        
        # Wait for user input
        logger.info("Press Ctrl+C to stop")
        while True:
            try:
                input()
            except KeyboardInterrupt:
                break
    
    except Exception as e:
        logger.error(f"Motion detection error: {e}")
        return 1
    
    finally:
        # Cleanup
        logger.info("Stopping motion detection...")
        if stream_name:
            camera.stop_camera(stream_name)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
