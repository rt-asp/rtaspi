"""
Event system for rtaspi-devices.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

class EventSystem:
    """Event system for device-related events."""

    def __init__(self):
        """Initialize the event system."""
        self.handlers: Dict[str, List[Callable]] = {}
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    def on(self, event_type: str, handler: Callable) -> None:
        """
        Register an event handler.

        Args:
            event_type (str): Type of event to handle.
            handler (Callable): Function to call when event occurs.
        """
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
        logger.debug(f"Registered handler for event type: {event_type}")

    def off(self, event_type: str, handler: Callable) -> None:
        """
        Remove an event handler.

        Args:
            event_type (str): Type of event to remove handler from.
            handler (Callable): Handler to remove.
        """
        if event_type in self.handlers:
            try:
                self.handlers[event_type].remove(handler)
                logger.debug(f"Removed handler for event type: {event_type}")
            except ValueError:
                pass

    async def emit(self, event_type: str, data: Any = None) -> None:
        """
        Emit an event.

        Args:
            event_type (str): Type of event to emit.
            data (Any, optional): Event data to pass to handlers.
        """
        if event_type in self.handlers:
            for handler in self.handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event_type, data)
                    else:
                        handler(event_type, data)
                except Exception as e:
                    logger.error(f"Error in event handler: {e}")

    def emit_sync(self, event_type: str, data: Any = None) -> None:
        """
        Emit an event synchronously.

        Args:
            event_type (str): Type of event to emit.
            data (Any, optional): Event data to pass to handlers.
        """
        if self.loop is None:
            self.loop = asyncio.get_event_loop()
        
        if event_type in self.handlers:
            for handler in self.handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        asyncio.run_coroutine_threadsafe(
                            handler(event_type, data), self.loop
                        )
                    else:
                        handler(event_type, data)
                except Exception as e:
                    logger.error(f"Error in event handler: {e}")
