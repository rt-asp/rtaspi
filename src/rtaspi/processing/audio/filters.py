"""
Audio filter implementations.

This module provides audio filter implementations using numpy and scipy, including:
- Basic filters (equalizer, noise gate, etc.)
- Effects (reverb, echo, etc.)
- Audio adjustments (pitch, time stretch, etc.)
"""

import numpy as np
from typing import Optional, Dict, Any
from scipy import signal
from scipy.io import wavfile


class AudioFilter:
    """Base class for audio filters."""

    def __init__(self, filter_type: str, params: Optional[Dict[str, Any]] = None):
        """Initialize the audio filter.

        Args:
            filter_type: Type of filter to apply
            params: Filter-specific parameters
        """
        self.filter_type = filter_type
        self.params = params or {}

    def apply(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply the filter to an audio signal.

        Args:
            audio: Input audio signal
            sample_rate: Audio sample rate in Hz

        Returns:
            Processed audio signal
        """
        if self.filter_type == "EQUALIZER":
            return self._apply_equalizer(audio, sample_rate)
        elif self.filter_type == "NOISE_GATE":
            return self._apply_noise_gate(audio)
        elif self.filter_type == "COMPRESSOR":
            return self._apply_compressor(audio)
        elif self.filter_type == "REVERB":
            return self._apply_reverb(audio, sample_rate)
        elif self.filter_type == "ECHO":
            return self._apply_echo(audio, sample_rate)
        elif self.filter_type == "PITCH_SHIFT":
            return self._apply_pitch_shift(audio, sample_rate)
        elif self.filter_type == "TIME_STRETCH":
            return self._apply_time_stretch(audio)
        elif self.filter_type == "NORMALIZATION":
            return self._apply_normalization(audio)
        elif self.filter_type == "BANDPASS":
            return self._apply_bandpass(audio, sample_rate)
        elif self.filter_type == "LOWPASS":
            return self._apply_lowpass(audio, sample_rate)
        elif self.filter_type == "HIGHPASS":
            return self._apply_highpass(audio, sample_rate)
        else:
            raise ValueError(f"Unsupported filter type: {self.filter_type}")

    def _apply_equalizer(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply equalizer filter.

        Args:
            audio: Input audio signal
            sample_rate: Audio sample rate in Hz

        Returns:
            Equalized audio signal
        """
        # Get parameters
        bands = self.params.get(
            "bands",
            {
                "60": 0,  # Sub bass
                "170": 0,  # Bass
                "310": 0,  # Low midrange
                "600": 0,  # Midrange
                "1000": 0,  # Higher midrange
                "3000": 0,  # Presence
                "6000": 0,  # Brilliance
                "12000": 0,  # Air
            },
        )

        # Apply each band
        output = np.zeros_like(audio)
        for freq, gain in bands.items():
            freq = float(freq)

            # Create bandpass filter
            nyquist = sample_rate / 2
            low = freq / 1.5
            high = freq * 1.5
            b, a = signal.butter(2, [low / nyquist, high / nyquist], btype="band")

            # Apply filter and adjust gain
            filtered = signal.filtfilt(b, a, audio)
            output += filtered * (10 ** (gain / 20))

        return output

    def _apply_noise_gate(self, audio: np.ndarray) -> np.ndarray:
        """Apply noise gate filter.

        Args:
            audio: Input audio signal

        Returns:
            Noise-gated audio signal
        """
        # Get parameters
        threshold = self.params.get("threshold", -50)  # dB
        ratio = self.params.get("ratio", 10)
        attack = self.params.get("attack", 0.01)
        release = self.params.get("release", 0.1)

        # Convert threshold to linear
        threshold_linear = 10 ** (threshold / 20)

        # Calculate envelope
        abs_audio = np.abs(audio)
        envelope = np.zeros_like(audio)
        for i in range(1, len(audio)):
            if abs_audio[i] > envelope[i - 1]:
                envelope[i] = envelope[i - 1] + attack * (
                    abs_audio[i] - envelope[i - 1]
                )
            else:
                envelope[i] = envelope[i - 1] + release * (
                    abs_audio[i] - envelope[i - 1]
                )

        # Apply gate
        gain = np.ones_like(audio)
        mask = envelope < threshold_linear
        gain[mask] = (envelope[mask] / threshold_linear) ** ratio

        return audio * gain

    def _apply_compressor(self, audio: np.ndarray) -> np.ndarray:
        """Apply compressor filter.

        Args:
            audio: Input audio signal

        Returns:
            Compressed audio signal
        """
        # Get parameters
        threshold = self.params.get("threshold", -20)  # dB
        ratio = self.params.get("ratio", 4)
        attack = self.params.get("attack", 0.01)
        release = self.params.get("release", 0.1)

        # Convert threshold to linear
        threshold_linear = 10 ** (threshold / 20)

        # Calculate envelope
        abs_audio = np.abs(audio)
        envelope = np.zeros_like(audio)
        for i in range(1, len(audio)):
            if abs_audio[i] > envelope[i - 1]:
                envelope[i] = envelope[i - 1] + attack * (
                    abs_audio[i] - envelope[i - 1]
                )
            else:
                envelope[i] = envelope[i - 1] + release * (
                    abs_audio[i] - envelope[i - 1]
                )

        # Apply compression
        gain = np.ones_like(audio)
        mask = envelope > threshold_linear
        gain[mask] = (threshold_linear / envelope[mask]) ** (1 - 1 / ratio)

        return audio * gain

    def _apply_reverb(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply reverb filter.

        Args:
            audio: Input audio signal
            sample_rate: Audio sample rate in Hz

        Returns:
            Reverberated audio signal
        """
        # Get parameters
        room_size = self.params.get("room_size", 0.5)  # 0.0 to 1.0
        damping = self.params.get("damping", 0.5)  # 0.0 to 1.0
        wet_level = self.params.get("wet_level", 0.3)  # 0.0 to 1.0
        dry_level = self.params.get("dry_level", 0.7)  # 0.0 to 1.0

        # Calculate delay times
        delays = [int(sample_rate * t) for t in [0.0297, 0.0371, 0.0411, 0.0437]]

        # Create feedback matrix
        size = len(delays)
        feedback = np.zeros((size, size))
        for i in range(size):
            for j in range(size):
                feedback[i, j] = (-1 if (i + j) % 2 else 1) * room_size * damping

        # Apply reverb
        output = np.zeros_like(audio)
        state = np.zeros((size, max(delays)))

        for i in range(len(audio)):
            # Get delayed samples
            delayed = np.array(
                [state[j, (i - delays[j]) % len(state[j])] for j in range(size)]
            )

            # Calculate feedback
            feedback_signal = feedback.dot(delayed)

            # Update state
            for j in range(size):
                state[j, i % len(state[j])] = audio[i] + feedback_signal[j]

            # Mix wet and dry signals
            output[i] = dry_level * audio[i] + wet_level * np.mean(delayed)

        return output

    def _apply_echo(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply echo filter.

        Args:
            audio: Input audio signal
            sample_rate: Audio sample rate in Hz

        Returns:
            Echo-processed audio signal
        """
        # Get parameters
        delay = self.params.get("delay", 0.3)  # seconds
        decay = self.params.get("decay", 0.5)  # 0.0 to 1.0
        count = self.params.get("count", 3)  # number of echoes

        # Calculate delay samples
        delay_samples = int(delay * sample_rate)

        # Apply echoes
        output = audio.copy()
        for i in range(1, count + 1):
            # Shift and attenuate
            echo = np.zeros_like(audio)
            echo[i * delay_samples :] = audio[: -i * delay_samples] * (decay**i)
            output += echo

        return output

    def _apply_pitch_shift(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply pitch shift filter.

        Args:
            audio: Input audio signal
            sample_rate: Audio sample rate in Hz

        Returns:
            Pitch-shifted audio signal
        """
        # Get parameters
        semitones = self.params.get("semitones", 0)

        if semitones == 0:
            return audio

        # Calculate pitch shift factor
        factor = 2 ** (semitones / 12)

        # Resample audio
        output_length = int(len(audio) / factor)
        time_orig = np.arange(len(audio))
        time_new = np.linspace(0, len(audio) - 1, output_length)

        return np.interp(time_new, time_orig, audio)

    def _apply_time_stretch(self, audio: np.ndarray) -> np.ndarray:
        """Apply time stretch filter.

        Args:
            audio: Input audio signal

        Returns:
            Time-stretched audio signal
        """
        # Get parameters
        factor = self.params.get("factor", 1.0)

        if factor == 1.0:
            return audio

        # Calculate new length
        output_length = int(len(audio) * factor)

        # Resample audio
        time_orig = np.arange(len(audio))
        time_new = np.linspace(0, len(audio) - 1, output_length)

        return np.interp(time_new, time_orig, audio)

    def _apply_normalization(self, audio: np.ndarray) -> np.ndarray:
        """Apply normalization filter.

        Args:
            audio: Input audio signal

        Returns:
            Normalized audio signal
        """
        # Get parameters
        target_db = self.params.get("target_db", -1)  # dB

        # Calculate current peak
        peak = np.max(np.abs(audio))
        if peak == 0:
            return audio

        # Calculate target amplitude
        target_amplitude = 10 ** (target_db / 20)

        return audio * (target_amplitude / peak)

    def _apply_bandpass(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply bandpass filter.

        Args:
            audio: Input audio signal
            sample_rate: Audio sample rate in Hz

        Returns:
            Bandpass-filtered audio signal
        """
        # Get parameters
        low_freq = self.params.get("low_freq", 500)
        high_freq = self.params.get("high_freq", 2000)
        order = self.params.get("order", 4)

        # Create bandpass filter
        nyquist = sample_rate / 2
        low = low_freq / nyquist
        high = high_freq / nyquist
        b, a = signal.butter(order, [low, high], btype="band")

        # Apply filter
        return signal.filtfilt(b, a, audio)

    def _apply_lowpass(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply lowpass filter.

        Args:
            audio: Input audio signal
            sample_rate: Audio sample rate in Hz

        Returns:
            Lowpass-filtered audio signal
        """
        # Get parameters
        cutoff = self.params.get("cutoff", 1000)
        order = self.params.get("order", 4)

        # Create lowpass filter
        nyquist = sample_rate / 2
        normal_cutoff = cutoff / nyquist
        b, a = signal.butter(order, normal_cutoff, btype="low")

        # Apply filter
        return signal.filtfilt(b, a, audio)

    def _apply_highpass(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply highpass filter.

        Args:
            audio: Input audio signal
            sample_rate: Audio sample rate in Hz

        Returns:
            Highpass-filtered audio signal
        """
        # Get parameters
        cutoff = self.params.get("cutoff", 1000)
        order = self.params.get("order", 4)

        # Create highpass filter
        nyquist = sample_rate / 2
        normal_cutoff = cutoff / nyquist
        b, a = signal.butter(order, normal_cutoff, btype="high")

        # Apply filter
        return signal.filtfilt(b, a, audio)
