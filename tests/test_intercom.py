"""Tests for intercom device."""

import pytest
import numpy as np
import threading
import time
from unittest.mock import Mock, patch, MagicMock

from rtaspi.device_managers.intercom.device import IntercomDevice
from rtaspi.processing.audio.filters import (
    AudioFilter,
    NoiseReductionFilter,
    EchoCancellationFilter,
    FeedbackSuppressionFilter,
    GainControlFilter
)


@pytest.fixture
def device_config():
    """Create test device configuration."""
    return {
        'id': 'test-intercom',
        'sample_rate': 16000,
        'channels': 1,
        'chunk_size': 1024
    }


@pytest.fixture
def device(device_config):
    """Create test intercom device."""
    device = IntercomDevice('test-intercom', device_config)
    device.initialize()
    yield device
    device.cleanup()


def test_device_init(device_config):
    """Test device initialization."""
    device = IntercomDevice('test-intercom', device_config)
    
    # Check initial state
    assert device.device_id == 'test-intercom'
    assert device.sample_rate == 16000
    assert device.channels == 1
    assert device.chunk_size == 1024
    assert not device._initialized
    assert not device._input_enabled
    assert not device._output_enabled
    
    # Check filter initialization
    assert len(device._input_filters) == 4
    assert len(device._output_filters) == 2
    assert isinstance(device._input_filters[0], NoiseReductionFilter)
    assert isinstance(device._input_filters[1], GainControlFilter)
    assert isinstance(device._input_filters[2], EchoCancellationFilter)
    assert isinstance(device._input_filters[3], FeedbackSuppressionFilter)
    assert isinstance(device._output_filters[0], NoiseReductionFilter)
    assert isinstance(device._output_filters[1], GainControlFilter)


def test_device_initialization(device_config):
    """Test device initialization process."""
    device = IntercomDevice('test-intercom', device_config)
    
    # Test successful initialization
    with patch.object(AudioFilter, 'initialize', return_value=True):
        assert device.initialize()
        assert device._initialized

    # Test initialization failure
    device._initialized = False
    with patch.object(AudioFilter, 'initialize', return_value=False):
        assert not device.initialize()
        assert not device._initialized


def test_device_cleanup(device):
    """Test device cleanup."""
    # Start processing
    device.start_input()
    device.start_output()
    assert device._input_thread is not None
    assert device._output_thread is not None

    # Clean up
    device.cleanup()
    assert not device._initialized
    assert not device._input_enabled
    assert not device._output_enabled
    assert device._input_thread is None
    assert device._output_thread is None


def test_audio_input_processing(device):
    """Test audio input processing."""
    # Start input processing
    assert device.start_input()
    assert device._input_enabled
    assert device._input_thread is not None

    # Process test audio
    test_audio = np.random.rand(1024).astype(np.float32)
    device.process_input(test_audio)

    # Wait for processing
    time.sleep(0.1)

    # Check output
    output = device.get_output()
    assert output is not None
    assert output.shape == test_audio.shape

    # Stop input
    device.stop_input()
    assert not device._input_enabled
    assert device._input_thread is None


def test_audio_output_processing(device):
    """Test audio output processing."""
    # Start output processing
    assert device.start_output()
    assert device._output_enabled
    assert device._output_thread is not None

    # Add test audio to output queue
    test_audio = np.random.rand(1024).astype(np.float32)
    device._output_queue.put(test_audio)

    # Wait for processing
    time.sleep(0.1)

    # Get processed output
    output = device.get_output()
    assert output is not None
    assert output.shape == test_audio.shape

    # Stop output
    device.stop_output()
    assert not device._output_enabled
    assert device._output_thread is None


def test_filter_application(device):
    """Test audio filter application."""
    # Mock filters
    mock_filter = Mock()
    mock_filter.initialize.return_value = True
    mock_filter.process.return_value = np.zeros(1024)
    
    # Set filters
    device.set_input_filters([mock_filter])
    device.set_output_filters([mock_filter])
    
    # Start processing
    device.start_input()
    device.start_output()
    
    # Process test audio
    test_audio = np.random.rand(1024).astype(np.float32)
    device.process_input(test_audio)
    
    # Wait for processing
    time.sleep(0.1)
    
    # Verify filter was called
    mock_filter.process.assert_called()


def test_error_handling(device):
    """Test error handling."""
    # Test initialization error
    with patch.object(AudioFilter, 'initialize', side_effect=Exception("Test error")):
        device._initialized = False
        assert not device.initialize()

    # Test input processing error
    device._initialized = True
    device.start_input()
    with patch.object(AudioFilter, 'process', side_effect=Exception("Test error")):
        device.process_input(np.zeros(1024))
        time.sleep(0.1)  # Should log error but not crash

    # Test output processing error
    device.start_output()
    with patch.object(AudioFilter, 'process', side_effect=Exception("Test error")):
        device._output_queue.put(np.zeros(1024))
        time.sleep(0.1)  # Should log error but not crash


def test_device_status(device):
    """Test device status reporting."""
    # Check initial status
    status = device.get_status()
    assert status['id'] == 'test-intercom'
    assert status['initialized']
    assert not status['input_enabled']
    assert not status['output_enabled']
    assert status['sample_rate'] == 16000
    assert status['channels'] == 1
    assert status['chunk_size'] == 1024
    assert len(status['input_filters']) == 4
    assert len(status['output_filters']) == 2

    # Check status after starting
    device.start_input()
    device.start_output()
    status = device.get_status()
    assert status['input_enabled']
    assert status['output_enabled']


def test_concurrent_processing(device):
    """Test concurrent input/output processing."""
    # Start both input and output
    device.start_input()
    device.start_output()

    # Process multiple audio chunks
    for _ in range(5):
        test_audio = np.random.rand(1024).astype(np.float32)
        device.process_input(test_audio)

    # Wait for processing
    time.sleep(0.2)

    # Get all processed outputs
    outputs = []
    while True:
        output = device.get_output()
        if output is None:
            break
        outputs.append(output)

    assert len(outputs) > 0
    for output in outputs:
        assert output.shape == (1024,)


def test_device_restart(device):
    """Test device restart capability."""
    # Start processing
    device.start_input()
    device.start_output()
    assert device._input_enabled
    assert device._output_enabled

    # Stop and restart
    device.stop_input()
    device.stop_output()
    assert not device._input_enabled
    assert not device._output_enabled

    device.start_input()
    device.start_output()
    assert device._input_enabled
    assert device._output_enabled

    # Process audio after restart
    test_audio = np.random.rand(1024).astype(np.float32)
    device.process_input(test_audio)
    time.sleep(0.1)
    assert device.get_output() is not None
