"""
Simplified utility functions.

This module provides easy-to-use functions for common tasks like adding filters,
configuring outputs, and managing configuration files.
"""

from typing import Optional, Dict, Any, Union
import logging
import yaml
from pathlib import Path

from rtaspi.constants import FilterType, OutputType
from rtaspi.api import StreamAPI


def add_filter(
    stream_name: str,
    filter_type: Union[str, FilterType],
    params: Optional[Dict[str, Any]] = None,
) -> None:
    """Add a filter to a stream.

    Args:
        stream_name: Stream name (from start_camera/start_microphone)
        filter_type: Type of filter to add (e.g., "GRAYSCALE", "EDGE_DETECTION")
        params: Optional filter parameters
    """
    stream_api = StreamAPI()
    logger = logging.getLogger(__name__)

    # Add filter to stream
    stream_api.add_filter(
        name=stream_name, filter_type=filter_type, params=params or {}
    )
    logger.info(f"Added {filter_type} filter to stream: {stream_name}")


def remove_filter(stream_name: str, filter_type: Union[str, FilterType]) -> None:
    """Remove a filter from a stream.

    Args:
        stream_name: Stream name (from start_camera/start_microphone)
        filter_type: Type of filter to remove
    """
    stream_api = StreamAPI()
    logger = logging.getLogger(__name__)

    # Remove filter from stream
    stream_api.remove_filter(name=stream_name, filter_type=filter_type)
    logger.info(f"Removed {filter_type} filter from stream: {stream_name}")


def add_output(
    stream_name: str,
    output_type: Union[str, OutputType],
    url: str,
    settings: Optional[Dict[str, Any]] = None,
) -> None:
    """Add an output to a stream.

    Args:
        stream_name: Stream name (from start_camera/start_microphone)
        output_type: Type of output (e.g., "RTSP", "RTMP", "WEBRTC")
        url: Output URL
        settings: Optional output settings
    """
    stream_api = StreamAPI()
    logger = logging.getLogger(__name__)

    # Create output settings
    output_settings = settings or {}
    output_settings["url"] = url

    # Add output to stream
    stream_api.add_output(
        name=stream_name,
        output_type=output_type,
        output_name=f"{stream_name}_{output_type.lower()}",
        settings=output_settings,
    )
    logger.info(f"Added {output_type} output to stream: {stream_name}")


def remove_output(stream_name: str, output_name: str) -> None:
    """Remove an output from a stream.

    Args:
        stream_name: Stream name (from start_camera/start_microphone)
        output_name: Name of output to remove
    """
    stream_api = StreamAPI()
    logger = logging.getLogger(__name__)

    # Remove output from stream
    stream_api.remove_output(name=stream_name, output_name=output_name)
    logger.info(f"Removed output {output_name} from stream: {stream_name}")


def save_config(
    stream_name: str,
    file_path: str,
    include_filters: bool = True,
    include_outputs: bool = True,
) -> None:
    """Save stream configuration to a file.

    This function saves the current configuration of a stream to a YAML file,
    which can be loaded later to recreate the same setup.

    Args:
        stream_name: Stream name (from start_camera/start_microphone)
        file_path: Path to save configuration file
        include_filters: Whether to include filter configurations
        include_outputs: Whether to include output configurations
    """
    stream_api = StreamAPI()
    logger = logging.getLogger(__name__)

    # Get stream configuration
    stream = stream_api.get_stream(stream_name)
    if not stream:
        raise ValueError(f"Stream not found: {stream_name}")

    # Create configuration to save
    config = {
        "name": stream["name"],
        "device": stream["source"]["device_name"],
        "type": stream["source"]["stream_type"],
        "settings": stream["settings"],
    }

    if include_filters:
        config["filters"] = [
            {"type": f["type"], "params": f.get("params", {})}
            for f in stream["filters"]
        ]

    if include_outputs:
        config["outputs"] = [
            {"type": o["type"], "settings": o["settings"]} for o in stream["outputs"]
        ]

    # Save configuration
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)

    logger.info(f"Saved configuration to: {file_path}")


def load_config(file_path: str) -> str:
    """Load stream configuration from a file.

    This function loads a stream configuration from a YAML file and creates
    a new stream with the same setup.

    Args:
        file_path: Path to configuration file

    Returns:
        Name of created stream
    """
    stream_api = StreamAPI()
    logger = logging.getLogger(__name__)

    # Load configuration
    with open(file_path) as f:
        config = yaml.safe_load(f)

    # Create stream
    stream_name = config["name"]
    stream_api.create_stream(
        name=stream_name,
        device=config["device"],
        stream_type=config["type"],
        settings=config["settings"],
    )

    # Add filters
    for filter_config in config.get("filters", []):
        stream_api.add_filter(
            name=stream_name,
            filter_type=filter_config["type"],
            params=filter_config.get("params", {}),
        )

    # Add outputs
    for output_config in config.get("outputs", []):
        stream_api.add_output(
            name=stream_name,
            output_type=output_config["type"],
            output_name=f"{stream_name}_{output_config['type'].lower()}",
            settings=output_config["settings"],
        )

    # Start stream
    stream_api.start_stream(stream_name)
    logger.info(
        f"Loaded configuration from {file_path} and started stream: {stream_name}"
    )

    return stream_name
