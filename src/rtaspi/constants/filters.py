"""
Constants for video and audio filter settings.
"""
from enum import Enum

class FilterType(Enum):
    NOISE_REDUCTION = "noise_reduction"
    SHARPEN = "sharpen"
    CONTRAST = "contrast"
    BRIGHTNESS = "brightness"
    SATURATION = "saturation"
    HUE = "hue"
    GAMMA = "gamma"
    BLUR = "blur"

# Default filter settings
DEFAULT_NOISE_REDUCTION_STRENGTH = 3
DEFAULT_SHARPEN_AMOUNT = 1.5
DEFAULT_CONTRAST_FACTOR = 1.2
DEFAULT_BRIGHTNESS_FACTOR = 1.0
DEFAULT_SATURATION_FACTOR = 1.0
DEFAULT_HUE_SHIFT = 0
DEFAULT_GAMMA_FACTOR = 1.0
DEFAULT_BLUR_RADIUS = 1

# Default filter configurations
DEFAULT_VIDEO_FILTERS = [
    {
        "type": FilterType.NOISE_REDUCTION.value,
        "strength": DEFAULT_NOISE_REDUCTION_STRENGTH
    },
    {
        "type": FilterType.SHARPEN.value,
        "amount": DEFAULT_SHARPEN_AMOUNT
    },
    {
        "type": FilterType.CONTRAST.value,
        "factor": DEFAULT_CONTRAST_FACTOR
    }
]
