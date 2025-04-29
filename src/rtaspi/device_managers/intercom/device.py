"""Intercom device implementation."""

import logging
import threading
import queue
import time
import numpy as np
from typing import Optional, Dict, Any, List

from ...core.logging import get_logger
from ..base import DeviceManager
from ...processing.audio.filters import (
    AudioFilter,
    NoiseReductionFilter,
    EchoCancellationFilter,
    FeedbackSuppressionFilter,
    GainControlFilter,
)

logger = get_logger(__name__)


class IntercomDevice:
    """Two-way audio communication device."""

    def __init__(self, device_id: str, config: Dict[str, Any]):
        """Initialize intercom device.

        Args:
            device_id: Device identifier
            config: Device configuration
        """
        self.device_id = device_id
        self.config = config

        # Audio settings
        self.sample_rate = config.get("sample_rate", 16000)
        self.channels = config.get("channels", 1)
        self.chunk_size = config.get("chunk_size", 1024)

        # Audio processing
        self._input_filters = [
            NoiseReductionFilter(),
            GainControlFilter(),
            EchoCancellationFilter(),
            FeedbackSuppressionFilter(),
        ]
        self._output_filters = [NoiseReductionFilter(), GainControlFilter()]

        # Audio buffers
        self._input_queue = queue.Queue()
        self._output_queue = queue.Queue()

        # Processing threads
        self._input_thread: Optional[threading.Thread] = None
        self._output_thread: Optional[threading.Thread] = None
        self._stop_processing = threading.Event()

        # State
        self._initialized = False
        self._input_enabled = False
        self._output_enabled = False

    def initialize(self) -> bool:
        """Initialize device.

        Returns:
            bool: True if initialization successful
        """
        if self._initialized:
            return True

        try:
            # Initialize audio filters
            for filter in self._input_filters + self._output_filters:
                if not filter.initialize(self.sample_rate, self.channels):
                    logger.error(
                        f"Failed to initialize filter: {filter.__class__.__name__}"
                    )
                    return False

            self._initialized = True
            logger.info(f"Initialized intercom device {self.device_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize intercom device: {e}")
            return False

    def cleanup(self) -> None:
        """Clean up device resources."""
        if self._initialized:
            try:
                self.stop_input()
                self.stop_output()

                # Clean up filters
                for filter in self._input_filters + self._output_filters:
                    filter.cleanup()

                self._initialized = False
                logger.info(f"Cleaned up intercom device {self.device_id}")

            except Exception as e:
                logger.error(f"Error cleaning up intercom device: {e}")

    def start_input(self) -> bool:
        """Start audio input processing.

        Returns:
            bool: True if started successfully
        """
        if not self._initialized:
            logger.error("Device not initialized")
            return False

        if self._input_enabled:
            logger.warning("Input already enabled")
            return True

        try:
            self._stop_processing.clear()
            self._input_thread = threading.Thread(target=self._process_input)
            self._input_thread.daemon = True
            self._input_thread.start()
            self._input_enabled = True
            logger.info("Started audio input")
            return True

        except Exception as e:
            logger.error(f"Failed to start audio input: {e}")
            return False

    def stop_input(self) -> None:
        """Stop audio input processing."""
        if self._input_enabled:
            self._stop_processing.set()
            if self._input_thread:
                self._input_thread.join()
                self._input_thread = None
            self._input_enabled = False
            logger.info("Stopped audio input")

    def start_output(self) -> bool:
        """Start audio output processing.

        Returns:
            bool: True if started successfully
        """
        if not self._initialized:
            logger.error("Device not initialized")
            return False

        if self._output_enabled:
            logger.warning("Output already enabled")
            return True

        try:
            self._stop_processing.clear()
            self._output_thread = threading.Thread(target=self._process_output)
            self._output_thread.daemon = True
            self._output_thread.start()
            self._output_enabled = True
            logger.info("Started audio output")
            return True

        except Exception as e:
            logger.error(f"Failed to start audio output: {e}")
            return False

    def stop_output(self) -> None:
        """Stop audio output processing."""
        if self._output_enabled:
            self._stop_processing.set()
            if self._output_thread:
                self._output_thread.join()
                self._output_thread = None
            self._output_enabled = False
            logger.info("Stopped audio output")

    def process_input(self, audio_data: np.ndarray) -> None:
        """Process input audio data.

        Args:
            audio_data: Audio samples as numpy array
        """
        if not self._input_enabled:
            return

        try:
            # Add to input queue
            self._input_queue.put(audio_data)
        except Exception as e:
            logger.error(f"Error processing input audio: {e}")

    def get_output(self) -> Optional[np.ndarray]:
        """Get processed output audio data.

        Returns:
            Optional[np.ndarray]: Audio samples if available
        """
        if not self._output_enabled:
            return None

        try:
            return self._output_queue.get_nowait()
        except queue.Empty:
            return None
        except Exception as e:
            logger.error(f"Error getting output audio: {e}")
            return None

    def _process_input(self) -> None:
        """Input audio processing loop."""
        while not self._stop_processing.is_set():
            try:
                # Get audio from queue with timeout
                try:
                    audio_data = self._input_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                # Apply input filters
                filtered_audio = audio_data
                for filter in self._input_filters:
                    filtered_audio = filter.process(filtered_audio, self.sample_rate)

                # Add to output queue
                self._output_queue.put(filtered_audio)

            except Exception as e:
                logger.error(f"Error in input processing: {e}")
                time.sleep(0.1)

    def _process_output(self) -> None:
        """Output audio processing loop."""
        while not self._stop_processing.is_set():
            try:
                # Get audio from queue with timeout
                try:
                    audio_data = self._output_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                # Apply output filters
                filtered_audio = audio_data
                for filter in self._output_filters:
                    filtered_audio = filter.process(filtered_audio, self.sample_rate)

                # Add back to output queue
                self._output_queue.put(filtered_audio)

            except Exception as e:
                logger.error(f"Error in output processing: {e}")
                time.sleep(0.1)

    def get_status(self) -> Dict[str, Any]:
        """Get device status.

        Returns:
            Dict[str, Any]: Status information
        """
        return {
            "id": self.device_id,
            "initialized": self._initialized,
            "input_enabled": self._input_enabled,
            "output_enabled": self._output_enabled,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "chunk_size": self.chunk_size,
            "input_filters": [f.__class__.__name__ for f in self._input_filters],
            "output_filters": [f.__class__.__name__ for f in self._output_filters],
        }

    def set_input_filters(self, filters: List[AudioFilter]) -> None:
        """Set input audio filters.

        Args:
            filters: List of audio filters
        """
        self._input_filters = filters
        if self._initialized:
            for filter in filters:
                filter.initialize(self.sample_rate, self.channels)

    def set_output_filters(self, filters: List[AudioFilter]) -> None:
        """Set output audio filters.

        Args:
            filters: List of audio filters
        """
        self._output_filters = filters
        if self._initialized:
            for filter in filters:
                filter.initialize(self.sample_rate, self.channels)

    def is_input_enabled(self) -> bool:
        """Check if input is enabled.

        Returns:
            bool: True if input enabled
        """
        return self._input_enabled

    def is_output_enabled(self) -> bool:
        """Check if output is enabled.

        Returns:
            bool: True if output enabled
        """
        return self._output_enabled
