"""
Stream management API facade.

This module provides a high-level interface for managing audio/video streams,
abstracting away the internal implementation details.
"""

from typing import Optional, Dict, List, Any, Union
import logging

from rtaspi.constants import OutputType, FilterType
from rtaspi.schemas import (
    StreamConfig,
    StreamStatus,
    StreamSource,
    StreamFilter,
    StreamOutput,
)
from rtaspi.streaming import RTSPServer, RTMPServer, WebRTCServer


class StreamAPI:
    """High-level API for stream management."""

    def __init__(self):
        """Initialize the stream API."""
        self.logger = logging.getLogger(__name__)
        self.rtsp_server = RTSPServer()
        self.rtmp_server = RTMPServer()
        self.webrtc_server = WebRTCServer()
        self.streams: Dict[str, StreamConfig] = {}

    def list_streams(
        self,
        device: Optional[str] = None,
        stream_type: Optional[str] = None,
        include_status: bool = True,
    ) -> Dict[str, Dict[str, Any]]:
        """List all configured streams.

        Args:
            device: Optional filter by source device
            stream_type: Optional filter by stream type (video, audio, both)
            include_status: Whether to include stream status information

        Returns:
            Dictionary mapping stream names to their configurations
        """
        streams = {}

        for name, config in self.streams.items():
            # Apply device filter
            if device and config.source.device_name != device:
                continue

            # Apply type filter
            if stream_type and config.source.stream_type != stream_type:
                continue

            # Convert to dict for modification
            stream_dict = config.dict()

            # Add status if requested
            if include_status:
                stream_dict["status"] = self.get_stream_status(name).dict()

            streams[name] = stream_dict

        return streams

    def get_stream(self, name: str) -> Optional[Dict[str, Any]]:
        """Get stream configuration by name.

        Args:
            name: Stream name

        Returns:
            Stream configuration if found, None otherwise
        """
        if name in self.streams:
            return self.streams[name].dict()
        return None

    def create_stream(
        self,
        name: str,
        device: str,
        stream_type: str,
        enabled: bool = True,
        filters: Optional[List[Dict[str, Any]]] = None,
        outputs: Optional[List[Dict[str, Any]]] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Create a new stream.

        Args:
            name: Unique stream name
            device: Source device name
            stream_type: Stream type (video, audio, both)
            enabled: Whether the stream is enabled
            filters: List of filter configurations
            outputs: List of output configurations
            settings: Stream-specific settings
        """
        if name in self.streams:
            raise ValueError(f"Stream already exists: {name}")

        # Create stream config
        config = {
            "name": name,
            "enabled": enabled,
            "source": {
                "device_name": device,
                "stream_type": stream_type,
                "enabled": True,
            },
            "filters": filters or [],
            "outputs": outputs or [],
            "settings": settings or {},
        }

        # Validate config
        stream_config = StreamConfig(**config)

        # Store stream
        self.streams[name] = stream_config

    def remove_stream(self, name: str) -> None:
        """Remove a stream.

        Args:
            name: Stream name
        """
        if name not in self.streams:
            raise ValueError(f"Stream not found: {name}")

        # Stop stream if running
        if self.get_stream_status(name).active:
            self.stop_stream(name)

        # Remove stream
        del self.streams[name]

    def update_stream(
        self,
        name: str,
        enabled: Optional[bool] = None,
        filters: Optional[List[Dict[str, Any]]] = None,
        outputs: Optional[List[Dict[str, Any]]] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update stream configuration.

        Args:
            name: Stream name
            enabled: Whether the stream is enabled
            filters: List of filter configurations
            outputs: List of output configurations
            settings: Stream-specific settings
        """
        if name not in self.streams:
            raise ValueError(f"Stream not found: {name}")

        stream = self.streams[name]
        config = stream.dict()

        # Update configuration
        if enabled is not None:
            config["enabled"] = enabled
        if filters is not None:
            config["filters"] = filters
        if outputs is not None:
            config["outputs"] = outputs
        if settings is not None:
            config["settings"] = {**config.get("settings", {}), **settings}

        # Validate updated config
        stream_config = StreamConfig(**config)

        # Store updated stream
        self.streams[name] = stream_config

    def get_stream_status(self, name: str) -> StreamStatus:
        """Get stream status.

        Args:
            name: Stream name

        Returns:
            Current stream status
        """
        if name not in self.streams:
            raise ValueError(f"Stream not found: {name}")

        # Get status from appropriate server based on outputs
        stream = self.streams[name]
        status = StreamStatus()

        for output in stream.outputs:
            if output.type == OutputType.RTSP:
                output_status = self.rtsp_server.get_stream_status(name)
            elif output.type == OutputType.RTMP:
                output_status = self.rtmp_server.get_stream_status(name)
            elif output.type == OutputType.WEBRTC:
                output_status = self.webrtc_server.get_stream_status(name)
            else:
                continue

            # Combine status from all outputs
            status.active = status.active or output_status.active
            if output_status.error:
                status.error = output_status.error
            if output_status.start_time:
                status.start_time = output_status.start_time
            if output_status.duration:
                status.duration = output_status.duration
            status.stats.update(output_status.stats)

        return status

    def start_stream(self, name: str) -> None:
        """Start a stream.

        Args:
            name: Stream name
        """
        if name not in self.streams:
            raise ValueError(f"Stream not found: {name}")

        stream = self.streams[name]
        if not stream.enabled:
            raise ValueError(f"Stream is disabled: {name}")

        # Start stream on each configured output
        for output in stream.outputs:
            if output.type == OutputType.RTSP:
                self.rtsp_server.start_stream(name, stream)
            elif output.type == OutputType.RTMP:
                self.rtmp_server.start_stream(name, stream)
            elif output.type == OutputType.WEBRTC:
                self.webrtc_server.start_stream(name, stream)

    def stop_stream(self, name: str) -> None:
        """Stop a stream.

        Args:
            name: Stream name
        """
        if name not in self.streams:
            raise ValueError(f"Stream not found: {name}")

        # Stop stream on each configured output
        stream = self.streams[name]
        for output in stream.outputs:
            if output.type == OutputType.RTSP:
                self.rtsp_server.stop_stream(name)
            elif output.type == OutputType.RTMP:
                self.rtmp_server.stop_stream(name)
            elif output.type == OutputType.WEBRTC:
                self.webrtc_server.stop_stream(name)

    def restart_stream(self, name: str) -> None:
        """Restart a stream.

        Args:
            name: Stream name
        """
        self.stop_stream(name)
        self.start_stream(name)

    def add_filter(
        self,
        name: str,
        filter_type: Union[FilterType, str],
        order: Optional[int] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a filter to a stream.

        Args:
            name: Stream name
            filter_type: Type of filter to add
            order: Order in which to apply the filter
            params: Filter-specific parameters
        """
        if name not in self.streams:
            raise ValueError(f"Stream not found: {name}")

        # Convert string type to enum if needed
        if isinstance(filter_type, str):
            filter_type = FilterType[filter_type]

        stream = self.streams[name]
        filters = list(stream.filters)

        # Determine filter order
        if order is None:
            order = max((f.order for f in filters), default=-1) + 1

        # Create filter config
        filter_config = StreamFilter(
            type=filter_type, enabled=True, order=order, params=params or {}
        )

        # Add filter and sort by order
        filters.append(filter_config)
        filters.sort(key=lambda f: f.order)

        # Update stream config
        self.update_stream(name, filters=[f.dict() for f in filters])

    def remove_filter(self, name: str, filter_type: Union[FilterType, str]) -> None:
        """Remove a filter from a stream.

        Args:
            name: Stream name
            filter_type: Type of filter to remove
        """
        if name not in self.streams:
            raise ValueError(f"Stream not found: {name}")

        # Convert string type to enum if needed
        if isinstance(filter_type, str):
            filter_type = FilterType[filter_type]

        stream = self.streams[name]
        filters = [f for f in stream.filters if f.type != filter_type]

        # Update stream config
        self.update_stream(name, filters=[f.dict() for f in filters])

    def add_output(
        self,
        name: str,
        output_type: Union[OutputType, str],
        output_name: str,
        settings: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add an output to a stream.

        Args:
            name: Stream name
            output_type: Type of output to add
            output_name: Unique name for this output
            settings: Output-specific settings
        """
        if name not in self.streams:
            raise ValueError(f"Stream not found: {name}")

        # Convert string type to enum if needed
        if isinstance(output_type, str):
            output_type = OutputType[output_type]

        stream = self.streams[name]
        outputs = list(stream.outputs)

        # Check for duplicate output name
        if any(o.name == output_name for o in outputs):
            raise ValueError(f"Output name already exists: {output_name}")

        # Create output config
        output_config = StreamOutput(
            type=output_type, enabled=True, name=output_name, settings=settings or {}
        )

        # Add output
        outputs.append(output_config)

        # Update stream config
        self.update_stream(name, outputs=[o.dict() for o in outputs])

    def remove_output(self, name: str, output_name: str) -> None:
        """Remove an output from a stream.

        Args:
            name: Stream name
            output_name: Name of output to remove
        """
        if name not in self.streams:
            raise ValueError(f"Stream not found: {name}")

        stream = self.streams[name]
        outputs = [o for o in stream.outputs if o.name != output_name]

        if len(outputs) == len(stream.outputs):
            raise ValueError(f"Output not found: {output_name}")

        # Update stream config
        self.update_stream(name, outputs=[o.dict() for o in outputs])
