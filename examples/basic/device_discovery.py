#!/usr/bin/env python3
"""
Device discovery example using RTASPI.
Shows how to scan for devices and get their capabilities.
"""

import argparse
import logging
import sys
from typing import List, Optional

from rtaspi.device_managers import discovery
from rtaspi.core import logging as rtaspi_logging
from rtaspi.schemas.device import Device

# Configure logging
logger = logging.getLogger(__name__)

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Device discovery example")
    
    parser.add_argument(
        "--type",
        type=str,
        choices=["all", "camera", "microphone", "network", "industrial"],
        default="all",
        help="Device type to scan for (default: all)"
    )
    
    parser.add_argument(
        "--network",
        action="store_true",
        help="Include network device scanning"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=5,
        help="Network scan timeout in seconds (default: 5)"
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output device info as JSON"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()

def scan_devices(device_type: str, include_network: bool, timeout: int) -> List[Device]:
    """Scan for devices of specified type."""
    devices = []
    
    try:
        # Scan for local devices
        logger.info(f"Scanning for {'all' if device_type == 'all' else device_type} devices...")
        devices.extend(discovery.scan_devices(
            type=None if device_type == "all" else device_type
        ))
        
        # Scan network if requested
        if include_network:
            logger.info("Scanning network for devices...")
            devices.extend(discovery.scan_network_devices(
                type=None if device_type == "all" else device_type,
                timeout=timeout
            ))
    
    except Exception as e:
        logger.error(f"Error during device scanning: {e}")
    
    return devices

def print_device_info(device: Device, as_json: bool = False) -> None:
    """Print device information."""
    if as_json:
        import json
        print(json.dumps(device.dict(), indent=2))
    else:
        print(f"\nDevice: {device.name}")
        print(f"  Type: {device.type}")
        print(f"  ID: {device.id}")
        print("  Capabilities:")
        for cap, value in device.capabilities.items():
            print(f"    {cap}: {value}")
        if device.network_info:
            print("  Network Info:")
            print(f"    IP: {device.network_info.ip}")
            print(f"    Protocol: {device.network_info.protocol}")
        print("  Status:", "Available" if device.available else "Unavailable")

def main() -> int:
    """Main function."""
    args = parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    rtaspi_logging.setup_logging(level=log_level)
    
    try:
        # Scan for devices
        devices = scan_devices(args.type, args.network, args.timeout)
        
        if not devices:
            logger.info("No devices found")
            return 0
        
        # Print results
        logger.info(f"Found {len(devices)} device(s)")
        for device in devices:
            print_device_info(device, args.json)
        
        # Print example usage
        if not args.json:
            print("\nExample Usage:")
            for device in devices:
                if device.type == "camera":
                    print(f"\nTo use camera '{device.name}':")
                    print(f"  python camera_stream.py --device {device.id}")
                elif device.type == "microphone":
                    print(f"\nTo use microphone '{device.name}':")
                    print(f"  python microphone_recording.py --device {device.id}")
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
