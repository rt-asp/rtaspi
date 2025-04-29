"""
schemas - Configuration schema definitions for rtaspi
"""

from .device import (
    DeviceType,
    DeviceProtocol,
    DeviceAuth,
    DeviceCapabilities,
    DeviceConfig,
    DeviceStatus,
    DeviceConnection,
    DeviceList,
)

from .stream import (
    StreamType,
    StreamProtocol,
    StreamFormat,
    StreamQuality,
    StreamAuth,
    StreamOutput,
    StreamConfig,
    StreamList,
    StreamStatus,
    StreamSource,
    StreamFilter,
)

from .pipeline import (
    PipelineType,
    FilterType,
    FilterConfig,
    PipelineStage,
    ResourceLimits,
    PipelineConfig,
    PipelineList,
    PipelineStatus,
    ExecutionSettings,
    ErrorHandling,
)

__all__ = [
    # Device schemas
    "DeviceType",
    "DeviceProtocol",
    "DeviceAuth",
    "DeviceCapabilities",
    "DeviceConfig",
    "DeviceStatus",
    "DeviceConnection",
    "DeviceList",
    # Stream schemas
    "StreamType",
    "StreamProtocol",
    "StreamFormat",
    "StreamQuality",
    "StreamAuth",
    "StreamOutput",
    "StreamConfig",
    "StreamList",
    "StreamStatus",
    "StreamSource",
    "StreamFilter",
    # Pipeline schemas
    "PipelineType",
    "FilterType",
    "FilterConfig",
    "PipelineStage",
    "ResourceLimits",
    "PipelineConfig",
    "PipelineList",
    "PipelineStatus",
    "ExecutionSettings",
    "ErrorHandling",
]
