#!/usr/bin/env python3
"""
Basic camera streaming example using RTASPI.
Shows how to capture from a camera and stream via RTSP.
"""

import argparse
import logging
import sys
from typing import Optional

from rtaspi.quick import camera
from rtaspi.core import config, logging as rtaspi_logging

# Configure logging
logger = logging.getLogger(__name__)

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Camera streaming example")
    
    parser.add_argument(
        "--device",
        type=str,
        default="0",
        help="Camera device (number or path, default: 0)"
    )
    
    parser.add_argument(
        "--resolution",
        type=str,
        default="1280x720",
        help="Stream resolution (WxH, default: 1280x720)"
    )
    
    parser.add_argument(
        "--fps",
        type=int,
        default=30,
        help="Frames per second (default: 30)"
    )
    
    parser.add_argument(
        "--rtsp-port",
        type=int,
        default=8554,
        help="RTSP server port (default: 8554)"
    )
    
    parser.add_argument(
        "--save-file",
        type=str,
        help="Save stream to file (optional)"
    )
    
    parser.add_argument(
        "--brightness",
        type=float,
        default=1.0,
        help="Brightness adjustment (default: 1.0)"
    )
    
    parser.add_argument(
        "--contrast",
        type=float,
        default=1.0,
        help="Contrast adjustment (default: 1.0)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()

def setup_camera(args: argparse.Namespace) -> Optional[camera.Camera]:
    """Initialize and configure the camera."""
    try:
        # Parse resolution
        width, height = map(int, args.resolution.split("x"))
        
        # Start camera
        cam = camera.start_camera(
            device=args.device,
            width=width,
            height=height,
            fps=args.fps
        )
        
        # Add video filters
        if args.brightness != 1.0:
            cam.add_filter("brightness", value=args.brightness)
        if args.contrast != 1.0:
            cam.add_filter("contrast", value=args.contrast)
            
        # Configure outputs
        cam.add_output(
            "rtsp",
            port=args.rtsp_port,
            path="/camera"
        )
        
        if args.save_file:
            cam.add_output(
                "file",
                path=args.save_file,
                format="mp4"
            )
            
        return cam
    
    except Exception as e:
        logger.error(f"Failed to setup camera: {e}")
        return None

def main() -> int:
    """Main function."""
    args = parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    rtaspi_logging.setup_logging(level=log_level)
    
    # Initialize camera
    cam = setup_camera(args)
    if not cam:
        return 1
    
    try:
        # Start streaming
        logger.info("Starting camera stream...")
        cam.start()
        
        # Print stream URLs
        rtsp_url = f"rtsp://localhost:{args.rtsp_port}/camera"
        logger.info(f"RTSP stream available at: {rtsp_url}")
        
        if args.save_file:
            logger.info(f"Saving stream to: {args.save_file}")
        
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
        if cam:
            cam.stop()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
