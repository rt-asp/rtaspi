"""
Constants and enumerations for filter types used in video and audio processing.
"""

from enum import Enum, auto


class FilterType(Enum):
    """Enumeration of available filter types for video and audio processing."""

    # Video Filters
    GRAYSCALE = auto()
    EDGE_DETECTION = auto()
    FACE_DETECTION = auto()
    MOTION_DETECTION = auto()
    BLUR = auto()
    SHARPEN = auto()
    COLOR_BALANCE = auto()
    BRIGHTNESS = auto()
    CONTRAST = auto()
    SATURATION = auto()
    HUE = auto()
    GAMMA = auto()
    THRESHOLD = auto()
    NOISE_REDUCTION = auto()

    # Audio Filters
    EQUALIZER = auto()
    NOISE_GATE = auto()
    COMPRESSOR = auto()
    REVERB = auto()
    ECHO = auto()
    PITCH_SHIFT = auto()
    TIME_STRETCH = auto()
    NORMALIZATION = auto()
    BANDPASS = auto()
    LOWPASS = auto()
    HIGHPASS = auto()

    @classmethod
    def video_filters(cls) -> list["FilterType"]:
        """Return a list of video-specific filters."""
        return [
            cls.GRAYSCALE,
            cls.EDGE_DETECTION,
            cls.FACE_DETECTION,
            cls.MOTION_DETECTION,
            cls.BLUR,
            cls.SHARPEN,
            cls.COLOR_BALANCE,
            cls.BRIGHTNESS,
            cls.CONTRAST,
            cls.SATURATION,
            cls.HUE,
            cls.GAMMA,
            cls.THRESHOLD,
            cls.NOISE_REDUCTION,
        ]

    @classmethod
    def audio_filters(cls) -> list["FilterType"]:
        """Return a list of audio-specific filters."""
        return [
            cls.EQUALIZER,
            cls.NOISE_GATE,
            cls.COMPRESSOR,
            cls.REVERB,
            cls.ECHO,
            cls.PITCH_SHIFT,
            cls.TIME_STRETCH,
            cls.NORMALIZATION,
            cls.BANDPASS,
            cls.LOWPASS,
            cls.HIGHPASS,
        ]

    def is_video_filter(self) -> bool:
        """Check if this filter is applicable to video streams."""
        return self in self.video_filters()

    def is_audio_filter(self) -> bool:
        """Check if this filter is applicable to audio streams."""
        return self in self.audio_filters()
