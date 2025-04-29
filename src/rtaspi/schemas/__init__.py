"""
schemas - Configuration schema definitions for rtaspi
"""

from .device import (
    DeviceType,
    DeviceProtocol,
    DeviceAuth,
    DeviceCapabilities,
    DeviceConfig,
    DeviceList
)

from .stream import (
    StreamType,
    StreamProtocol,
    StreamFormat,
    StreamQuality,
    StreamAuth,
    StreamOutput,
    StreamConfig,
    StreamList
)

from .pipeline import (
    PipelineType,
    FilterType,
    FilterConfig,
    PipelineStage,
    ResourceLimits,
    PipelineConfig,
    PipelineList
)

__all__ = [
    # Device schemas
    'DeviceType',
    'DeviceProtocol',
    'DeviceAuth',
    'DeviceCapabilities',
    'DeviceConfig',
    'DeviceList',
    
    # Stream schemas
    'StreamType',
    'StreamProtocol',
    'StreamFormat',
    'StreamQuality',
    'StreamAuth',
    'StreamOutput',
    'StreamConfig',
    'StreamList',
    
    # Pipeline schemas
    'PipelineType',
    'FilterType',
    'FilterConfig',
    'PipelineStage',
    'ResourceLimits',
    'PipelineConfig',
    'PipelineList'
]
