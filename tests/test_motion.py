"""Tests for motion behavior analysis."""

import pytest
import numpy as np
import cv2
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from rtaspi.security.analysis.motion import MotionAnalyzer, TrackingInfo
from rtaspi.security.analysis.base import DetectionResult, AnomalyResult


@pytest.fixture
def motion_config():
    """Create test motion analyzer configuration."""
    return {
        'enabled': True,
        'min_confidence': 0.5,
        'max_history': 100,
        'alert_threshold': 0.8,
        'motion_threshold': 25,
        'min_area': 500,
        'blur_size': (21, 21),
        'dilate_iterations': 2,
        'max_disappeared': 30,
        'max_distance': 0.2,
        'track_history': 50,
        'velocity_threshold': 0.1,
        'direction_bins': 8,
        'loitering_time': 10,
        'crowding_threshold': 5,
        'zones': {
            'entrance': {
                'x': 0.0,
                'y': 0.0,
                'width': 0.3,
                'height': 1.0,
                'restricted': True,
                'check_crowding': True
            },
            'exit': {
                'x': 0.7,
                'y': 0.0,
                'width': 0.3,
                'height': 1.0,
                'restricted': False,
                'check_crowding': True
            }
        }
    }


@pytest.fixture
def analyzer(motion_config):
    """Create test motion analyzer."""
    analyzer = MotionAnalyzer(motion_config)
    analyzer.initialize()
    return analyzer


@pytest.fixture
def mock_frame():
    """Create test video frame."""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    # Draw some motion
    cv2.rectangle(frame, (100, 100), (200, 200), (255, 255, 255), -1)
    return frame


def test_analyzer_init(motion_config):
    """Test analyzer initialization."""
    analyzer = MotionAnalyzer(motion_config)
    
    # Check configuration
    assert analyzer.enabled
    assert analyzer.min_confidence == 0.5
    assert analyzer.max_history == 100
    assert analyzer.alert_threshold == 0.8
    assert analyzer.motion_threshold == 25
    assert analyzer.min_area == 500
    assert analyzer.blur_size == (21, 21)
    assert analyzer.dilate_iterations == 2
    assert analyzer.max_disappeared == 30
    assert analyzer.max_distance == 0.2
    assert analyzer.track_history == 50
    assert analyzer.velocity_threshold == 0.1
    assert analyzer.direction_bins == 8
    assert analyzer.loitering_time == 10
    assert analyzer.crowding_threshold == 5
    assert len(analyzer.zones) == 2
    
    # Check state
    assert not analyzer._initialized
    assert not analyzer._tracks
    assert analyzer._next_track_id == 0
    assert analyzer._frame_count == 0


def test_motion_detection(analyzer, mock_frame):
    """Test motion detection."""
    detections = analyzer.analyze_frame(mock_frame)
    
    # Check detections
    assert len(detections) > 0
    for detection in detections:
        assert isinstance(detection, DetectionResult)
        assert detection.confidence == 1.0
        assert detection.label == 'motion'
        assert detection.bbox is not None
        assert detection.metadata is not None
        assert 'area' in detection.metadata
        assert 'perimeter' in detection.metadata


def test_object_tracking(analyzer):
    """Test object tracking."""
    # Create test detections
    timestamp = datetime.now()
    detections = [
        DetectionResult(
            timestamp=timestamp,
            confidence=1.0,
            label='motion',
            bbox=(0.1, 0.1, 0.1, 0.1)
        ),
        DetectionResult(
            timestamp=timestamp,
            confidence=1.0,
            label='motion',
            bbox=(0.5, 0.5, 0.1, 0.1)
        )
    ]
    
    # Update tracks
    analyzer._update_tracks(detections)
    assert len(analyzer._tracks) == 2
    
    # Check track creation
    for track_id, track in analyzer._tracks.items():
        assert isinstance(track, TrackingInfo)
        assert track.bbox is not None
        assert track.centroid is not None
        assert track.velocity == (0, 0)
        assert track.label == 'motion'
        assert track.confidence == 1.0
        assert len(track.history) == 1
    
    # Update with moved objects
    new_detections = [
        DetectionResult(
            timestamp=timestamp + timedelta(seconds=1),
            confidence=1.0,
            label='motion',
            bbox=(0.15, 0.15, 0.1, 0.1)
        ),
        DetectionResult(
            timestamp=timestamp + timedelta(seconds=1),
            confidence=1.0,
            label='motion',
            bbox=(0.55, 0.55, 0.1, 0.1)
        )
    ]
    
    analyzer._update_tracks(new_detections)
    assert len(analyzer._tracks) == 2
    
    # Check track updates
    for track in analyzer._tracks.values():
        assert len(track.history) == 2
        assert track.velocity != (0, 0)


