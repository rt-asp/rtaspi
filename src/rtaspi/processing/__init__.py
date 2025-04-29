"""
Processing module for rtaspi.

This module provides image and audio processing capabilities, including:
- Video filters (grayscale, edge detection, etc.)
- Audio filters (EQ, noise reduction, etc.)
- Object/face detection
- Speech recognition
- Pipeline execution
"""

__version__ = "1.0.0"
__author__ = "RT-ASP Team"
__all__ = [
    # Video processing
    "VideoFilter",
    "ObjectDetector",
    "FaceDetector",
    # Audio processing
    "AudioFilter",
    "SpeechRecognizer",
    # Pipeline execution
    "PipelineExecutor",
]

from .video.filters import VideoFilter
from .video.detection import ObjectDetector, FaceDetector
from .audio.filters import AudioFilter
from .audio.speech import SpeechRecognizer
from .pipeline_executor import PipelineExecutor

# Version history:
# 1.0.0 - Initial release with processing components
#       - Video filters and detection
#       - Audio filters and speech recognition
#       - Pipeline execution
