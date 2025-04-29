"""Audio processing filters."""

import logging
import numpy as np
from typing import Optional, List, Dict, Any
import scipy.signal as signal

from ...core.logging import get_logger

logger = get_logger(__name__)


class AudioFilter:
    """Base class for audio filters."""

    def __init__(self):
        """Initialize filter."""
        self._initialized = False
        self._sample_rate = 0
        self._channels = 0

    def initialize(self, sample_rate: int, channels: int) -> bool:
        """Initialize filter.

        Args:
            sample_rate: Audio sample rate in Hz
            channels: Number of audio channels

        Returns:
            bool: True if initialization successful
        """
        self._sample_rate = sample_rate
        self._channels = channels
        self._initialized = True
        return True

    def process(
        self, audio_data: np.ndarray, sample_rate: Optional[int] = None
    ) -> np.ndarray:
        """Process audio data.

        Args:
            audio_data: Audio samples as numpy array
            sample_rate: Sample rate (optional, for verification)

        Returns:
            np.ndarray: Processed audio samples
        """
        if not self._initialized:
            logger.warning("Filter not initialized")
            return audio_data

        if sample_rate is not None and sample_rate != self._sample_rate:
            logger.warning(
                f"Sample rate mismatch: {sample_rate} != {self._sample_rate}"
            )
            return audio_data

        return audio_data

    def cleanup(self) -> None:
        """Clean up filter resources."""
        self._initialized = False


class NoiseReductionFilter(AudioFilter):
    """Noise reduction filter using spectral subtraction."""

    def __init__(self, frame_size: int = 2048, overlap: float = 0.75):
        """Initialize noise reduction filter.

        Args:
            frame_size: FFT frame size
            overlap: Frame overlap ratio
        """
        super().__init__()
        self.frame_size = frame_size
        self.overlap = overlap
        self._noise_estimate = None
        self._window = None

    def initialize(self, sample_rate: int, channels: int) -> bool:
        """Initialize filter.

        Args:
            sample_rate: Audio sample rate in Hz
            channels: Number of audio channels

        Returns:
            bool: True if initialization successful
        """
        if not super().initialize(sample_rate, channels):
            return False

        self._window = signal.windows.hann(self.frame_size)
        self._noise_estimate = np.zeros(self.frame_size // 2 + 1)
        return True

    def process(
        self, audio_data: np.ndarray, sample_rate: Optional[int] = None
    ) -> np.ndarray:
        """Process audio data.

        Args:
            audio_data: Audio samples as numpy array
            sample_rate: Sample rate (optional, for verification)

        Returns:
            np.ndarray: Processed audio samples
        """
        if not super().process(audio_data, sample_rate).any():
            return audio_data

        # Convert to float32 if needed
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)

        # Apply spectral subtraction
        hop_size = int(self.frame_size * (1 - self.overlap))
        num_frames = (len(audio_data) - self.frame_size) // hop_size + 1
        output = np.zeros_like(audio_data)
        window_sum = np.zeros_like(audio_data)

        for i in range(num_frames):
            start = i * hop_size
            end = start + self.frame_size
            frame = audio_data[start:end] * self._window

            # Compute spectrum
            spectrum = np.fft.rfft(frame)
            magnitude = np.abs(spectrum)
            phase = np.angle(spectrum)

            # Update noise estimate
            if i == 0:
                self._noise_estimate = magnitude
            else:
                self._noise_estimate = 0.95 * self._noise_estimate + 0.05 * magnitude

            # Apply spectral subtraction
            magnitude = np.maximum(magnitude - self._noise_estimate, 0)
            spectrum = magnitude * np.exp(1j * phase)

            # Reconstruct frame
            frame = np.fft.irfft(spectrum) * self._window
            output[start:end] += frame
            window_sum[start:end] += self._window

        # Normalize by window sum
        valid_indices = window_sum > 1e-10
        output[valid_indices] /= window_sum[valid_indices]
        return output


class EchoCancellationFilter(AudioFilter):
    """Echo cancellation filter using adaptive filtering."""

    def __init__(self, filter_length: int = 1024, step_size: float = 0.1):
        """Initialize echo cancellation filter.

        Args:
            filter_length: Length of adaptive filter
            step_size: LMS adaptation step size
        """
        super().__init__()
        self.filter_length = filter_length
        self.step_size = step_size
        self._filter = None
        self._buffer = None

    def initialize(self, sample_rate: int, channels: int) -> bool:
        """Initialize filter.

        Args:
            sample_rate: Audio sample rate in Hz
            channels: Number of audio channels

        Returns:
            bool: True if initialization successful
        """
        if not super().initialize(sample_rate, channels):
            return False

        self._filter = np.zeros(self.filter_length)
        self._buffer = np.zeros(self.filter_length)
        return True

    def process(
        self, audio_data: np.ndarray, sample_rate: Optional[int] = None
    ) -> np.ndarray:
        """Process audio data.

        Args:
            audio_data: Audio samples as numpy array
            sample_rate: Sample rate (optional, for verification)

        Returns:
            np.ndarray: Processed audio samples
        """
        if not super().process(audio_data, sample_rate).any():
            return audio_data

        # Convert to float32 if needed
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)

        # Apply adaptive filtering
        output = np.zeros_like(audio_data)
        for i in range(len(audio_data)):
            # Update buffer
            self._buffer = np.roll(self._buffer, 1)
            self._buffer[0] = audio_data[i]

            # Estimate echo
            echo = np.dot(self._filter, self._buffer)

            # Cancel echo
            output[i] = audio_data[i] - echo

            # Update filter
            error = output[i]
            self._filter += self.step_size * error * self._buffer

        return output


