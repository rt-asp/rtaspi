#!/usr/bin/env python3
"""
Advanced camera stream example demonstrating complex video processing pipeline
with motion detection, object tracking, and multiple output streams.
"""

import argparse
import logging
import sys
from typing import Optional

from rtaspi.quick import camera
from rtaspi.core import logging as rtaspi_logging
from rtaspi.constants.logging import DEFAULT_LOGGING_CONFIG
from rtaspi.processing.video.detection import detect_motion
from rtaspi.processing.video.filters import apply_filters
from rtaspi.security.analysis.motion import analyze_motion
from rtaspi.constants.devices import DEVICE_SUBTYPE_USB
from rtaspi.constants.filters import DEFAULT_VIDEO_FILTERS
from rtaspi.constants.resolutions import RES_FULL_HD
from rtaspi.constants.streaming import (
    DEFAULT_RTSP_PORT,
    DEFAULT_RTMP_URL,
    DEFAULT_STREAM_PATH,
    DEFAULT_VIDEO_FRAMERATE
)
from rtaspi.constants.camera import DEFAULT_CAMERA_DEVICE
from rtaspi.constants.detection import (
    MOTION_SENSITIVITY,
    MOTION_MIN_AREA,
    MOTION_BLUR_SIZE,
    MOTION_TRIGGER_THRESHOLD,
    DEFAULT_ZONES
)

# Configure logging
logger = logging.getLogger(__name__)

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Advanced camera streaming example")
    
    parser.add_argument(
        "--device",
        type=str,
        default=DEFAULT_CAMERA_DEVICE,
        help=f"Camera device (number or path, default: {DEFAULT_CAMERA_DEVICE})"
    )
    
    parser.add_argument(
        "--rtmp-url",
        type=str,
        default=DEFAULT_RTMP_URL,
        help=f"RTMP streaming URL (default: {DEFAULT_RTMP_URL})"
    )
    
    parser.add_argument(
        "--rtsp-port",
        type=int,
        default=DEFAULT_RTSP_PORT,
        help=f"RTSP server port (default: {DEFAULT_RTSP_PORT})"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()

def setup_advanced_camera(args: argparse.Namespace) -> Optional[tuple[str, str]]:
    """Initialize and configure the advanced camera streaming.
    
    Returns:
        Tuple of (stream_name, rtsp_url) if successful, None otherwise
    """
    try:
        # Configure stream URLs
        rtsp_url = f"rtsp://localhost:{args.rtsp_port}/{DEFAULT_STREAM_PATH}"
        
        # Start camera stream with high resolution
        stream_name = camera.start_camera(
            name=args.device,
            type=DEVICE_SUBTYPE_USB,
            resolution=RES_FULL_HD,
            framerate=DEFAULT_VIDEO_FRAMERATE,
            rtsp_url=rtsp_url,
            rtmp_url=args.rtmp_url
        )
        
        # Configure motion detection settings
        detect_motion(
            stream_name,
            sensitivity=MOTION_SENSITIVITY,
            min_area=MOTION_MIN_AREA,
            blur_size=MOTION_BLUR_SIZE
        )
        
        # Apply video filters
        apply_filters(stream_name, filters=DEFAULT_VIDEO_FILTERS)
        
        # Setup motion analysis zones
        analyze_motion(
            stream_name,
            zones=DEFAULT_ZONES,
            trigger_threshold=MOTION_TRIGGER_THRESHOLD,
            callback=lambda zone, conf: logger.info(f"Motion in {zone}: {conf:.2f}")
        )
            
        return stream_name, rtsp_url
    
    except Exception as e:
        logger.error(f"Failed to setup camera streaming: {e}")
        return None

def main() -> int:
    """Main function."""
    args = parse_args()
    
    # Configure logging
    logging_config = DEFAULT_LOGGING_CONFIG.copy()
    if args.verbose:
        logging_config["system"]["log_level"] = "DEBUG"
    rtaspi_logging.setup_logging(logging_config)
    
    # Initialize streaming
    result = setup_advanced_camera(args)
    if not result:
        return 1
    
    stream_name, rtsp_url = result
    try:
        # Print stream URLs
        logger.info(f"RTSP stream available at: {rtsp_url}")
        logger.info(f"RTMP stream publishing to: {args.rtmp_url}")
        
        # Wait for user input
        logger.info("Press Ctrl+C to stop streaming")
        while True:
            try:
                input()
            except KeyboardInterrupt:
                break
    
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        return 1
    
    finally:
        # Cleanup
        logger.info("Stopping stream...")
        if stream_name:
            camera.stop_camera(stream_name)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
