"""Modbus protocol support."""

import logging
import time
from typing import Dict, Any, Optional, List, Union, Tuple
from pymodbus.client import ModbusTcpClient, ModbusSerialClient
from pymodbus.exceptions import ModbusException
from pymodbus.payload import BinaryPayloadDecoder, BinaryPayloadBuilder
from pymodbus.constants import Endian

from ...core.logging import get_logger
from ..base import DeviceManager

logger = get_logger(__name__)

class ModbusDevice:
    """Modbus device implementation."""

    def __init__(self, device_id: str, config: Dict[str, Any]):
        """Initialize Modbus device.
        
        Args:
            device_id: Device identifier
            config: Device configuration
        """
        self.device_id = device_id
        self.config = config

        # Connection settings
        self.mode = config.get('mode', 'tcp')  # tcp or rtu
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 502)
        self.unit = config.get('unit', 1)
        
        # Serial settings (for RTU mode)
        self.serial_port = config.get('serial_port')
        self.baudrate = config.get('baudrate', 9600)
        self.parity = config.get('parity', 'N')
        self.stopbits = config.get('stopbits', 1)
        self.bytesize = config.get('bytesize', 8)

        # Register mapping
        self.registers = config.get('registers', {})

        # Client
        self._client = None
        self._connected = False

    def connect(self) -> bool:
        """Connect to Modbus device.
        
        Returns:
            bool: True if connection successful
        """
        try:
            if self.mode == 'tcp':
                self._client = ModbusTcpClient(
                    host=self.host,
                    port=self.port
                )
            else:  # rtu
                self._client = ModbusSerialClient(
                    method='rtu',
                    port=self.serial_port,
                    baudrate=self.baudrate,
                    parity=self.parity,
                    stopbits=self.stopbits,
                    bytesize=self.bytesize
                )

            self._connected = self._client.connect()
            if self._connected:
                logger.info(f"Connected to Modbus device {self.device_id}")
            else:
                logger.error(f"Failed to connect to Modbus device {self.device_id}")

            return self._connected

        except Exception as e:
            logger.error(f"Error connecting to Modbus device: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from Modbus device."""
        try:
            if self._client:
                self._client.close()
                self._client = None
            self._connected = False
            logger.info(f"Disconnected from Modbus device {self.device_id}")

        except Exception as e:
            logger.error(f"Error disconnecting from Modbus device: {e}")

    def read_register(self, name: str) -> Optional[Any]:
        """Read register by name.
        
        Args:
            name: Register name from configuration
            
        Returns:
            Optional[Any]: Register value if successful
        """
        if not self._connected:
            logger.error("Device not connected")
            return None

        try:
            # Get register configuration
            reg_config = self.registers.get(name)
            if not reg_config:
                logger.error(f"Register {name} not found in configuration")
                return None

            # Get register parameters
            reg_type = reg_config.get('type', 'holding')
            address = reg_config.get('address')
            data_type = reg_config.get('data_type', 'uint16')
            count = reg_config.get('count', 1)
            scale = reg_config.get('scale', 1)
            offset = reg_config.get('offset', 0)

            # Read register
            if reg_type == 'holding':
                result = self._client.read_holding_registers(address, count, unit=self.unit)
            elif reg_type == 'input':
                result = self._client.read_input_registers(address, count, unit=self.unit)
            elif reg_type == 'coil':
                result = self._client.read_coils(address, count, unit=self.unit)
            elif reg_type == 'discrete':
                result = self._client.read_discrete_inputs(address, count, unit=self.unit)
            else:
                logger.error(f"Invalid register type: {reg_type}")
                return None

            if result.isError():
                logger.error(f"Error reading register {name}: {result}")
                return None

            # Decode value based on data type
            if reg_type in ['coil', 'discrete']:
                return result.bits[0] if count == 1 else result.bits[:count]

            decoder = BinaryPayloadDecoder.fromRegisters(
                result.registers,
                byteorder=Endian.Big,
                wordorder=Endian.Big
            )

            value = None
            if data_type == 'uint16':
                value = decoder.decode_16bit_uint()
            elif data_type == 'int16':
                value = decoder.decode_16bit_int()
            elif data_type == 'uint32':
                value = decoder.decode_32bit_uint()
            elif data_type == 'int32':
                value = decoder.decode_32bit_int()
            elif data_type == 'float32':
                value = decoder.decode_32bit_float()
            elif data_type == 'float64':
                value = decoder.decode_64bit_float()
            elif data_type == 'string':
                value = decoder.decode_string(count * 2).decode().strip('\x00')
            else:
                logger.error(f"Invalid data type: {data_type}")
                return None

            # Apply scaling and offset
            if isinstance(value, (int, float)):
                value = value * scale + offset

            return value

        except Exception as e:
            logger.error(f"Error reading register {name}: {e}")
            return None

    def write_register(self, name: str, value: Any) -> bool:
        """Write register by name.
        
        Args:
            name: Register name from configuration
            value: Value to write
            
        Returns:
            bool: True if write successful
        """
        if not self._connected:
            logger.error("Device not connected")
            return False

        try:
            # Get register configuration
            reg_config = self.registers.get(name)
            if not reg_config:
                logger.error(f"Register {name} not found in configuration")
                return False

            # Get register parameters
            reg_type = reg_config.get('type', 'holding')
            address = reg_config.get('address')
            data_type = reg_config.get('data_type', 'uint16')
            scale = reg_config.get('scale', 1)
            offset = reg_config.get('offset', 0)

            # Apply reverse scaling and offset
            if isinstance(value, (int, float)):
                value = (value - offset) / scale

            # Encode value based on data type
            if reg_type in ['coil']:
                result = self._client.write_coil(address, bool(value), unit=self.unit)
            else:
                builder = BinaryPayloadBuilder(
                    byteorder=Endian.Big,
                    wordorder=Endian.Big
                )

                if data_type == 'uint16':
                    builder.add_16bit_uint(int(value))
                elif data_type == 'int16':
                    builder.add_16bit_int(int(value))
                elif data_type == 'uint32':
                    builder.add_32bit_uint(int(value))
                elif data_type == 'int32':
                    builder.add_32bit_int(int(value))
                elif data_type == 'float32':
                    builder.add_32bit_float(float(value))
                elif data_type == 'float64':
                    builder.add_64bit_float(float(value))
                elif data_type == 'string':
                    builder.add_string(str(value).encode())
                else:
                    logger.error(f"Invalid data type: {data_type}")
                    return False

                registers = builder.to_registers()
                result = self._client.write_registers(address, registers, unit=self.unit)

            if result.isError():
                logger.error(f"Error writing register {name}: {result}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error writing register {name}: {e}")
            return False

    def read_all_registers(self) -> Dict[str, Any]:
        """Read all configured registers.
        
        Returns:
            Dict[str, Any]: Register values by name
        """
        values = {}
        for name in self.registers:
            value = self.read_register(name)
            if value is not None:
                values[name] = value
        return values

    def get_status(self) -> Dict[str, Any]:
        """Get device status.
        
        Returns:
            Dict[str, Any]: Status information
        """
        return {
            'id': self.device_id,
            'connected': self._connected,
            'mode': self.mode,
            'host': self.host if self.mode == 'tcp' else self.serial_port,
            'unit': self.unit,
            'registers': list(self.registers.keys())
        }


class ModbusManager(DeviceManager):
    """Manager for Modbus devices."""

    def __init__(self):
        """Initialize Modbus manager."""
        super().__init__()
        self._devices: Dict[str, ModbusDevice] = {}

    def add_device(self, device_id: str, config: Dict[str, Any]) -> bool:
        """Add Modbus device.
        
        Args:
            device_id: Device identifier
            config: Device configuration
            
        Returns:
            bool: True if device added successfully
        """
        try:
            # Create device
            device = ModbusDevice(device_id, config)
            if device.connect():
                self._devices[device_id] = device
                return True
            return False

        except Exception as e:
            logger.error(f"Error adding Modbus device: {e}")
            return False

    def remove_device(self, device_id: str) -> bool:
        """Remove Modbus device.
        
        Args:
            device_id: Device identifier
            
        Returns:
            bool: True if device removed
        """
        try:
            device = self._devices.get(device_id)
            if device:
                device.disconnect()
                del self._devices[device_id]
                return True
            return False

        except Exception as e:
            logger.error(f"Error removing Modbus device: {e}")
            return False

    def get_device(self, device_id: str) -> Optional[ModbusDevice]:
        """Get Modbus device by ID.
        
        Args:
            device_id: Device identifier
            
        Returns:
            Optional[ModbusDevice]: Device if found
        """
        return self._devices.get(device_id)

    def get_devices(self) -> List[ModbusDevice]:
        """Get all Modbus devices.
        
        Returns:
            List[ModbusDevice]: List of devices
        """
        return list(self._devices.values())

    def cleanup(self) -> None:
        """Clean up manager resources."""
        for device in self._devices.values():
            device.disconnect()
        self._devices.clear()
