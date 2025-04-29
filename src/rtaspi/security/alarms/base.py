"""Base classes for alarm system integration."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import time
import threading

from ...core.logging import get_logger

logger = get_logger(__name__)

@dataclass
class AlarmState:
    """Alarm system state."""
    armed: bool
    triggered: bool
    bypass_zones: List[str]
    last_event: Optional[Dict[str, Any]]
    last_update: datetime

@dataclass
class AlarmZone:
    """Alarm zone information."""
    zone_id: str
    name: str
    type: str  # e.g., motion, contact, glass_break
    state: str  # e.g., normal, triggered, bypassed, fault
    last_trigger: Optional[datetime]
    metadata: Optional[Dict[str, Any]]

@dataclass
class AlarmEvent:
    """Alarm system event."""
    timestamp: datetime
    type: str
    zone_id: Optional[str]
    details: Optional[Dict[str, Any]]
    severity: float  # 0-1, higher means more severe

class AlarmSystem(ABC):
    """Base class for alarm systems."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize alarm system.
        
        Args:
            config: Alarm system configuration
        """
        self.config = config
        self.system_id = config.get('system_id', 'default')
        self.name = config.get('name', 'Alarm System')
        self.auto_reconnect = config.get('auto_reconnect', True)
        self.reconnect_delay = config.get('reconnect_delay', 30)
        self.event_history_size = config.get('event_history_size', 1000)

        # State
        self._connected = False
        self._state = AlarmState(
            armed=False,
            triggered=False,
            bypass_zones=[],
            last_event=None,
            last_update=datetime.now()
        )
        self._zones: Dict[str, AlarmZone] = {}
        self._events: List[AlarmEvent] = []
        self._event_callbacks: List[callable] = []
        self._state_callbacks: List[callable] = []
        self._reconnect_thread: Optional[threading.Thread] = None
        self._stop_reconnect = threading.Event()

    @abstractmethod
    def connect(self) -> bool:
        """Connect to alarm system.
        
        Returns:
            bool: True if connection successful
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from alarm system."""
        pass

    @abstractmethod
    def arm(self, mode: str = 'away') -> bool:
        """Arm the system.
        
        Args:
            mode: Arming mode (away, stay, night)
            
        Returns:
            bool: True if arming successful
        """
        pass

    @abstractmethod
    def disarm(self, code: Optional[str] = None) -> bool:
        """Disarm the system.
        
        Args:
            code: Security code if required
            
        Returns:
            bool: True if disarming successful
        """
        pass

    @abstractmethod
    def bypass_zone(self, zone_id: str) -> bool:
        """Bypass a zone.
        
        Args:
            zone_id: Zone identifier
            
        Returns:
            bool: True if bypass successful
        """
        pass

    @abstractmethod
    def unbypass_zone(self, zone_id: str) -> bool:
        """Remove zone bypass.
        
        Args:
            zone_id: Zone identifier
            
        Returns:
            bool: True if unbypass successful
        """
        pass

    @abstractmethod
    def trigger_alarm(self, zone_id: str, trigger_type: str) -> bool:
        """Trigger alarm in zone.
        
        Args:
            zone_id: Zone identifier
            trigger_type: Type of trigger
            
        Returns:
            bool: True if trigger successful
        """
        pass

    @abstractmethod
    def clear_alarm(self, zone_id: str) -> bool:
        """Clear alarm in zone.
        
        Args:
            zone_id: Zone identifier
            
        Returns:
            bool: True if clear successful
        """
        pass

    def get_state(self) -> AlarmState:
        """Get current alarm state.
        
        Returns:
            AlarmState: Current state
        """
        return self._state

    def get_zone(self, zone_id: str) -> Optional[AlarmZone]:
        """Get zone information.
        
        Args:
            zone_id: Zone identifier
            
        Returns:
            Optional[AlarmZone]: Zone information if found
        """
        return self._zones.get(zone_id)

    def get_zones(self) -> List[AlarmZone]:
        """Get all zones.
        
        Returns:
            List[AlarmZone]: List of zones
        """
        return list(self._zones.values())

    def get_events(self, count: Optional[int] = None) -> List[AlarmEvent]:
        """Get recent events.
        
        Args:
            count: Maximum number of events to return
            
        Returns:
            List[AlarmEvent]: List of events
        """
        if count:
            return self._events[-count:]
        return self._events

    def add_event_callback(self, callback: callable) -> None:
        """Add event callback.
        
        Args:
            callback: Function to call when event occurs
        """
        self._event_callbacks.append(callback)

    def remove_event_callback(self, callback: callable) -> None:
        """Remove event callback.
        
        Args:
            callback: Callback to remove
        """
        if callback in self._event_callbacks:
            self._event_callbacks.remove(callback)

    def add_state_callback(self, callback: callable) -> None:
        """Add state callback.
        
        Args:
            callback: Function to call when state changes
        """
        self._state_callbacks.append(callback)

    def remove_state_callback(self, callback: callable) -> None:
        """Remove state callback.
        
        Args:
            callback: Callback to remove
        """
        if callback in self._state_callbacks:
            self._state_callbacks.remove(callback)

    def _update_state(self, state: AlarmState) -> None:
        """Update alarm state.
        
        Args:
            state: New state
        """
        self._state = state
        self._state.last_update = datetime.now()
        
        # Notify callbacks
        for callback in self._state_callbacks:
            try:
                callback(self._state)
            except Exception as e:
                logger.error(f"Error in state callback: {e}")

    def _update_zone(self, zone: AlarmZone) -> None:
        """Update zone information.
        
        Args:
            zone: Zone information
        """
        self._zones[zone.zone_id] = zone

    def _add_event(self, event: AlarmEvent) -> None:
        """Add new event.
        
        Args:
            event: Event information
        """
        self._events.append(event)
        if len(self._events) > self.event_history_size:
            self._events = self._events[-self.event_history_size:]
        
        # Update state
        self._state.last_event = {
            'timestamp': event.timestamp,
            'type': event.type,
            'zone_id': event.zone_id,
            'details': event.details,
            'severity': event.severity
        }
        
        # Notify callbacks
        for callback in self._event_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")

    def _start_reconnect(self) -> None:
        """Start reconnection thread."""
        if self.auto_reconnect and not self._reconnect_thread:
            self._stop_reconnect.clear()
            self._reconnect_thread = threading.Thread(target=self._reconnect_loop)
            self._reconnect_thread.daemon = True
            self._reconnect_thread.start()

    def _stop_reconnect(self) -> None:
        """Stop reconnection thread."""
        if self._reconnect_thread:
            self._stop_reconnect.set()
            self._reconnect_thread.join()
            self._reconnect_thread = None

    def _reconnect_loop(self) -> None:
        """Reconnection loop."""
        while not self._stop_reconnect.is_set():
            try:
                if not self._connected:
                    logger.info(f"Attempting to reconnect to {self.name}")
                    if self.connect():
                        logger.info(f"Reconnected to {self.name}")
                    else:
                        logger.error(f"Failed to reconnect to {self.name}")
                time.sleep(self.reconnect_delay)
            except Exception as e:
                logger.error(f"Error in reconnect loop: {e}")
                time.sleep(self.reconnect_delay)

    def get_status(self) -> Dict[str, Any]:
        """Get system status.
        
        Returns:
            Dict[str, Any]: Status information
        """
        return {
            'system_id': self.system_id,
            'name': self.name,
            'connected': self._connected,
            'armed': self._state.armed,
            'triggered': self._state.triggered,
            'bypass_zones': self._state.bypass_zones,
            'last_update': self._state.last_update,
            'zone_count': len(self._zones),
            'event_count': len(self._events)
        }
