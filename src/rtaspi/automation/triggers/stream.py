"""Stream event trigger."""

from typing import Dict, Any, Optional
from ...core.logging import get_logger
from ..rules import Trigger

logger = get_logger(__name__)

class Trigger(Trigger):
    """Stream event trigger."""

    def __init__(self, trigger_type: str, config: Dict[str, Any]):
        """Initialize stream trigger.
        
        Args:
            trigger_type: Type of trigger
            config: Trigger configuration
        """
        super().__init__(trigger_type, config)
        self.stream_id = config.get('stream_id')
        self.event_type = config.get('event_type')
        self._stream_manager = None

    def initialize(self) -> bool:
        """Initialize trigger.
        
        Returns:
            bool: True if initialization successful
        """
        try:
            # Import stream manager
            from ...device_managers import StreamManager
            self._stream_manager = StreamManager()

            # Subscribe to stream events
            if self.stream_id:
                stream = self._stream_manager.get_stream(self.stream_id)
                if stream:
                    stream.add_event_listener(self._handle_event)
                    return True
                logger.error(f"Stream {self.stream_id} not found")
                return False

            # Subscribe to all stream events
            self._stream_manager.add_event_listener(self._handle_event)
            return True

        except Exception as e:
            logger.error(f"Error initializing stream trigger: {e}")
            return False

    def cleanup(self) -> None:
        """Clean up trigger resources."""
        try:
            if self._stream_manager:
                if self.stream_id:
                    stream = self._stream_manager.get_stream(self.stream_id)
                    if stream:
                        stream.remove_event_listener(self._handle_event)
                else:
                    self._stream_manager.remove_event_listener(self._handle_event)

        except Exception as e:
            logger.error(f"Error cleaning up stream trigger: {e}")

    def _handle_event(self, event: Dict[str, Any]) -> None:
        """Handle stream event.
        
        Args:
            event: Stream event data
        """
        try:
            # Check event type
            if self.event_type and event.get('type') != self.event_type:
                return

            # Check stream ID
            if self.stream_id and event.get('stream_id') != self.stream_id:
                return

            # Add stream info to event
            if self.stream_id and self._stream_manager:
                stream = self._stream_manager.get_stream(self.stream_id)
                if stream:
                    event['stream_info'] = stream.get_info()

            # Fire trigger
            self._fire(event)

        except Exception as e:
            logger.error(f"Error handling stream event: {e}")

    def get_supported_events(self) -> List[str]:
        """Get list of supported event types.
        
        Returns:
            List[str]: List of event types
        """
        return [
            'stream_started',
            'stream_stopped',
            'stream_error',
            'stream_stats',
            'stream_connected',
            'stream_disconnected',
            'stream_reconnecting',
            'stream_quality_changed',
            'stream_bitrate_changed',
            'stream_resolution_changed',
            'stream_framerate_changed',
            'stream_keyframe',
            'stream_buffer_full',
            'stream_buffer_empty',
            'stream_data_received',
            'stream_data_sent'
        ]
