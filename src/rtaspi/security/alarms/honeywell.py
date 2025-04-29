"""Honeywell Total Connect alarm system integration."""

import requests
import json
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import threading

from .base import AlarmSystem, AlarmState, AlarmZone, AlarmEvent
from ...core.logging import get_logger

logger = get_logger(__name__)

# API endpoints
API_BASE = "https://rs.alarmnet.com/TC21API/TC2.asmx"
API_ENDPOINTS = {
    "authenticate": "/AuthenticateUserLogin",
    "get_session_details": "/GetSessionDetails",
    "keep_alive": "/KeepAlive",
    "get_panel_meta_data": "/GetPanelMetaData",
    "get_panel_status": "/GetPanelStatus",
    "get_zone_status": "/GetZonesListInState",
    "arm_panel": "/ArmPanel",
    "disarm_panel": "/DisarmPanel",
    "bypass_zone": "/BypassZone",
    "clear_bypass": "/ClearBypass",
    "get_events": "/GetPanelEvents",
}

# Arm modes
ARM_MODES = {
    "away": 0,  # Away
    "stay": 1,  # Stay
    "night": 2,  # Night Stay
    "instant": 3,  # Instant
    "max": 4,  # Maximum
}


class HoneywellAlarmSystem(AlarmSystem):
    """Honeywell Total Connect alarm system implementation."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize Honeywell alarm system.

        Args:
            config: Alarm system configuration
        """
        super().__init__(config)

        # API settings
        self.username = config.get("username")
        self.password = config.get("password")
        self.application_id = config.get("application_id")
        self.application_version = config.get("application_version", "1.0.0")
        self.location_id = config.get("location_id")
        self.device_id = config.get("device_id")

        # Session settings
        self.session_timeout = config.get("session_timeout", 300)  # 5 minutes
        self.keepalive_interval = config.get("keepalive_interval", 60)

        # State
        self._session_id: Optional[str] = None
        self._session_start: Optional[float] = None
        self._keepalive_thread: Optional[threading.Thread] = None
        self._stop_keepalive = threading.Event()

    def connect(self) -> bool:
        """Connect to Honeywell system.

        Returns:
            bool: True if connection successful
        """
        try:
            # Authenticate
            response = self._api_call(
                "authenticate",
                {
                    "userName": self.username,
                    "password": self.password,
                    "applicationId": self.application_id,
                    "applicationVersion": self.application_version,
                },
            )

            if not response or response.get("resultCode") != 0:
                logger.error(f"Authentication failed: {response.get('resultData')}")
                return False

            # Store session ID
            self._session_id = response["sessionId"]
            self._session_start = time.time()

            # Start keepalive thread
            self._stop_keepalive.clear()
            self._keepalive_thread = threading.Thread(target=self._keepalive_loop)
            self._keepalive_thread.daemon = True
            self._keepalive_thread.start()

            # Get initial state
            if not self._update_state():
                logger.error("Failed to get initial state")
                self.disconnect()
                return False

            self._connected = True
            return True

        except Exception as e:
            logger.error(f"Error connecting to Honeywell system: {e}")
            self.disconnect()
            return False

    def disconnect(self) -> None:
        """Disconnect from Honeywell system."""
        try:
            self._stop_keepalive.set()

            if self._keepalive_thread:
                self._keepalive_thread.join()
                self._keepalive_thread = None

            self._session_id = None
            self._session_start = None
            self._connected = False

        except Exception as e:
            logger.error(f"Error disconnecting from Honeywell system: {e}")

    def arm(self, mode: str = "away") -> bool:
        """Arm the system.

        Args:
            mode: Arming mode (away, stay, night, instant, max)

        Returns:
            bool: True if arming successful
        """
        try:
            if not self._connected:
                return False

            # Validate mode
            if mode not in ARM_MODES:
                logger.error(f"Invalid arm mode: {mode}")
                return False

            # Send arm command
            response = self._api_call(
                "arm_panel",
                {
                    "locationId": self.location_id,
                    "deviceId": self.device_id,
                    "armType": ARM_MODES[mode],
                },
            )

            if not response or response.get("resultCode") != 0:
                logger.error(f"Arming failed: {response.get('resultData')}")
                return False

            # Update state
            return self._update_state()

        except Exception as e:
            logger.error(f"Error arming Honeywell system: {e}")
            return False

    def disarm(self, code: Optional[str] = None) -> bool:
        """Disarm the system.

        Args:
            code: Security code if required

        Returns:
            bool: True if disarming successful
        """
        try:
            if not self._connected:
                return False

            # Send disarm command
            response = self._api_call(
                "disarm_panel",
                {
                    "locationId": self.location_id,
                    "deviceId": self.device_id,
                    "userCode": code or "",
                },
            )

            if not response or response.get("resultCode") != 0:
                logger.error(f"Disarming failed: {response.get('resultData')}")
                return False

            # Update state
            return self._update_state()

        except Exception as e:
            logger.error(f"Error disarming Honeywell system: {e}")
            return False

    def bypass_zone(self, zone_id: str) -> bool:
        """Bypass a zone.

        Args:
            zone_id: Zone identifier

        Returns:
            bool: True if bypass successful
        """
        try:
            if not self._connected:
                return False

            # Send bypass command
            response = self._api_call(
                "bypass_zone",
                {
                    "locationId": self.location_id,
                    "deviceId": self.device_id,
                    "zoneId": zone_id,
                },
            )

            if not response or response.get("resultCode") != 0:
                logger.error(f"Bypass failed: {response.get('resultData')}")
                return False

            # Update state
            return self._update_state()

        except Exception as e:
            logger.error(f"Error bypassing zone: {e}")
            return False

    def unbypass_zone(self, zone_id: str) -> bool:
        """Remove zone bypass.

        Args:
            zone_id: Zone identifier

        Returns:
            bool: True if unbypass successful
        """
        try:
            if not self._connected:
                return False

            # Send clear bypass command
            response = self._api_call(
                "clear_bypass",
                {
                    "locationId": self.location_id,
                    "deviceId": self.device_id,
                    "zoneId": zone_id,
                },
            )

            if not response or response.get("resultCode") != 0:
                logger.error(f"Clear bypass failed: {response.get('resultData')}")
                return False

            # Update state
            return self._update_state()

        except Exception as e:
            logger.error(f"Error unbypassing zone: {e}")
            return False

    def trigger_alarm(self, zone_id: str, trigger_type: str) -> bool:
        """Trigger alarm in zone.

        Args:
            zone_id: Zone identifier
            trigger_type: Type of trigger

        Returns:
            bool: True if trigger successful
        """
        # Not supported by Total Connect API
        return False

    def clear_alarm(self, zone_id: str) -> bool:
        """Clear alarm in zone.

        Args:
            zone_id: Zone identifier

        Returns:
            bool: True if clear successful
        """
        # Not supported by Total Connect API
        return False

    def _api_call(
        self, endpoint: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Make API call to Total Connect.

        Args:
            endpoint: API endpoint name
            data: Request data

        Returns:
            Optional[Dict[str, Any]]: Response data if successful
        """
        try:
            # Add session ID if available
            if self._session_id and endpoint != "authenticate":
                data["sessionId"] = self._session_id

            # Make request
            url = f"{API_BASE}{API_ENDPOINTS[endpoint]}"
            response = requests.post(url, json=data)
            response.raise_for_status()

            # Parse response
            result = response.json()
            if not result:
                return None

            return result

        except Exception as e:
            logger.error(f"API call failed: {e}")
            return None

    def _keepalive_loop(self) -> None:
        """Keepalive loop."""
        while not self._stop_keepalive.is_set():
            try:
                time.sleep(self.keepalive_interval)

                # Check session timeout
                if not self._session_id or not self._session_start:
                    continue

                if time.time() - self._session_start > self.session_timeout:
                    logger.info("Session expired, reconnecting")
                    self.connect()
                    continue

                # Send keepalive
                response = self._api_call("keep_alive", {})
                if not response or response.get("resultCode") != 0:
                    logger.error("Keepalive failed")
                    self._connected = False
                    self.connect()

            except Exception as e:
                logger.error(f"Error in keepalive loop: {e}")

    def _update_state(self) -> bool:
        """Update system state.

        Returns:
            bool: True if update successful
        """
        try:
            # Get panel status
            response = self._api_call(
                "get_panel_status",
                {"locationId": self.location_id, "deviceId": self.device_id},
            )

            if not response or response.get("resultCode") != 0:
                return False

            panel_status = response["panelStatus"]

            # Update state
            self._update_state_from_status(panel_status)

            # Get zone status
            response = self._api_call(
                "get_zone_status",
                {"locationId": self.location_id, "deviceId": self.device_id},
            )

            if not response or response.get("resultCode") != 0:
                return False

            zones = response["zones"]

            # Update zones
            self._update_zones_from_status(zones)

            # Get recent events
            response = self._api_call(
                "get_events",
                {
                    "locationId": self.location_id,
                    "deviceId": self.device_id,
                    "partitionId": -1,  # All partitions
                    "count": 10,
                },
            )

            if not response or response.get("resultCode") != 0:
                return False

            events = response["events"]

            # Update events
            self._update_events_from_status(events)

            return True

        except Exception as e:
            logger.error(f"Error updating state: {e}")
            return False

    def _update_state_from_status(self, status: Dict[str, Any]) -> None:
        """Update state from panel status.

        Args:
            status: Panel status data
        """
        try:
            # Parse armed state
            armed = status.get("armedState", 0) > 0

            # Parse alarm state
            triggered = status.get("alarmState", 0) > 0

            # Get bypassed zones
            bypass_zones = [
                str(zone["id"])
                for zone in status.get("zones", [])
                if zone.get("bypassed")
            ]

            # Create new state
            new_state = AlarmState(
                armed=armed,
                triggered=triggered,
                bypass_zones=bypass_zones,
                last_event=self._state.last_event,
                last_update=datetime.now(),
            )

            # Update state
            self._update_state(new_state)

        except Exception as e:
            logger.error(f"Error updating state from status: {e}")

    def _update_zones_from_status(self, zones: List[Dict[str, Any]]) -> None:
        """Update zones from status.

        Args:
            zones: Zone status data
        """
        try:
            for zone_data in zones:
                try:
                    zone_id = str(zone_data["id"])

                    # Parse zone state
                    state = "normal"
                    if zone_data.get("faulted"):
                        state = "faulted"
                    elif zone_data.get("troubled"):
                        state = "troubled"
                    elif zone_data.get("bypassed"):
                        state = "bypassed"
                    elif zone_data.get("alarmed"):
                        state = "triggered"

                    # Create zone info
                    zone = AlarmZone(
                        zone_id=zone_id,
                        name=zone_data.get("name", f"Zone {zone_id}"),
                        type=zone_data.get("type", "security"),
                        state=state,
                        last_trigger=datetime.now() if state == "triggered" else None,
                        metadata={
                            "partition": zone_data.get("partition"),
                            "can_bypass": zone_data.get("canBypass", False),
                        },
                    )

                    # Update zone
                    self._update_zone(zone)

                except Exception as e:
                    logger.error(f"Error updating zone {zone_data.get('id')}: {e}")

        except Exception as e:
            logger.error(f"Error updating zones from status: {e}")

    def _update_events_from_status(self, events: List[Dict[str, Any]]) -> None:
        """Update events from status.

        Args:
            events: Event data
        """
        try:
            for event_data in events:
                try:
                    # Parse event type
                    event_type = event_data.get("type", "unknown")

                    # Parse severity
                    severity = 0.5
                    if event_type in ["alarm", "panic", "fire"]:
                        severity = 1.0
                    elif event_type in ["trouble", "fault"]:
                        severity = 0.8

                    # Create event
                    event = AlarmEvent(
                        timestamp=datetime.fromtimestamp(event_data.get("time", 0)),
                        type=event_type,
                        zone_id=(
                            str(event_data.get("zoneId"))
                            if event_data.get("zoneId")
                            else None
                        ),
                        details={
                            "partition": event_data.get("partition"),
                            "user": event_data.get("user"),
                            "message": event_data.get("message"),
                        },
                        severity=severity,
                    )

                    # Add event
                    self._add_event(event)

                except Exception as e:
                    logger.error(f"Error updating event: {e}")

        except Exception as e:
            logger.error(f"Error updating events from status: {e}")
