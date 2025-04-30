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
from rtaspi.core import config, logging as rtaspi_logging, mcp
from rtaspi.constants import DeviceType

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

def setup_streaming(args: argparse.Namespace, config_manager: config.ConfigManager, mcp_broker: mcp.MCPBroker) -> Optional[str]:
    """Initialize and configure the camera streaming."""
    try:
        # Parse resolution
        width, height = map(int, args.resolution.split("x"))
        
        # Configure RTSP URL
        rtsp_url = f"rtsp://localhost:{args.rtsp_port}/camera"
        
        # Start camera stream
        stream_name = camera.start_camera(
            name=args.device,
            type=DeviceType.USB_CAMERA.value,
            resolution=f"{width}x{height}",
            framerate=args.fps,
            rtsp_url=rtsp_url,
            rtmp_url=args.save_file if args.save_file else None,
            config=config_manager.config,
            mcp_broker=mcp_broker
        )
            
        return stream_name
    
    except Exception as e:
        logger.error(f"Failed to setup camera streaming: {e}")
        return None

def main() -> int:
    """Main function."""
    args = parse_args()
    
    # Initialize config and logging
    config_manager = config.ConfigManager()
    log_level = "DEBUG" if args.verbose else "INFO"
    config_manager.set_config("system", "log_level", log_level)
    config_manager.set_config("system", "storage_path", "storage")
    rtaspi_logging.setup_logging(config_manager.config)
    
    # Initialize MCP broker
    mcp_broker = mcp.MCPBroker()
    
    # Initialize streaming
    stream_name = setup_streaming(args, config_manager, mcp_broker)
    if not stream_name:
        return 1
    
    try:
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
        if stream_name:
            camera.stop_camera(stream_name, config=config_manager.config, mcp_broker=mcp_broker)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
