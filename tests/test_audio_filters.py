"""Tests for audio processing filters."""

import pytest
import numpy as np
from unittest.mock import Mock, patch

from rtaspi.processing.audio.filters import (
    AudioFilter,
    NoiseReductionFilter,
    EchoCancellationFilter,
    FeedbackSuppressionFilter,
    GainControlFilter,
)


@pytest.fixture
def test_audio():
    """Create test audio data."""
    # Generate 1 second of audio at 16kHz
    t = np.linspace(0, 1, 16000)
    # Mix sine waves at different frequencies
    audio = (
        0.5 * np.sin(2 * np.pi * 440 * t)  # A4 note
        + 0.3 * np.sin(2 * np.pi * 880 * t)  # A5 note
        + 0.2 * np.random.randn(len(t))  # Noise
    ).astype(np.float32)
    return audio


def test_base_filter():
    """Test base audio filter."""
    filter = AudioFilter()

    # Test initialization
    assert filter.initialize(16000, 1)
    assert filter._initialized
    assert filter._sample_rate == 16000
    assert filter._channels == 1

    # Test processing
    audio = np.random.randn(1000).astype(np.float32)
    output = filter.process(audio)
    np.testing.assert_array_equal(output, audio)  # Base filter should pass through

    # Test sample rate verification
    output = filter.process(audio, 16000)  # Should work
    np.testing.assert_array_equal(output, audio)

    output = filter.process(audio, 44100)  # Should warn but still process
    np.testing.assert_array_equal(output, audio)

    # Test cleanup
    filter.cleanup()
    assert not filter._initialized


def test_noise_reduction_filter(test_audio):
    """Test noise reduction filter."""
    filter = NoiseReductionFilter(frame_size=2048, overlap=0.75)

    # Test initialization
    assert filter.initialize(16000, 1)
    assert filter._window is not None
    assert filter._noise_estimate is not None

    # Test processing
    output = filter.process(test_audio)
    assert output.shape == test_audio.shape
    assert output.dtype == np.float32

    # Verify noise reduction
    input_noise = np.std(test_audio)
    output_noise = np.std(output)
    assert output_noise < input_noise  # Should reduce noise level

    # Test with different frame sizes
    filter = NoiseReductionFilter(frame_size=1024, overlap=0.5)
    assert filter.initialize(16000, 1)
    output = filter.process(test_audio)
    assert output.shape == test_audio.shape


def test_echo_cancellation_filter(test_audio):
    """Test echo cancellation filter."""
    filter = EchoCancellationFilter(filter_length=1024, step_size=0.1)

    # Test initialization
    assert filter.initialize(16000, 1)
    assert filter._filter is not None
    assert filter._buffer is not None
    assert len(filter._filter) == 1024

    # Create echo by delaying and attenuating
    echo_delay = 100
    echo_gain = 0.5
    echo = np.pad(test_audio, (echo_delay, 0))[:-echo_delay] * echo_gain
    input_with_echo = test_audio + echo

    # Test processing
    output = filter.process(input_with_echo)
    assert output.shape == input_with_echo.shape
    assert output.dtype == np.float32

    # Verify echo reduction
    input_echo_level = np.std(input_with_echo)
    output_echo_level = np.std(output)
    assert output_echo_level < input_echo_level  # Should reduce echo level


def test_feedback_suppression_filter(test_audio):
    """Test feedback suppression filter."""
    filter = FeedbackSuppressionFilter(shift_hz=5.0)

    # Test initialization
    assert filter.initialize(16000, 1)
    assert filter._phase_increment > 0

    # Test processing
    output = filter.process(test_audio)
    assert output.shape == test_audio.shape
    assert output.dtype == np.float32

    # Verify frequency shift
    input_fft = np.fft.rfft(test_audio)
    output_fft = np.fft.rfft(output)
    assert not np.allclose(input_fft, output_fft)  # Spectrum should be shifted

    # Test phase continuity
    initial_phase = filter._phase
    filter.process(test_audio)
    assert filter._phase != initial_phase  # Phase should advance
    assert 0 <= filter._phase < 2 * np.pi  # Phase should wrap


def test_gain_control_filter(test_audio):
    """Test automatic gain control filter."""
    filter = GainControlFilter(target_rms=0.1, attack_time=0.01, release_time=0.1)

    # Test initialization
    assert filter.initialize(16000, 1)
    assert 0 < filter._attack_coef < 1
    assert 0 < filter._release_coef < 1

    # Test processing with low input level
    quiet_audio = test_audio * 0.1
    output_quiet = filter.process(quiet_audio)
    assert output_quiet.shape == quiet_audio.shape
    assert output_quiet.dtype == np.float32

    quiet_rms = np.sqrt(np.mean(quiet_audio**2))
    output_quiet_rms = np.sqrt(np.mean(output_quiet**2))
    assert output_quiet_rms > quiet_rms  # Should increase gain

    # Test processing with high input level
    loud_audio = test_audio * 2.0
    output_loud = filter.process(loud_audio)

    loud_rms = np.sqrt(np.mean(loud_audio**2))
    output_loud_rms = np.sqrt(np.mean(output_loud**2))
    assert output_loud_rms < loud_rms  # Should decrease gain


def test_filter_chaining(test_audio):
    """Test chaining multiple filters."""
    filters = [
        NoiseReductionFilter(),
        EchoCancellationFilter(),
        FeedbackSuppressionFilter(),
        GainControlFilter(),
    ]

    # Initialize all filters
    for filter in filters:
        assert filter.initialize(16000, 1)

    # Process through chain
    audio = test_audio.copy()
    for filter in filters:
        audio = filter.process(audio)

    assert audio.shape == test_audio.shape
    assert audio.dtype == np.float32
    assert not np.array_equal(audio, test_audio)  # Should modify audio


def test_filter_error_handling():
    """Test filter error handling."""
    filter = AudioFilter()

    # Test processing without initialization
    audio = np.random.randn(1000).astype(np.float32)
    output = filter.process(audio)
    np.testing.assert_array_equal(output, audio)  # Should pass through

    # Test with invalid input types
    filter.initialize(16000, 1)
    int_audio = np.random.randint(0, 100, 1000)
    output = filter.process(int_audio)
    assert output.dtype == int_audio.dtype  # Should preserve dtype

    # Test cleanup during processing
    filter.cleanup()
    output = filter.process(audio)
    np.testing.assert_array_equal(output, audio)  # Should pass through


def test_filter_parameters():
    """Test filter parameter validation."""
    # Test noise reduction parameters
    nr_filter = NoiseReductionFilter(frame_size=1024, overlap=0.5)
    assert nr_filter.frame_size == 1024
    assert nr_filter.overlap == 0.5

    # Test echo cancellation parameters
    ec_filter = EchoCancellationFilter(filter_length=2048, step_size=0.2)
    assert ec_filter.filter_length == 2048
    assert ec_filter.step_size == 0.2

    # Test feedback suppression parameters
    fb_filter = FeedbackSuppressionFilter(shift_hz=10.0)
    assert fb_filter.shift_hz == 10.0

    # Test gain control parameters
    gc_filter = GainControlFilter(target_rms=0.2, attack_time=0.02, release_time=0.2)
    assert gc_filter.target_rms == 0.2
    assert gc_filter.attack_time == 0.02
    assert gc_filter.release_time == 0.2
