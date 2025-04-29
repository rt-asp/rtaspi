"""DSC PowerSeries alarm system integration."""

import socket
import time
import threading
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import re

from .base import AlarmSystem, AlarmState, AlarmZone, AlarmEvent
from ...core.logging import get_logger

logger = get_logger(__name__)

# DSC command codes
DSC_COMMANDS = {
    'poll': '000',
    'status_report': '001',
    'labels_request': '002',
    'arm_away': '030',
    'arm_stay': '031',
    'arm_zero_entry': '032',
    'disarm': '040',
    'trigger_panic': '060',
    'time_stamp': '550',
    'time_date_broadcast': '580',
    'code_send': '200'
}

# DSC response codes
DSC_RESPONSES = {
    '500': 'command_acknowledge',
    '501': 'command_error',
    '502': 'system_error',
    '505': 'login_interaction',
    '510': 'keypad_led_state',
    '511': 'keypad_led_flash_state',
    '550': 'time_date_broadcast',
    '560': 'ring_detected',
    '561': 'indoor_temperature',
    '562': 'outdoor_temperature',
    '601': 'zone_alarm',
    '602': 'zone_alarm_restore',
    '603': 'zone_tamper',
    '604': 'zone_tamper_restore',
    '605': 'zone_fault',
    '606': 'zone_fault_restore',
    '609': 'zone_open',
    '610': 'zone_restored',
    '615': 'envisalink_zone_timer_dump',
    '620': 'duress_alarm',
    '621': 'fire_key_alarm',
    '622': 'fire_key_restore',
    '623': 'auxiliary_key_alarm',
    '624': 'auxiliary_key_restore',
    '625': 'panic_key_alarm',
    '626': 'panic_key_restore',
    '631': 'smoke_alarm',
    '632': 'smoke_alarm_restore',
    '650': 'partition_ready',
    '651': 'partition_not_ready',
    '652': 'partition_armed',
    '653': 'partition_ready_force_arm',
    '654': 'partition_in_alarm',
    '655': 'partition_disarmed',
    '656': 'exit_delay',
    '657': 'entry_delay',
    '658': 'keypad_lock',
    '659': 'keypad_unlock',
    '660': 'partition_failed_to_arm',
    '663': 'chime_enabled',
    '664': 'chime_disabled',
    '670': 'invalid_code',
    '671': 'function_not_available',
    '672': 'failure_to_arm',
    '673': 'partition_busy',
    '674': 'system_arming',
    '680': 'system_in_installers_mode',
    '700': 'partition_armed_with_user',
    '701': 'partition_disarmed_with_user',
    '702': 'partition_armed_with_master',
    '750': 'command_output_pressed',
    '751': 'command_output_released',
    '800': 'panel_battery_trouble',
    '801': 'panel_battery_restored',
    '802': 'panel_ac_trouble',
    '803': 'panel_ac_restored',
    '806': 'system_bell_trouble',
    '807': 'system_bell_restored',
    '810': 'tlm_line_1_trouble',
    '811': 'tlm_line_1_restored',
    '812': 'tlm_line_2_trouble',
    '813': 'tlm_line_2_restored',
    '814': 'fts_buffer_nearly_full',
    '816': 'periodic_test_transmission',
    '821': 'rf_delinquency_trouble',
    '822': 'rf_delinquency_restored',
    '829': 'general_system_tamper',
    '830': 'general_system_tamper_restored',
    '840': 'trouble_led_on',
    '841': 'trouble_led_off',
    '842': 'fire_trouble_alarm',
    '843': 'fire_trouble_restored',
    '849': 'verbose_trouble_status',
    '900': 'code_required',
    '912': 'command_output_pressed_partition',
    '921': 'master_code_required',
    '922': 'installers_code_required'
}

