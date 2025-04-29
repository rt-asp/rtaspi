"""Device event trigger."""

from typing import Dict, Any, Optional
from ...core.logging import get_logger
from ..rules import Trigger

logger = get_logger(__name__)


class Trigger(Trigger):
    """Device event trigger."""

    def __init__(self, trigger_type: str, config: Dict[str, Any]):
        """Initialize device trigger.

        Args:
            trigger_type: Type of trigger
            config: Trigger configuration
        """
        super().__init__(trigger_type, config)
        self.device_id = config.get("device_id")
        self.event_type = config.get("event_type")
        self._device_manager = None

    def initialize(self) -> bool:
        """Initialize trigger.

        Returns:
            bool: True if initialization successful
        """
        try:
            # Import device manager
            from ...device_managers import DeviceManager

            self._device_manager = DeviceManager()

            # Subscribe to device events
            if self.device_id:
                device = self._device_manager.get_device(self.device_id)
                if device:
                    device.add_event_listener(self._handle_event)
                    return True
                logger.error(f"Device {self.device_id} not found")
                return False

            # Subscribe to all device events
            self._device_manager.add_event_listener(self._handle_event)
            return True

        except Exception as e:
            logger.error(f"Error initializing device trigger: {e}")
            return False

    def cleanup(self) -> None:
        """Clean up trigger resources."""
        try:
            if self._device_manager:
                if self.device_id:
                    device = self._device_manager.get_device(self.device_id)
                    if device:
                        device.remove_event_listener(self._handle_event)
                else:
                    self._device_manager.remove_event_listener(self._handle_event)

        except Exception as e:
            logger.error(f"Error cleaning up device trigger: {e}")

    def _handle_event(self, event: Dict[str, Any]) -> None:
        """Handle device event.

        Args:
            event: Device event data
        """
        try:
            # Check event type
            if self.event_type and event.get("type") != self.event_type:
                return

            # Check device ID
            if self.device_id and event.get("device_id") != self.device_id:
                return

            # Fire trigger
            self._fire(event)

        except Exception as e:
            logger.error(f"Error handling device event: {e}")