def test_zone_analysis(analyzer):
    """Test zone-based analysis."""
    # Create object in restricted zone
    timestamp = datetime.now()
    analyzer._tracks[0] = TrackingInfo(
        track_id=0,
        bbox=(0.1, 0.1, 0.1, 0.1),
        centroid=(0.15, 0.5),  # In entrance zone
        velocity=(0, 0),
        timestamp=time.time(),
        label='motion',
        confidence=1.0,
        history=[(0.15, 0.5)]
    )
    
    # Check for anomalies
    anomalies = analyzer._check_zone_anomalies()
    assert len(anomalies) == 1
    anomaly = anomalies[0]
    assert anomaly.type == 'zone_violation'
    assert anomaly.score == 1.0
    assert anomaly.details['zone_id'] == 'entrance'


def test_pattern_analysis(analyzer):
    """Test motion pattern analysis."""
    timestamp = datetime.now()
    
    # Create track with high velocity
    analyzer._tracks[0] = TrackingInfo(
        track_id=0,
        bbox=(0.1, 0.1, 0.1, 0.1),
        centroid=(0.5, 0.5),
        velocity=(0.2, 0.2),  # Above threshold
        timestamp=time.time(),
        label='motion',
        confidence=1.0,
        history=[(0.5, 0.5)]
    )
    
    # Check for anomalies
    anomalies = analyzer._check_pattern_anomalies()
    assert len(anomalies) == 1
    anomaly = anomalies[0]
    assert anomaly.type == 'rapid_motion'
    assert anomaly.score > analyzer.min_confidence
    
    # Create track with erratic motion
    analyzer._tracks[1] = TrackingInfo(
        track_id=1,
        bbox=(0.2, 0.2, 0.1, 0.1),
        centroid=(0.5, 0.5),
        velocity=(0, 0),
        timestamp=time.time(),
        label='motion',
        confidence=1.0,
        history=[
            (0.4, 0.4),
            (0.5, 0.4),
            (0.5, 0.5),
            (0.4, 0.5),
            (0.3, 0.5)
        ]
    )
    
    # Check for anomalies again
    anomalies = analyzer._check_pattern_anomalies()
    assert len(anomalies) == 2  # Both rapid and erratic motion
    assert any(a.type == 'erratic_motion' for a in anomalies)


def test_crowding_detection(analyzer):
    """Test crowding detection."""
    timestamp = datetime.now()
    
    # Create multiple objects in zone
    for i in range(6):  # Above crowding threshold
        analyzer._tracks[i] = TrackingInfo(
            track_id=i,
            bbox=(0.1, 0.1, 0.1, 0.1),
            centroid=(0.15, 0.1 + i * 0.1),  # In entrance zone
            velocity=(0, 0),
            timestamp=time.time(),
            label='motion',
            confidence=1.0,
            history=[(0.15, 0.1 + i * 0.1)]
        )
    
    # Check for anomalies
    anomalies = analyzer._check_crowding()
    assert len(anomalies) == 1
    anomaly = anomalies[0]
    assert anomaly.type == 'crowding'
    assert anomaly.score > analyzer.min_confidence
    assert anomaly.details['object_count'] == 6


def test_loitering_detection(analyzer):
    """Test loitering detection."""
    old_timestamp = time.time() - analyzer.loitering_time - 5
    
    # Create stationary object
    analyzer._tracks[0] = TrackingInfo(
        track_id=0,
        bbox=(0.1, 0.1, 0.1, 0.1),
        centroid=(0.5, 0.5),
        velocity=(0, 0),
        timestamp=old_timestamp,
        label='motion',
        confidence=1.0,
        history=[(0.49, 0.49), (0.5, 0.5)]  # Small movement
    )
    
    # Check for anomalies
    anomalies = analyzer._check_loitering()
    assert len(anomalies) == 1
    anomaly = anomalies[0]
    assert anomaly.type == 'loitering'
    assert anomaly.score > analyzer.min_confidence
    assert anomaly.details['duration'] > analyzer.loitering_time


def test_alert_handling(analyzer):
    """Test alert callbacks."""
    # Create mock callback
    callback = Mock()
    analyzer.add_alert_callback(callback)
    
    # Create anomaly
    anomaly = AnomalyResult(
        timestamp=datetime.now(),
        score=1.0,
        type='test_anomaly',
        details={'test': 'data'}
    )
    
    # Trigger alert
    analyzer._trigger_alert(anomaly)
    callback.assert_called_once_with(anomaly)
    
    # Remove callback
    analyzer.remove_alert_callback(callback)
    analyzer._trigger_alert(anomaly)
    assert callback.call_count == 1  # Not called again


def test_error_handling(analyzer, mock_frame):
    """Test error handling."""
    # Test frame analysis error
    with patch.object(analyzer, '_background_subtractor') as mock_bg:
        mock_bg.apply.side_effect = Exception("Test error")
        detections = analyzer.analyze_frame(mock_frame)
        assert not detections
    
    # Test anomaly detection error
    with patch.object(analyzer, '_check_zone_anomalies') as mock_check:
        mock_check.side_effect = Exception("Test error")
        anomalies = analyzer.detect_anomalies([])
        assert not anomalies
    
    # Test track update error
    with patch.object(analyzer, '_add_track') as mock_add:
        mock_add.side_effect = Exception("Test error")
        analyzer._update_tracks([])  # Should not raise