class DSCAlarmSystem(AlarmSystem):
    """DSC PowerSeries alarm system implementation."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize DSC alarm system.
        
        Args:
            config: Alarm system configuration
        """
        super().__init__(config)
        
        # Connection settings
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 4025)
        self.password = config.get('password')
        self.user_code = config.get('user_code')
        self.partition = config.get('partition', 1)
        
        # Socket settings
        self.socket_timeout = config.get('socket_timeout', 10)
        self.keepalive_interval = config.get('keepalive_interval', 30)
        
        # State
        self._socket: Optional[socket.socket] = None
        self._reader_thread: Optional[threading.Thread] = None
        self._keepalive_thread: Optional[threading.Thread] = None
        self._stop_threads = threading.Event()

    def connect(self) -> bool:
        """Connect to DSC alarm system.
        
        Returns:
            bool: True if connection successful
        """
        try:
            # Create socket
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(self.socket_timeout)
            self._socket.connect((self.host, self.port))
            
            # Start reader thread
            self._stop_threads.clear()
            self._reader_thread = threading.Thread(target=self._reader_loop)
            self._reader_thread.daemon = True
            self._reader_thread.start()
            
            # Start keepalive thread
            self._keepalive_thread = threading.Thread(target=self._keepalive_loop)
            self._keepalive_thread.daemon = True
            self._keepalive_thread.start()
            
            # Login
            if self.password:
                if not self._send_command(f'005{self.password}'):
                    logger.error("Failed to login")
                    self.disconnect()
                    return False
            
            # Request initial status
            if not self._send_command(DSC_COMMANDS['status_report']):
                logger.error("Failed to get initial status")
                self.disconnect()
                return False
            
            self._connected = True
            return True

        except Exception as e:
            logger.error(f"Error connecting to DSC system: {e}")
            self.disconnect()
            return False

    def disconnect(self) -> None:
        """Disconnect from DSC alarm system."""
        try:
            self._stop_threads.set()
            
            if self._reader_thread:
                self._reader_thread.join()
                self._reader_thread = None
            
            if self._keepalive_thread:
                self._keepalive_thread.join()
                self._keepalive_thread = None
            
            if self._socket:
                self._socket.close()
                self._socket = None
            
            self._connected = False

        except Exception as e:
            logger.error(f"Error disconnecting from DSC system: {e}")

    def arm(self, mode: str = 'away') -> bool:
        """Arm the system.
        
        Args:
            mode: Arming mode (away, stay, night)
            
        Returns:
            bool: True if arming successful
        """
        try:
            if not self._connected:
                return False
            
            # Send arm command
            if mode == 'away':
                command = DSC_COMMANDS['arm_away']
            elif mode == 'stay':
                command = DSC_COMMANDS['arm_stay']
            elif mode == 'night':
                command = DSC_COMMANDS['arm_zero_entry']
            else:
                logger.error(f"Invalid arm mode: {mode}")
                return False
            
            return self._send_command(f"{command}{self.partition:01d}")

        except Exception as e:
            logger.error(f"Error arming DSC system: {e}")
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
            
            # Use provided code or configured user code
            disarm_code = code or self.user_code
            if not disarm_code:
                logger.error("No disarm code provided")
                return False
            
            return self._send_command(f"{DSC_COMMANDS['disarm']}{self.partition:01d}{disarm_code}")

        except Exception as e:
            logger.error(f"Error disarming DSC system: {e}")
            return False

    def bypass_zone(self, zone_id: str) -> bool:
        """Bypass a zone.
        
        Args:
            zone_id: Zone identifier
            
        Returns:
            bool: True if bypass successful
        """
        try:
            if not self._connected or not self.user_code:
                return False
            
            # Send bypass command
            zone_num = int(zone_id)
            return self._send_command(f"071{self.user_code}{zone_num:03d}")

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
            if not self._connected or not self.user_code:
                return False
            
            # Send unbypass command
            zone_num = int(zone_id)
            return self._send_command(f"072{self.user_code}{zone_num:03d}")

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
        try:
            if not self._connected:
                return False
            
            # Send trigger command
            zone_num = int(zone_id)
            return self._send_command(f"601{zone_num:03d}")

        except Exception as e:
            logger.error(f"Error triggering alarm: {e}")
            return False

    def clear_alarm(self, zone_id: str) -> bool:
        """Clear alarm in zone.
        
        Args:
            zone_id: Zone identifier
            
        Returns:
            bool: True if clear successful
        """
        try:
            if not self._connected:
                return False
            
            # Send clear command
            zone_num = int(zone_id)
            return self._send_command(f"602{zone_num:03d}")

        except Exception as e:
            logger.error(f"Error clearing alarm: {e}")
            return False

    def _send_command(self, command: str) -> bool:
        """Send command to DSC system.
        
        Args:
            command: Command string
            
        Returns:
            bool: True if command successful
        """
        try:
            if not self._socket:
                return False
            
            # Add checksum and newline
            checksum = sum(ord(c) for c in command) % 256
            message = f"{command}{checksum:02X}\r\n"
            
            # Send command
            self._socket.send(message.encode())
            return True

        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return False

    def _reader_loop(self) -> None:
        """Socket reader loop."""
        try:
            buffer = ""
            while not self._stop_threads.is_set():
                try:
                    # Read data
                    data = self._socket.recv(1024).decode()
                    if not data:
                        break
                    
                    # Process messages
                    buffer += data
                    while '\r\n' in buffer:
                        message, buffer = buffer.split('\r\n', 1)
                        self._handle_message(message.strip())

                except socket.timeout:
                    continue
                except Exception as e:
                    logger.error(f"Error reading data: {e}")
                    break

            # Connection lost
            if not self._stop_threads.is_set():
                logger.error("Connection lost")
                self._connected = False
                self._start_reconnect()

        except Exception as e:
            logger.error(f"Error in reader loop: {e}")

    def _keepalive_loop(self) -> None:
        """Keepalive loop."""
        while not self._stop_threads.is_set():
            try:
                time.sleep(self.keepalive_interval)
                if self._connected:
                    self._send_command(DSC_COMMANDS['poll'])
            except Exception as e:
                logger.error(f"Error in keepalive loop: {e}")

    def _handle_message(self, message: str) -> None:
        """Handle received message.
        
        Args:
            message: Message string
        """
        try:
            # Verify checksum
            if len(message) < 5:
                return
            
            data = message[:-2]
            checksum = int(message[-2:], 16)
            if sum(ord(c) for c in data) % 256 != checksum:
                logger.error("Invalid checksum")
                return
            
            # Get command code
            code = data[:3]
            if code not in DSC_RESPONSES:
                return
            
            command = DSC_RESPONSES[code]
            details = data[3:]
            
            # Handle message
            if command == 'command_acknowledge':
                pass  # Normal response
            
            elif command == 'command_error':
                logger.error(f"Command error: {details}")
            
            elif command == 'system_error':
                logger.error(f"System error: {details}")
                self._add_event(AlarmEvent(
                    timestamp=datetime.now(),
                    type='system_error',
                    zone_id=None,
                    details={'error': details},
                    severity=1.0
                ))
            
            elif command in ['zone_alarm', 'zone_tamper', 'zone_fault']:
                zone_id = str(int(details))
                self._update_zone(AlarmZone(
                    zone_id=zone_id,
                    name=f"Zone {zone_id}",
                    type='security',
                    state='triggered',
                    last_trigger=datetime.now(),
                    metadata=None
                ))
                self._add_event(AlarmEvent(
                    timestamp=datetime.now(),
                    type=command,
                    zone_id=zone_id,
                    details=None,
                    severity=1.0
                ))
            
            elif command in ['zone_alarm_restore', 'zone_tamper_restore', 'zone_fault_restore']:
                zone_id = str(int(details))
                self._update_zone(AlarmZone(
                    zone_id=zone_id,
                    name=f"Zone {zone_id}",
                    type='security',
                    state='normal',
                    last_trigger=None,
                    metadata=None
                ))
                self._add_event(AlarmEvent(
                    timestamp=datetime.now(),
                    type=command,
                    zone_id=zone_id,
                    details=None,
                    severity=0.5
                ))
            
            elif command == 'partition_armed':
                self._update_state(AlarmState(
                    armed=True,
                    triggered=False,
                    bypass_zones=self._state.bypass_zones,
                    last_event=self._state.last_event,
                    last_update=datetime.now()
                ))
                self._add_event(AlarmEvent(
                    timestamp=datetime.now(),
                    type='armed',
                    zone_id=None,
                    details={'partition': int(details)},
                    severity=0.5
                ))
            
            elif command == 'partition_disarmed':
                self._update_state(AlarmState(
                    armed=False,
                    triggered=False,
                    bypass_zones=self._state.bypass_zones,
                    last_event=self._state.last_event,
                    last_update=datetime.now()
                ))
                self._add_event(AlarmEvent(
                    timestamp=datetime.now(),
                    type='disarmed',
                    zone_id=None,
                    details={'partition': int(details)},
                    severity=0.5
                ))
            
            elif command == 'partition_in_alarm':
                self._update_state(AlarmState(
                    armed=True,
                    triggered=True,
                    bypass_zones=self._state.bypass_zones,
                    last_event=self._state.last_event,
                    last_update=datetime.now()
                ))
                self._add_event(AlarmEvent(
                    timestamp=datetime.now(),
                    type='alarm',
                    zone_id=None,
                    details={'partition': int(details)},
                    severity=1.0
                ))

        except Exception as e:
            logger.error(f"Error handling message: {e}")
