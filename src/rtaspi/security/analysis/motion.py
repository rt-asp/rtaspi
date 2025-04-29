"""Motion behavior analysis."""

import numpy as np
import cv2
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
import time
from dataclasses import dataclass

from .base import BehaviorAnalyzer, DetectionResult, AnomalyResult
from ...core.logging import get_logger

logger = get_logger(__name__)

@dataclass
class TrackingInfo:
    """Object tracking information."""
    track_id: int
    bbox: Tuple[float, float, float, float]  # x, y, width, height (normalized)
    centroid: Tuple[float, float]  # x, y (normalized)
    velocity: Tuple[float, float]  # dx, dy (normalized)
    timestamp: float
    label: str
    confidence: float
    history: List[Tuple[float, float]]  # List of historical centroids

class MotionAnalyzer(BehaviorAnalyzer):
    """Motion behavior analyzer."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize motion analyzer.
        
        Args:
            config: Analyzer configuration
        """
        super().__init__(config)
        
        # Motion detection settings
        self.motion_threshold = config.get('motion_threshold', 25)
        self.min_area = config.get('min_area', 500)
        self.blur_size = config.get('blur_size', (21, 21))
        self.dilate_iterations = config.get('dilate_iterations', 2)
        
        # Object tracking settings
        self.max_disappeared = config.get('max_disappeared', 30)  # Maximum frames before removing track
        self.max_distance = config.get('max_distance', 0.2)  # Maximum normalized distance for track association
        self.track_history = config.get('track_history', 50)  # Number of positions to keep in history
        
        # Behavior analysis settings
        self.velocity_threshold = config.get('velocity_threshold', 0.1)
        self.direction_bins = config.get('direction_bins', 8)
        self.loitering_time = config.get('loitering_time', 10)  # Seconds
        self.crowding_threshold = config.get('crowding_threshold', 5)  # Objects per zone
        
        # State
        self._background_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=16,
            detectShadows=False
        )
        self._tracks: Dict[int, TrackingInfo] = {}
        self._next_track_id = 0
        self._last_frame = None
        self._frame_count = 0

    def initialize(self) -> bool:
        """Initialize analyzer.
        
        Returns:
            bool: True if initialization successful
        """
        try:
            # Reset state
            self._tracks.clear()
            self._next_track_id = 0
            self._frame_count = 0
            return True

        except Exception as e:
            logger.error(f"Error initializing motion analyzer: {e}")
            return False

    def analyze_frame(self, frame: np.ndarray) -> List[DetectionResult]:
        """Analyze video frame.
        
        Args:
            frame: Video frame as numpy array
            
        Returns:
            List[DetectionResult]: Detection results
        """
        try:
            # Convert frame to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, self.blur_size, 0)

            # Detect motion
            mask = self._background_subtractor.apply(gray)
            mask = cv2.dilate(mask, None, iterations=self.dilate_iterations)

            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            detections = []

            # Process each contour
            frame_height, frame_width = frame.shape[:2]
            timestamp = datetime.now()

            for contour in contours:
                if cv2.contourArea(contour) < self.min_area:
                    continue

                # Get bounding box
                x, y, w, h = cv2.boundingRect(contour)
                
                # Normalize coordinates
                bbox = (
                    x / frame_width,
                    y / frame_height,
                    w / frame_width,
                    h / frame_height
                )

                # Create detection result
                detection = DetectionResult(
                    timestamp=timestamp,
                    confidence=1.0,  # Motion detection doesn't provide confidence
                    label='motion',
                    bbox=bbox,
                    metadata={
                        'area': cv2.contourArea(contour),
                        'perimeter': cv2.arcLength(contour, True)
                    }
                )
                detections.append(detection)

            # Update tracking
            self._update_tracks(detections)
            self._frame_count += 1

            return detections

        except Exception as e:
            logger.error(f"Error analyzing frame: {e}")
            return []

    def detect_anomalies(self, detections: List[DetectionResult]) -> List[AnomalyResult]:
        """Detect anomalies in detection results.
        
        Args:
            detections: List of detection results
            
        Returns:
            List[AnomalyResult]: Anomaly detection results
        """
        try:
            anomalies = []
            timestamp = datetime.now()

            # Check for zone-based anomalies
            zone_anomalies = self._check_zone_anomalies()
            anomalies.extend(zone_anomalies)

            # Check for motion pattern anomalies
            pattern_anomalies = self._check_pattern_anomalies()
            anomalies.extend(pattern_anomalies)

            # Check for crowding
            crowding_anomalies = self._check_crowding()
            anomalies.extend(crowding_anomalies)

            # Check for loitering
            loitering_anomalies = self._check_loitering()
            anomalies.extend(loitering_anomalies)

            return anomalies

        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return []

    def _update_tracks(self, detections: List[DetectionResult]) -> None:
        """Update object tracks.
        
        Args:
            detections: New detections
        """
        try:
            # Get centroids from detections
            centroids = []
            for detection in detections:
                if detection.bbox:
                    x, y, w, h = detection.bbox
                    centroids.append((x + w/2, y + h/2))

            # If no existing tracks, create new ones
            if not self._tracks:
                for i, (detection, centroid) in enumerate(zip(detections, centroids)):
                    self._add_track(detection, centroid)
                return

            # If no detections, update disappeared counts
            if not detections:
                for track_id in list(self._tracks.keys()):
                    track = self._tracks[track_id]
                    if time.time() - track.timestamp > self.max_disappeared:
                        del self._tracks[track_id]
                return

            # Match detections to existing tracks
            track_ids = list(self._tracks.keys())
            track_centroids = [self._tracks[track_id].centroid for track_id in track_ids]

            # Calculate distances between all tracks and detections
            distances = np.zeros((len(track_centroids), len(centroids)))
            for i, track_centroid in enumerate(track_centroids):
                for j, detection_centroid in enumerate(centroids):
                    distances[i, j] = np.sqrt(
                        (track_centroid[0] - detection_centroid[0])**2 +
                        (track_centroid[1] - detection_centroid[1])**2
                    )

            # Find best matches
            matched_tracks = set()
            matched_detections = set()

            while True:
                if distances.size == 0:
                    break

                # Find minimum distance
                i, j = np.unravel_index(distances.argmin(), distances.shape)
                distance = distances[i, j]

                # Stop if distance is too large
                if distance > self.max_distance:
                    break

                track_id = track_ids[i]
                if track_id not in matched_tracks and j not in matched_detections:
                    # Update track
                    track = self._tracks[track_id]
                    detection = detections[j]
                    centroid = centroids[j]

                    # Calculate velocity
                    dt = time.time() - track.timestamp
                    if dt > 0:
                        dx = (centroid[0] - track.centroid[0]) / dt
                        dy = (centroid[1] - track.centroid[1]) / dt
                    else:
                        dx, dy = 0, 0

                    # Update track info
                    track.bbox = detection.bbox
                    track.centroid = centroid
                    track.velocity = (dx, dy)
                    track.timestamp = time.time()
                    track.label = detection.label
                    track.confidence = detection.confidence
                    track.history.append(centroid)
                    if len(track.history) > self.track_history:
                        track.history.pop(0)

                    matched_tracks.add(track_id)
                    matched_detections.add(j)

                # Remove matched pair from consideration
                distances[i, :] = float('inf')
                distances[:, j] = float('inf')

            # Add new tracks for unmatched detections
            for i, (detection, centroid) in enumerate(zip(detections, centroids)):
                if i not in matched_detections:
                    self._add_track(detection, centroid)

            # Remove old tracks
            for track_id in list(self._tracks.keys()):
                if track_id not in matched_tracks:
                    track = self._tracks[track_id]
                    if time.time() - track.timestamp > self.max_disappeared:
                        del self._tracks[track_id]

        except Exception as e:
            logger.error(f"Error updating tracks: {e}")

    def _add_track(self, detection: DetectionResult, centroid: Tuple[float, float]) -> None:
        """Add new track.
        
        Args:
            detection: Detection result
            centroid: Object centroid
        """
        self._tracks[self._next_track_id] = TrackingInfo(
            track_id=self._next_track_id,
            bbox=detection.bbox,
            centroid=centroid,
            velocity=(0, 0),
            timestamp=time.time(),
            label=detection.label,
            confidence=detection.confidence,
            history=[centroid]
        )
        self._next_track_id += 1

    def _check_zone_anomalies(self) -> List[AnomalyResult]:
        """Check for zone-based anomalies.
        
        Returns:
            List[AnomalyResult]: Zone anomalies
        """
        anomalies = []
        timestamp = datetime.now()

        for zone_id, zone in self.zones.items():
            # Get objects in zone
            objects_in_zone = []
            for track in self._tracks.values():
                x, y = track.centroid
                if (zone['x'] <= x <= zone['x'] + zone['width'] and
                    zone['y'] <= y <= zone['y'] + zone['height']):
                    objects_in_zone.append(track)

            # Check zone rules
            if zone.get('restricted', False) and objects_in_zone:
                anomalies.append(AnomalyResult(
                    timestamp=timestamp,
                    score=1.0,
                    type='zone_violation',
                    details={
                        'zone_id': zone_id,
                        'object_count': len(objects_in_zone)
                    },
                    related_detections=[DetectionResult(
                        timestamp=timestamp,
                        confidence=track.confidence,
                        label=track.label,
                        bbox=track.bbox
                    ) for track in objects_in_zone]
                ))

        return anomalies

    def _check_pattern_anomalies(self) -> List[AnomalyResult]:
        """Check for motion pattern anomalies.
        
        Returns:
            List[AnomalyResult]: Pattern anomalies
        """
        anomalies = []
        timestamp = datetime.now()

        for track in self._tracks.values():
            # Check velocity
            speed = np.sqrt(track.velocity[0]**2 + track.velocity[1]**2)
            if speed > self.velocity_threshold:
                anomalies.append(AnomalyResult(
                    timestamp=timestamp,
                    score=min(speed / self.velocity_threshold, 1.0),
                    type='rapid_motion',
                    details={
                        'track_id': track.track_id,
                        'speed': speed
                    },
                    related_detections=[DetectionResult(
                        timestamp=timestamp,
                        confidence=track.confidence,
                        label=track.label,
                        bbox=track.bbox
                    )]
                ))

            # Check direction changes
            if len(track.history) >= 3:
                changes = 0
                prev_direction = None
                for i in range(len(track.history) - 2):
                    p1 = track.history[i]
                    p2 = track.history[i + 1]
                    p3 = track.history[i + 2]
                    
                    # Calculate angles
                    angle1 = np.arctan2(p2[1] - p1[1], p2[0] - p1[0])
                    angle2 = np.arctan2(p3[1] - p2[1], p3[0] - p2[0])
                    diff = abs(angle2 - angle1)
                    
                    # Normalize angle difference
                    if diff > np.pi:
                        diff = 2 * np.pi - diff
                    
                    # Check for significant direction change
                    if diff > np.pi / 4:  # 45 degrees
                        changes += 1

                if changes >= 3:  # Multiple direction changes
                    anomalies.append(AnomalyResult(
                        timestamp=timestamp,
                        score=min(changes / 5, 1.0),
                        type='erratic_motion',
                        details={
                            'track_id': track.track_id,
                            'direction_changes': changes
                        },
                        related_detections=[DetectionResult(
                            timestamp=timestamp,
                            confidence=track.confidence,
                            label=track.label,
                            bbox=track.bbox
                        )]
                    ))

        return anomalies

    def _check_crowding(self) -> List[AnomalyResult]:
        """Check for crowding anomalies.
        
        Returns:
            List[AnomalyResult]: Crowding anomalies
        """
        anomalies = []
        timestamp = datetime.now()

        # Check each zone
        for zone_id, zone in self.zones.items():
            if not zone.get('check_crowding', True):
                continue

            # Count objects in zone
            objects_in_zone = []
            for track in self._tracks.values():
                x, y = track.centroid
                if (zone['x'] <= x <= zone['x'] + zone['width'] and
                    zone['y'] <= y <= zone['y'] + zone['height']):
                    objects_in_zone.append(track)

            # Check crowding threshold
            if len(objects_in_zone) > self.crowding_threshold:
                anomalies.append(AnomalyResult(
                    timestamp=timestamp,
                    score=min(len(objects_in_zone) / self.crowding_threshold, 1.0),
                    type='crowding',
                    details={
                        'zone_id': zone_id,
                        'object_count': len(objects_in_zone)
                    },
                    related_detections=[DetectionResult(
                        timestamp=timestamp,
                        confidence=track.confidence,
                        label=track.label,
                        bbox=track.bbox
                    ) for track in objects_in_zone]
                ))

        return anomalies

    def _check_loitering(self) -> List[AnomalyResult]:
        """Check for loitering anomalies.
        
        Returns:
            List[AnomalyResult]: Loitering anomalies
        """
        anomalies = []
        timestamp = datetime.now()

        for track in self._tracks.values():
            duration = time.time() - track.timestamp
            if duration > self.loitering_time:
                # Calculate movement extent
                if len(track.history) >= 2:
                    x_coords = [p[0] for p in track.history]
                    y_coords = [p[1] for p in track.history]
                    movement_area = (max(x_coords) - min(x_coords)) * (max(y_coords) - min(y_coords))
                    
                    # Check if movement is limited
                    if movement_area < 0.01:  # 1% of frame area
                        anomalies.append(AnomalyResult(
                            timestamp=timestamp,
                            score=min(duration / self.loitering_time, 1.0),
                            type='loitering',
                            details={
                                'track_id': track.track_id,
                                'duration': duration,
                                'movement_area': movement_area
                            },
                            related_detections=[DetectionResult(
                                timestamp=timestamp,
                                confidence=track.confidence,
                                label=track.label,
                                bbox=track.bbox
                            )]
                        ))

        return anomalies
