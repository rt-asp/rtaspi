"""Device control action."""

from typing import Dict, Any, Optional
from ...core.logging import get_logger
from ..rules import Action

logger = get_logger(__name__)


class Action(Action):
    """Device control action."""

    def __init__(self, action_type: str, config: Dict[str, Any]):
        """Initialize device action.

        Args:
            action_type: Type of action
            config: Action configuration
        """
        super().__init__(action_type, config)
        self.device_id = config.get("device_id")
        self.command = config.get("command")
        self.parameters = config.get("parameters", {})
        self._device_manager = None

    def initialize(self) -> bool:
        """Initialize action.

        Returns:
            bool: True if initialization successful
        """
        try:
            # Import device manager
            from ...device_managers import DeviceManager

            self._device_manager = DeviceManager()

            # Verify device exists
            if self.device_id:
                device = self._device_manager.get_device(self.device_id)
                if not device:
                    logger.error(f"Device {self.device_id} not found")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error initializing device action: {e}")
            return False

    def cleanup(self) -> None:
        """Clean up action resources."""
        self._device_manager = None

    def execute(self, data: Dict[str, Any]) -> bool:
        """Execute device action.

        Args:
            data: Action input data

        Returns:
            bool: True if execution successful
        """
        try:
            # Get device
            if not self.device_id:
                logger.error("No device ID specified")
                return False

            device = self._device_manager.get_device(self.device_id)
            if not device:
                logger.error(f"Device {self.device_id} not found")
                return False

            # Get command
            if not self.command:
                logger.error("No command specified")
                return False

            # Process parameter templates
            parameters = {}
            for key, value in self.parameters.items():
                if isinstance(value, str):
                    # Replace {data.key} with values from trigger data
                    for match in re.finditer(r"\{data\.([^}]+)\}", value):
                        data_key = match.group(1)
                        if data_key in data:
                            value = value.replace(match.group(0), str(data[data_key]))
                parameters[key] = value

            # Execute command
            result = device.execute_command(self.command, parameters)
            if not result:
                logger.error(
                    f"Command {self.command} failed on device {self.device_id}"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"Error executing device action: {e}")
            return False

    def get_supported_commands(self) -> Dict[str, List[str]]:
        """Get list of supported commands by device type.

        Returns:
            Dict[str, List[str]]: Device type to command list mapping
        """
        return {
            "camera": [
                "start_stream",
                "stop_stream",
                "set_resolution",
                "set_framerate",
                "set_bitrate",
                "set_quality",
                "set_position",
                "move_relative",
                "move_absolute",
                "zoom_in",
                "zoom_out",
                "focus_near",
                "focus_far",
                "auto_focus",
                "iris_open",
                "iris_close",
                "auto_iris",
            ],
            "microphone": [
                "start_stream",
                "stop_stream",
                "set_volume",
                "set_gain",
                "set_sample_rate",
                "set_channels",
                "enable_noise_reduction",
                "disable_noise_reduction",
                "enable_echo_cancellation",
                "disable_echo_cancellation",
            ],
            "intercom": [
                "start_input",
                "stop_input",
                "start_output",
                "stop_output",
                "set_volume",
                "set_gain",
                "enable_echo_cancellation",
                "disable_echo_cancellation",
            ],
            "remote_desktop": [
                "connect",
                "disconnect",
                "send_key",
                "send_mouse",
                "set_resolution",
                "set_quality",
                "set_compression",
            ],
            "sip": [
                "make_call",
                "hangup",
                "answer",
                "reject",
                "hold",
                "unhold",
                "send_dtmf",
                "set_volume",
            ],
        }
