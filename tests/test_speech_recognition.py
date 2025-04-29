"""Tests for speech recognition module."""

import pytest
import numpy as np
import torch
import threading
import time
from unittest.mock import Mock, patch, MagicMock

from rtaspi.processing.speech.recognition import SpeechRecognizer
from rtaspi.processing.audio.filters import NoiseReductionFilter, NormalizationFilter


@pytest.fixture
def recognizer():
    """Create test speech recognizer."""
    with patch("whisper.load_model") as mock_load:
        # Mock Whisper model
        mock_model = Mock()
        mock_model.transcribe.return_value = {"text": "test transcription"}
        mock_load.return_value = mock_model

        # Create recognizer with mocked model
        recognizer = SpeechRecognizer(model_name="tiny")
        yield recognizer
        recognizer.cleanup()


def test_recognizer_init():
    """Test recognizer initialization."""
    with patch("whisper.load_model") as mock_load:
        # Test CPU initialization
        with patch("torch.cuda.is_available", return_value=False):
            recognizer = SpeechRecognizer(model_name="tiny")
            assert recognizer.device == "cpu"
            assert recognizer.model_name == "tiny"
            assert recognizer.language is None
            assert len(recognizer.filters) == 2
            assert isinstance(recognizer.filters[0], NoiseReductionFilter)
            assert isinstance(recognizer.filters[1], NormalizationFilter)

        # Test CUDA initialization
        with patch("torch.cuda.is_available", return_value=True):
            recognizer = SpeechRecognizer(model_name="tiny")
            assert recognizer.device == "cuda"

        # Test custom filters
        custom_filter = Mock()
        recognizer = SpeechRecognizer(model_name="tiny", filters=[custom_filter])
        assert len(recognizer.filters) == 1
        assert recognizer.filters[0] is custom_filter


def test_recognizer_start_stop(recognizer):
    """Test recognition thread management."""
    # Start recognition
    recognizer.start()
    assert recognizer._recognition_thread is not None
    assert recognizer._recognition_thread.is_alive()
    assert not recognizer._stop_recognition.is_set()

    # Try to start again
    recognizer.start()  # Should log warning but not crash

    # Stop recognition
    recognizer.stop()
    assert not recognizer._recognition_thread.is_alive()
    assert recognizer._stop_recognition.is_set()


def test_recognizer_process_audio(recognizer):
    """Test audio processing."""
    # Create test audio data
    audio_data = np.random.rand(16000).astype(np.float32)  # 1 second at 16kHz
    sample_rate = 16000

    # Mock filters
    mock_filter = Mock()
    mock_filter.process.return_value = audio_data
    recognizer.filters = [mock_filter]

    # Process audio
    recognizer.process_audio(audio_data, sample_rate)

    # Verify filter was called
    mock_filter.process.assert_called_once_with(audio_data, sample_rate)

    # Verify data was added to queue
    queued_data, queued_rate = recognizer._audio_queue.get_nowait()
    np.testing.assert_array_equal(queued_data, audio_data)
    assert queued_rate == sample_rate


def test_recognizer_transcription_callback(recognizer):
    """Test transcription callback."""
    # Set up callback
    callback = Mock()
    recognizer.set_on_transcription(callback)

    # Start recognition
    recognizer.start()

    # Process some audio
    audio_data = np.random.rand(16000).astype(np.float32)
    recognizer.process_audio(audio_data, 16000)

    # Wait for processing
    time.sleep(0.5)

    # Verify callback was called
    callback.assert_called_once_with("test transcription")

    # Clean up
    recognizer.stop()


def test_recognizer_error_callback(recognizer):
    """Test error callback."""
    # Set up callback
    callback = Mock()
    recognizer.set_on_error(callback)

    # Simulate error in filter
    mock_filter = Mock()
    mock_filter.process.side_effect = Exception("Test error")
    recognizer.filters = [mock_filter]

    # Process audio
    audio_data = np.random.rand(16000).astype(np.float32)
    recognizer.process_audio(audio_data, 16000)

    # Verify callback was called
    callback.assert_called_once()
    assert isinstance(callback.call_args[0][0], Exception)


def test_recognizer_language_handling(recognizer):
    """Test language handling."""
    # Test setting language
    recognizer.set_language("en")
    assert recognizer.language == "en"

    # Test auto-detect
    recognizer.set_language(None)
    assert recognizer.language is None

    # Test getting available languages
    with patch("whisper.tokenizer.LANGUAGES", {"en": "English", "de": "German"}):
        languages = recognizer.get_available_languages()
        assert "en" in languages
        assert "de" in languages


def test_recognizer_model_info(recognizer):
    """Test model info retrieval."""
    info = recognizer.get_model_info()
    assert info["name"] == "tiny"
    assert info["language"] == "auto"
    assert info["device"] == recognizer.device
    assert len(info["filters"]) == 2
    assert "NoiseReductionFilter" in info["filters"]
    assert "NormalizationFilter" in info["filters"]


def test_recognizer_cleanup(recognizer):
    """Test cleanup."""
    # Start recognition
    recognizer.start()
    assert recognizer._recognition_thread is not None

    # Clean up
    recognizer.cleanup()
    assert not recognizer._recognition_thread.is_alive()
    assert recognizer._stop_recognition.is_set()


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
def test_recognizer_cuda():
    """Test CUDA support."""
    with patch("whisper.load_model") as mock_load:
        recognizer = SpeechRecognizer(model_name="tiny")
        assert recognizer.device == "cuda"
        # Verify model was moved to CUDA
        mock_load.return_value.to.assert_called_once_with("cuda")


def test_recognizer_recognition_loop(recognizer):
    """Test recognition loop error handling."""
    # Mock model to raise error
    recognizer.model.transcribe.side_effect = Exception("Test error")

    # Set up error callback
    callback = Mock()
    recognizer.set_on_error(callback)

    # Start recognition
    recognizer.start()

    # Process audio
    audio_data = np.random.rand(16000).astype(np.float32)
    recognizer.process_audio(audio_data, 16000)

    # Wait for error
    time.sleep(0.5)

    # Verify error callback
    callback.assert_called_once()
    assert isinstance(callback.call_args[0][0], Exception)

    # Clean up
    recognizer.stop()