class FeedbackSuppressionFilter(AudioFilter):
    """Feedback suppression using frequency shifting."""

    def __init__(self, shift_hz: float = 5.0):
        """Initialize feedback suppression filter.

        Args:
            shift_hz: Frequency shift in Hz
        """
        super().__init__()
        self.shift_hz = shift_hz
        self._phase = 0.0
        self._phase_increment = 0.0

    def initialize(self, sample_rate: int, channels: int) -> bool:
        """Initialize filter.

        Args:
            sample_rate: Audio sample rate in Hz
            channels: Number of audio channels

        Returns:
            bool: True if initialization successful
        """
        if not super().initialize(sample_rate, channels):
            return False

        self._phase_increment = 2 * np.pi * self.shift_hz / sample_rate
        return True

    def process(
        self, audio_data: np.ndarray, sample_rate: Optional[int] = None
    ) -> np.ndarray:
        """Process audio data.

        Args:
            audio_data: Audio samples as numpy array
            sample_rate: Sample rate (optional, for verification)

        Returns:
            np.ndarray: Processed audio samples
        """
        if not super().process(audio_data, sample_rate).any():
            return audio_data

        # Convert to float32 if needed
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)

        # Apply frequency shift
        t = np.arange(len(audio_data))
        phase = self._phase + t * self._phase_increment
        output = audio_data * np.cos(phase)

        # Update phase
        self._phase = (self._phase + len(audio_data) * self._phase_increment) % (
            2 * np.pi
        )

        return output


class NormalizationFilter(AudioFilter):
    """Audio normalization filter."""

    def __init__(self, target_peak: float = 0.9):
        """Initialize normalization filter.

        Args:
            target_peak: Target peak amplitude (0.0 to 1.0)
        """
        super().__init__()
        self.target_peak = target_peak

    def process(
        self, audio_data: np.ndarray, sample_rate: Optional[int] = None
    ) -> np.ndarray:
        """Process audio data.

        Args:
            audio_data: Audio samples as numpy array
            sample_rate: Sample rate (optional, for verification)

        Returns:
            np.ndarray: Processed audio samples
        """
        if not super().process(audio_data, sample_rate).any():
            return audio_data

        # Convert to float32 if needed
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)

        # Calculate peak amplitude
        peak = np.max(np.abs(audio_data))
        if peak < 1e-10:
            return audio_data

        # Apply normalization
        scale = self.target_peak / peak
        return audio_data * scale


class GainControlFilter(AudioFilter):
    """Automatic gain control."""

    def __init__(
        self,
        target_rms: float = 0.1,
        attack_time: float = 0.01,
        release_time: float = 0.1,
    ):
        """Initialize gain control filter.

        Args:
            target_rms: Target RMS level
            attack_time: Attack time in seconds
            release_time: Release time in seconds
        """
        super().__init__()
        self.target_rms = target_rms
        self.attack_time = attack_time
        self.release_time = release_time
        self._current_gain = 1.0
        self._attack_coef = 0.0
        self._release_coef = 0.0

    def initialize(self, sample_rate: int, channels: int) -> bool:
        """Initialize filter.

        Args:
            sample_rate: Audio sample rate in Hz
            channels: Number of audio channels

        Returns:
            bool: True if initialization successful
        """
        if not super().initialize(sample_rate, channels):
            return False

        self._attack_coef = np.exp(-1 / (self.attack_time * sample_rate))
        self._release_coef = np.exp(-1 / (self.release_time * sample_rate))
        return True

    def process(
        self, audio_data: np.ndarray, sample_rate: Optional[int] = None
    ) -> np.ndarray:
        """Process audio data.

        Args:
            audio_data: Audio samples as numpy array
            sample_rate: Sample rate (optional, for verification)

        Returns:
            np.ndarray: Processed audio samples
        """
        if not super().process(audio_data, sample_rate).any():
            return audio_data

        # Convert to float32 if needed
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)

        # Calculate RMS level
        rms = np.sqrt(np.mean(audio_data**2))
        if rms < 1e-10:
            return audio_data

        # Calculate target gain
        target_gain = self.target_rms / rms

        # Apply smoothing
        if target_gain > self._current_gain:
            self._current_gain = (
                self._attack_coef * self._current_gain
                + (1 - self._attack_coef) * target_gain
            )
        else:
            self._current_gain = (
                self._release_coef * self._current_gain
                + (1 - self._release_coef) * target_gain
            )

        # Apply gain
        return audio_data * self._current_gain
