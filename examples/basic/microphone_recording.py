#!/usr/bin/env python3
"""
Microphone recording example using RTASPI.
Shows how to capture audio and apply processing.
"""

import argparse
import logging
import sys
from typing import Optional

from rtaspi.quick import microphone
from rtaspi.core import config, logging as rtaspi_logging

# Configure logging
logger = logging.getLogger(__name__)

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Microphone recording example")
    
    parser.add_argument(
        "--device",
        type=str,
        default="default",
        help="Microphone device (name or index, default: default)"
    )
    
    parser.add_argument(
        "--rate",
        type=int,
        default=44100,
        help="Sample rate in Hz (default: 44100)"
    )
    
    parser.add_argument(
        "--channels",
        type=int,
        default=2,
        help="Number of channels (default: 2)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output file path (e.g., recording.wav)"
    )
    
    parser.add_argument(
        "--format",
        type=str,
        choices=["wav", "mp3", "ogg"],
        default="wav",
        help="Output file format (default: wav)"
    )
    
    parser.add_argument(
        "--gain",
        type=float,
        default=1.0,
        help="Audio gain multiplier (default: 1.0)"
    )
    
    parser.add_argument(
        "--noise-reduction",
        action="store_true",
        help="Enable noise reduction"
    )
    
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Enable audio monitoring through speakers"
    )
    
    parser.add_argument(
        "--duration",
        type=int,
        help="Recording duration in seconds (optional)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()

def setup_recording(args: argparse.Namespace) -> Optional[str]:
    """Initialize and configure the microphone recording."""
    try:
        # Configure RTMP URL for file output
        rtmp_url = f"file://{args.output}"
        
        # Start microphone stream
        stream_name = microphone.start_microphone(
            name=args.device,
            type="USB_MICROPHONE",
            sample_rate=args.rate,
            channels=args.channels,
            rtmp_url=rtmp_url
        )
            
        return stream_name
    
    except Exception as e:
        logger.error(f"Failed to setup microphone recording: {e}")
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
    
    # Initialize recording
    stream_name = setup_recording(args)
    if not stream_name:
        return 1
    
    try:
        # Print recording info
        logger.info(f"Recording to: {args.output}")
        if args.duration:
            logger.info(f"Recording will stop after {args.duration} seconds")
            import time
            time.sleep(args.duration)
        else:
            logger.info("Press Ctrl+C to stop recording")
            while True:
                try:
                    input()
                except KeyboardInterrupt:
                    break
    
    except Exception as e:
        logger.error(f"Recording error: {e}")
        return 1
    
    finally:
        # Cleanup
        logger.info("Stopping recording...")
        if stream_name:
            microphone.stop_microphone(stream_name)
            logger.info(f"Recording saved to: {args.output}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
