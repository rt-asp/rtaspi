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

def setup_microphone(args: argparse.Namespace) -> Optional[microphone.Microphone]:
    """Initialize and configure the microphone."""
    try:
        # Start microphone
        mic = microphone.start_microphone(
            device=args.device,
            rate=args.rate,
            channels=args.channels
        )
        
        # Add audio filters
        if args.gain != 1.0:
            mic.add_filter("gain", value=args.gain)
        if args.noise_reduction:
            mic.add_filter("noise_reduction")
            
        # Configure outputs
        mic.add_output(
            "file",
            path=args.output,
            format=args.format
        )
        
        if args.monitor:
            mic.add_output("monitor")
            
        return mic
    
    except Exception as e:
        logger.error(f"Failed to setup microphone: {e}")
        return None

def main() -> int:
    """Main function."""
    args = parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    rtaspi_logging.setup_logging(level=log_level)
    
    # Initialize microphone
    mic = setup_microphone(args)
    if not mic:
        return 1
    
    try:
        # Start recording
        logger.info("Starting audio recording...")
        mic.start()
        
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
        if mic:
            mic.stop()
            logger.info(f"Recording saved to: {args.output}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
