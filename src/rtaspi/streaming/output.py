"""Stream output configuration and management."""

import cv2
from dataclasses import dataclass
from typing import Optional, Dict, Any, Union
import numpy as np
import importlib
import warnings

# Global variable to store sounddevice module
_sounddevice = None

def _get_sounddevice():
    """Get the sounddevice module, importing it only when needed."""
    global _sounddevice
    if _sounddevice is None:
        try:
            _sounddevice = importlib.import_module('sounddevice')
        except ImportError:
            raise ImportError("sounddevice package is required for audio output. Install it with: pip install sounddevice")
    return _sounddevice


class AudioOutput:
    """Audio output for playing processed audio."""

    def __init__(self, sample_rate: int = 44100, channels: int = 2):
        """Initialize audio output.

        Args:
            sample_rate: Audio sample rate in Hz
            channels: Number of audio channels (1 for mono, 2 for stereo)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.stream = None
        
    def write(self, audio: np.ndarray) -> None:
        """Write audio data to output.

        Args:
            audio: Audio data to write
        """
        sd = _get_sounddevice()
        if self.stream is None:
            self.stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.float32
            )
            self.stream.start()
            
        self.stream.write(audio)
        
    def close(self) -> None:
        """Close audio output."""
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None


class StreamOutput:
    """RTSP stream output."""

    def __init__(self, port: int = 8554, path: str = "stream"):
        """Initialize RTSP stream output.

        Args:
            port: RTSP server port
            path: Stream path
        """
        self.port = port
        self.path = path
        self.url = f"rtsp://localhost:{port}/{path}"
        self.stream = None

    def write(self, frame: np.ndarray) -> None:
        """Write frame to stream.

        Args:
            frame: Frame to write
        """
        if self.stream is None:
            height, width = frame.shape[:2]
            self.stream = cv2.VideoWriter(
                self.url,
                cv2.VideoWriter_fourcc(*'H264'),
                30,
                (width, height)
            )

        self.stream.write(frame)

    def close(self) -> None:
        """Close stream."""
        if self.stream is not None:
            self.stream.release()
            self.stream = None


class FileOutput:
    """File output for saving video."""

    def __init__(self, path: str, fps: int = 30):
        """Initialize file output.

        Args:
            path: Output file path
            fps: Frames per second
        """
        self.path = path
        self.fps = fps
        self.writer = None

    def write(self, frame: np.ndarray) -> None:
        """Write frame to file.

        Args:
            frame: Frame to write
        """
        if self.writer is None:
            height, width = frame.shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.writer = cv2.VideoWriter(
                self.path,
                fourcc,
                self.fps,
                (width, height)
            )

        self.writer.write(frame)

    def close(self) -> None:
        """Close file output."""
        if self.writer is not None:
            self.writer.release()
            self.writer = None
