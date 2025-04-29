"""
Central point for all schema definitions used in the rtaspi library.

This module provides easy access to all schema models through a clean interface:

from rtaspi.schemas import (
    DeviceConfig, DeviceStatus,
    StreamConfig, StreamStatus,
    PipelineConfig, PipelineStatus
)

It also provides version information and metadata about the schemas module.
"""

__version__ = "1.0.0"
__author__ = "RT-ASP Team"
__all__ = [
    # Device schemas
    "DeviceAuth",
    "DeviceConnection",
    "DeviceCapabilities",
    "DeviceConfig",
    "DeviceStatus",
    # Stream schemas
    "StreamSource",
    "StreamFilter",
    "StreamOutput",
    "StreamEncoding",
    "StreamConfig",
    "StreamStatus",
    # Pipeline schemas
    "PipelineStage",
    "ResourceLimits",
    "ExecutionSettings",
    "ErrorHandling",
    "PipelineConfig",
    "PipelineStatus",
]

from .device import (
    DeviceAuth,
    DeviceConnection,
    DeviceCapabilities,
    DeviceConfig,
    DeviceStatus,
)

from .stream import (
    StreamSource,
    StreamFilter,
    StreamOutput,
    StreamEncoding,
    StreamConfig,
    StreamStatus,
)

from .pipeline import (
    PipelineStage,
    ResourceLimits,
    ExecutionSettings,
    ErrorHandling,
    PipelineConfig,
    PipelineStatus,
)

# Version history:
# 1.0.0 - Initial release with core schemas
#       - Device schemas: Configuration and status for devices
#       - Stream schemas: Configuration and status for streams
#       - Pipeline schemas: Configuration and status for processing pipelines
