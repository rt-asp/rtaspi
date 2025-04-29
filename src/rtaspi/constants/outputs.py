"""
Constants and enumerations for output types supported by the system.
"""

from enum import Enum, auto


class OutputType(Enum):
    """Enumeration of supported output types for video and audio streams."""

    # Streaming Outputs
    RTSP = auto()
    RTMP = auto()
    WEBRTC = auto()
    HLS = auto()
    MPEG_DASH = auto()
    SRT = auto()

    # File Outputs
    MP4_FILE = auto()
    MKV_FILE = auto()
    AVI_FILE = auto()
    MOV_FILE = auto()
    WAV_FILE = auto()
    MP3_FILE = auto()
    AAC_FILE = auto()
    JPEG_SEQUENCE = auto()
    PNG_SEQUENCE = auto()

    # Event/Special Outputs
    EVENT_WEBSOCKET = auto()  # For real-time events (motion detection, etc.)
    EVENT_MQTT = auto()  # For IoT integration
    EVENT_HTTP = auto()  # For webhook notifications
    VIRTUAL_DEVICE = auto()  # Output as virtual camera/microphone
    DISPLAY = auto()  # Local display output

    @classmethod
    def streaming_outputs(cls) -> list["OutputType"]:
        """Return a list of streaming output types."""
        return [
            cls.RTSP,
            cls.RTMP,
            cls.WEBRTC,
            cls.HLS,
            cls.MPEG_DASH,
            cls.SRT,
        ]

    @classmethod
    def file_outputs(cls) -> list["OutputType"]:
        """Return a list of file output types."""
        return [
            cls.MP4_FILE,
            cls.MKV_FILE,
            cls.AVI_FILE,
            cls.MOV_FILE,
            cls.WAV_FILE,
            cls.MP3_FILE,
            cls.AAC_FILE,
            cls.JPEG_SEQUENCE,
            cls.PNG_SEQUENCE,
        ]

    @classmethod
    def event_outputs(cls) -> list["OutputType"]:
        """Return a list of event/special output types."""
        return [
            cls.EVENT_WEBSOCKET,
            cls.EVENT_MQTT,
            cls.EVENT_HTTP,
            cls.VIRTUAL_DEVICE,
            cls.DISPLAY,
        ]

    @classmethod
    def video_outputs(cls) -> list["OutputType"]:
        """Return a list of output types that support video."""
        return [
            cls.RTSP,
            cls.RTMP,
            cls.WEBRTC,
            cls.HLS,
            cls.MPEG_DASH,
            cls.SRT,
            cls.MP4_FILE,
            cls.MKV_FILE,
            cls.AVI_FILE,
            cls.MOV_FILE,
            cls.JPEG_SEQUENCE,
            cls.PNG_SEQUENCE,
            cls.VIRTUAL_DEVICE,
            cls.DISPLAY,
        ]

    @classmethod
    def audio_outputs(cls) -> list["OutputType"]:
        """Return a list of output types that support audio."""
        return [
            cls.RTSP,
            cls.RTMP,
            cls.WEBRTC,
            cls.HLS,
            cls.MPEG_DASH,
            cls.SRT,
            cls.MP4_FILE,
            cls.MKV_FILE,
            cls.AVI_FILE,
            cls.MOV_FILE,
            cls.WAV_FILE,
            cls.MP3_FILE,
            cls.AAC_FILE,
            cls.VIRTUAL_DEVICE,
        ]

    def is_streaming_output(self) -> bool:
        """Check if this is a streaming output type."""
        return self in self.streaming_outputs()

    def is_file_output(self) -> bool:
        """Check if this is a file output type."""
        return self in self.file_outputs()

    def is_event_output(self) -> bool:
        """Check if this is an event/special output type."""
        return self in self.event_outputs()

    def supports_video(self) -> bool:
        """Check if this output type supports video streams."""
        return self in self.video_outputs()

    def supports_audio(self) -> bool:
        """Check if this output type supports audio streams."""
        return self in self.audio_outputs()
