"""Stream control action."""

from typing import Dict, Any, Optional, List
from ...core.logging import get_logger
from ..rules import Action

logger = get_logger(__name__)

class Action(Action):
    """Stream control action."""

    def __init__(self, action_type: str, config: Dict[str, Any]):
        """Initialize stream action.
        
        Args:
            action_type: Type of action
            config: Action configuration
        """
        super().__init__(action_type, config)
        self.stream_id = config.get('stream_id')
        self.command = config.get('command')
        self.parameters = config.get('parameters', {})
        self._stream_manager = None

    def initialize(self) -> bool:
        """Initialize action.
        
        Returns:
            bool: True if initialization successful
        """
        try:
            # Import stream manager
            from ...device_managers import StreamManager
            self._stream_manager = StreamManager()

            # Verify stream exists
            if self.stream_id:
                stream = self._stream_manager.get_stream(self.stream_id)
                if not stream:
                    logger.error(f"Stream {self.stream_id} not found")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error initializing stream action: {e}")
            return False

    def cleanup(self) -> None:
        """Clean up action resources."""
        self._stream_manager = None

    def execute(self, data: Dict[str, Any]) -> bool:
        """Execute stream action.
        
        Args:
            data: Action input data
            
        Returns:
            bool: True if execution successful
        """
        try:
            # Get stream
            if not self.stream_id:
                logger.error("No stream ID specified")
                return False

            stream = self._stream_manager.get_stream(self.stream_id)
            if not stream:
                logger.error(f"Stream {self.stream_id} not found")
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
                    for match in re.finditer(r'\{data\.([^}]+)\}', value):
                        data_key = match.group(1)
                        if data_key in data:
                            value = value.replace(match.group(0), str(data[data_key]))
                parameters[key] = value

            # Execute command
            result = stream.execute_command(self.command, parameters)
            if not result:
                logger.error(f"Command {self.command} failed on stream {self.stream_id}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error executing stream action: {e}")
            return False

    def get_supported_commands(self) -> Dict[str, List[str]]:
        """Get list of supported commands by stream type.
        
        Returns:
            Dict[str, List[str]]: Stream type to command list mapping
        """
        return {
            'rtsp': [
                'start',
                'stop',
                'restart',
                'set_url',
                'set_transport',
                'set_timeout',
                'set_buffer_size',
                'set_reconnect_delay',
                'enable_authentication',
                'disable_authentication',
                'set_username',
                'set_password'
            ],
            'rtmp': [
                'start',
                'stop',
                'restart',
                'set_url',
                'set_stream_key',
                'set_bitrate',
                'set_quality',
                'set_keyframe_interval',
                'set_buffer_size',
                'set_reconnect_delay',
                'enable_authentication',
                'disable_authentication',
                'set_username',
                'set_password'
            ],
            'webrtc': [
                'start',
                'stop',
                'restart',
                'set_ice_servers',
                'add_ice_server',
                'remove_ice_server',
                'set_bandwidth',
                'set_quality',
                'enable_data_channel',
                'disable_data_channel',
                'send_data',
                'set_signaling_url',
                'set_peer_id'
            ],
            'pipeline': [
                'start',
                'stop',
                'restart',
                'add_filter',
                'remove_filter',
                'set_filter_parameter',
                'enable_filter',
                'disable_filter',
                'set_input',
                'set_output',
                'add_output',
                'remove_output'
            ]
        }

    def get_supported_parameters(self) -> Dict[str, Dict[str, Any]]:
        """Get list of supported parameters by command.
        
        Returns:
            Dict[str, Dict[str, Any]]: Command to parameter info mapping
        """
        return {
            'start': {},
            'stop': {},
            'restart': {},
            'set_url': {
                'url': {
                    'type': 'string',
                    'required': True,
                    'description': 'Stream URL'
                }
            },
            'set_bitrate': {
                'bitrate': {
                    'type': 'integer',
                    'required': True,
                    'description': 'Target bitrate in bits per second',
                    'min': 100000,
                    'max': 10000000
                }
            },
            'set_quality': {
                'quality': {
                    'type': 'integer',
                    'required': True,
                    'description': 'Quality level (0-100)',
                    'min': 0,
                    'max': 100
                }
            },
            'set_buffer_size': {
                'size': {
                    'type': 'integer',
                    'required': True,
                    'description': 'Buffer size in bytes',
                    'min': 1024,
                    'max': 10485760
                }
            },
            'set_reconnect_delay': {
                'delay': {
                    'type': 'integer',
                    'required': True,
                    'description': 'Reconnect delay in seconds',
                    'min': 1,
                    'max': 300
                }
            },
            'set_username': {
                'username': {
                    'type': 'string',
                    'required': True,
                    'description': 'Authentication username'
                }
            },
            'set_password': {
                'password': {
                    'type': 'string',
                    'required': True,
                    'description': 'Authentication password'
                }
            },
            'add_filter': {
                'filter_type': {
                    'type': 'string',
                    'required': True,
                    'description': 'Type of filter to add'
                },
                'parameters': {
                    'type': 'object',
                    'required': False,
                    'description': 'Filter parameters'
                }
            },
            'remove_filter': {
                'filter_id': {
                    'type': 'string',
                    'required': True,
                    'description': 'ID of filter to remove'
                }
            },
            'set_filter_parameter': {
                'filter_id': {
                    'type': 'string',
                    'required': True,
                    'description': 'ID of filter'
                },
                'parameter': {
                    'type': 'string',
                    'required': True,
                    'description': 'Parameter name'
                },
                'value': {
                    'type': 'any',
                    'required': True,
                    'description': 'Parameter value'
                }
            }
        }
