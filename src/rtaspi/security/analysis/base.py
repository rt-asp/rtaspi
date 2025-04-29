"""Base classes for security analysis."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
import time
import numpy as np
from dataclasses import dataclass
from datetime import datetime

from ...core.logging import get_logger

logger = get_logger(__name__)

@dataclass
class DetectionResult:
    """Detection result data."""
    timestamp: datetime
    confidence: float
    label: str
    bbox: Optional[Tuple[float, float, float, float]] = None  # x, y, width, height (normalized)
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class AnomalyResult:
    """Anomaly detection result data."""
    timestamp: datetime
    score: float  # 0-1, higher means more anomalous
    type: str
    details: Optional[Dict[str, Any]] = None
    related_detections: Optional[List[DetectionResult]] = None

class SecurityAnalyzer(ABC):
    """Base class for security analyzers."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize analyzer.
        
        Args:
            config: Analyzer configuration
        """
        self.config = config
        self.enabled = config.get('enabled', True)
        self.min_confidence = config.get('min_confidence', 0.5)
        self.max_history = config.get('max_history', 1000)
        self.alert_threshold = config.get('alert_threshold', 0.8)

        # State
        self._initialized = False
        self._history: List[Any] = []
        self._last_update = time.time()
        self._alert_callbacks: List[callable] = []

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize analyzer.
        
        Returns:
            bool: True if initialization successful
        """
        pass

    @abstractmethod
    def analyze_frame(self, frame: np.ndarray) -> List[DetectionResult]:
        """Analyze video frame.
        
        Args:
            frame: Video frame as numpy array
            
        Returns:
            List[DetectionResult]: Detection results
        """
        pass

    @abstractmethod
    def detect_anomalies(self, detections: List[DetectionResult]) -> List[AnomalyResult]:
        """Detect anomalies in detection results.
        
        Args:
            detections: List of detection results
            
        Returns:
            List[AnomalyResult]: Anomaly detection results
        """
        pass

    def update(self, frame: np.ndarray) -> Tuple[List[DetectionResult], List[AnomalyResult]]:
        """Update analyzer with new frame.
        
        Args:
            frame: Video frame as numpy array
            
        Returns:
            Tuple[List[DetectionResult], List[AnomalyResult]]: Detection and anomaly results
        """
        if not self.enabled:
            return [], []

        if not self._initialized:
            if not self.initialize():
                logger.error("Failed to initialize analyzer")
                return [], []
            self._initialized = True

        try:
            # Analyze frame
            detections = self.analyze_frame(frame)
            detections = [d for d in detections if d.confidence >= self.min_confidence]

            # Update history
            self._history.extend(detections)
            if len(self._history) > self.max_history:
                self._history = self._history[-self.max_history:]

            # Detect anomalies
            anomalies = self.detect_anomalies(detections)

            # Check for alerts
            for anomaly in anomalies:
                if anomaly.score >= self.alert_threshold:
                    self._trigger_alert(anomaly)

            self._last_update = time.time()
            return detections, anomalies

        except Exception as e:
            logger.error(f"Error in analyzer update: {e}")
            return [], []

    def add_alert_callback(self, callback: callable) -> None:
        """Add alert callback.
        
        Args:
            callback: Function to call when alert triggered
        """
        self._alert_callbacks.append(callback)

    def remove_alert_callback(self, callback: callable) -> None:
        """Remove alert callback.
        
        Args:
            callback: Callback to remove
        """
        if callback in self._alert_callbacks:
            self._alert_callbacks.remove(callback)

    def _trigger_alert(self, anomaly: AnomalyResult) -> None:
        """Trigger alert callbacks.
        
        Args:
            anomaly: Anomaly that triggered alert
        """
        for callback in self._alert_callbacks:
            try:
                callback(anomaly)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get analyzer status.
        
        Returns:
            Dict[str, Any]: Status information
        """
        return {
            'enabled': self.enabled,
            'initialized': self._initialized,
            'history_size': len(self._history),
            'last_update': self._last_update,
            'min_confidence': self.min_confidence,
            'alert_threshold': self.alert_threshold
        }

    def reset(self) -> None:
        """Reset analyzer state."""
        self._history.clear()
        self._last_update = time.time()


class BehaviorAnalyzer(SecurityAnalyzer):
    """Base class for behavior analyzers."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize behavior analyzer.
        
        Args:
            config: Analyzer configuration
        """
        super().__init__(config)
        self.behavior_types = config.get('behavior_types', ['motion', 'presence', 'interaction'])
        self.zones = config.get('zones', {})  # Defined areas of interest
        self.time_window = config.get('time_window', 60)  # Analysis window in seconds
        self.baseline_period = config.get('baseline_period', 3600)  # Period for learning normal behavior

        # Behavior tracking
        self._behaviors: Dict[str, List[Any]] = {t: [] for t in self.behavior_types}
        self._baseline: Dict[str, Any] = {}

    def update_zones(self, zones: Dict[str, Any]) -> None:
        """Update analysis zones.
        
        Args:
            zones: Zone definitions
        """
        self.zones = zones

    def learn_baseline(self, behaviors: Dict[str, List[Any]]) -> None:
        """Learn baseline behavior patterns.
        
        Args:
            behaviors: Historical behavior data
        """
        try:
            for behavior_type, data in behaviors.items():
                if behavior_type not in self._behaviors:
                    continue

                # Calculate baseline statistics
                if data:
                    self._baseline[behavior_type] = {
                        'mean': np.mean(data),
                        'std': np.std(data),
                        'min': np.min(data),
                        'max': np.max(data),
                        'count': len(data)
                    }

        except Exception as e:
            logger.error(f"Error learning baseline: {e}")

    def check_anomaly(self, behavior_type: str, value: float) -> Optional[float]:
        """Check if behavior value is anomalous.
        
        Args:
            behavior_type: Type of behavior
            value: Behavior value
            
        Returns:
            Optional[float]: Anomaly score if anomalous
        """
        try:
            baseline = self._baseline.get(behavior_type)
            if not baseline:
                return None

            # Calculate z-score
            z_score = abs(value - baseline['mean']) / baseline['std'] if baseline['std'] > 0 else 0

            # Convert to anomaly score (0-1)
            score = 1 - (1 / (1 + z_score))
            return score if score >= self.min_confidence else None

        except Exception as e:
            logger.error(f"Error checking anomaly: {e}")
            return None

    def get_behavior_stats(self) -> Dict[str, Any]:
        """Get behavior statistics.
        
        Returns:
            Dict[str, Any]: Statistics by behavior type
        """
        stats = {}
        for behavior_type in self.behavior_types:
            behaviors = self._behaviors[behavior_type]
            if behaviors:
                stats[behavior_type] = {
                    'current': behaviors[-1],
                    'mean': np.mean(behaviors),
                    'std': np.std(behaviors),
                    'min': np.min(behaviors),
                    'max': np.max(behaviors),
                    'count': len(behaviors)
                }
        return stats

    def cleanup_old_data(self) -> None:
        """Remove data outside time window."""
        cutoff = time.time() - self.time_window
        for behavior_type in self.behavior_types:
            self._behaviors[behavior_type] = [
                b for b in self._behaviors[behavior_type]
                if b.get('timestamp', 0) >= cutoff
            ]
