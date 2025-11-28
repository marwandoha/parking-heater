"""Bluetooth client for Parking Heater."""
from __future__ import annotations

import asyncio
import logging
import struct
from typing import Any, Callable

from bleak import BleakClient, BleakGATTCharacteristic
from bleak.exc import BleakError
from bleak_retry_connector import establish_connection

from homeassistant.core import HomeAssistant

from .const import (
    CMD_GET_STATUS,
    CMD_POWER_OFF,
    CMD_POWER_ON,
    MAX_TEMP,
    MIN_TEMP,
    NOTIFY_CHAR_UUID,
    SERVICE_UUID,
    WRITE_CHAR_UUID,
)

_LOGGER = logging.getLogger(__name__)


class ParkingHeaterClient:
    """Client for communicating with parking heater via Bluetooth."""

    def __init__(self, mac_address: str, hass: HomeAssistant) -> None:
        """Initialize the client."""
        self.mac_address = mac_address
        self.hass = hass
        self._client: BleakClient | None = None
        self._notification_data: bytearray = bytearray()
        self._notification_event = asyncio.Event()
        self._is_connected = False

    @property
    def is_connected(self) -> bool:
        """Return connection status."""
        return self._is_connected and self._client is not None and self._client.is_connected

    async def connect(self) -> None:
        """Connect to the device."""
        if self.is_connected:
            return

        try:
            _LOGGER.debug("Connecting to %s", self.mac_address)
            
            # Create BleakClient directly
            self._client = BleakClient(
                self.mac_address,
                disconnected_callback=self._on_disconnect,
            )
            
            await self._client.connect()
            
            # Subscribe to notifications
            await self._client.start_notify(NOTIFY_CHAR_UUID, self._notification_handler)
            self._is_connected = True
            _LOGGER.info("Connected to parking heater at %s", self.mac_address)
        except Exception as err:
            _LOGGER.error("Failed to connect to %s: %s", self.mac_address, err)
            self._is_connected = False
            raise

    async def disconnect(self) -> None:
        """Disconnect from the device."""
        if self._client is not None:
            try:
                if self._client.is_connected:
                    await self._client.stop_notify(NOTIFY_CHAR_UUID)
                    await self._client.disconnect()
            except Exception as err:
                _LOGGER.error("Error disconnecting: %s", err)
            finally:
                self._client = None
                self._is_connected = False

    def _on_disconnect(self, client: BleakClient) -> None:
        """Handle disconnection."""
        _LOGGER.warning("Disconnected from parking heater at %s", self.mac_address)
        self._is_connected = False

    def _notification_handler(
        self, sender: BleakGATTCharacteristic, data: bytearray
    ) -> None:
        """Handle notification data."""
        _LOGGER.debug("Received notification: %s", data.hex())
        self._notification_data = data
        self._notification_event.set()

    async def _send_command(self, command: bytes) -> bytearray:
        """Send a command and wait for response."""
        if not self.is_connected:
            raise BleakError("Not connected to device")

        self._notification_event.clear()
        self._notification_data = bytearray()

        try:
            _LOGGER.debug("Sending command: %s", command.hex())
            await self._client.write_gatt_char(WRITE_CHAR_UUID, command, response=False)
            
            # Wait for response with timeout
            try:
                await asyncio.wait_for(self._notification_event.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                _LOGGER.warning("Timeout waiting for response")
                return bytearray()

            return self._notification_data
        except Exception as err:
            _LOGGER.error("Error sending command: %s", err)
            raise

    def _calculate_checksum(self, data: bytes) -> int:
        """Calculate checksum for command."""
        return sum(data) & 0xFF

    def _build_command(self, cmd_type: int, data: bytes = b"") -> bytes:
        """Build a command with checksum."""
        # Command format: [0x76, cmd_type, length, data..., checksum]
        length = len(data)
        command = bytes([0x76, cmd_type, length]) + data
        checksum = self._calculate_checksum(command)
        return command + bytes([checksum])

    async def get_status(self) -> dict[str, Any]:
        """Get current status from the heater."""
        try:
            response = await self._send_command(CMD_GET_STATUS)
            
            if not response or len(response) < 8:
                _LOGGER.warning("Invalid response received")
                return self._get_default_status()

            # Parse response
            # This is a common format for Chinese BLE heaters, but may need adjustment
            # Format: [header, cmd, length, power, temp, fan_speed, ..., checksum]
            status = {
                "is_on": bool(response[3]) if len(response) > 3 else False,
                "target_temperature": response[4] if len(response) > 4 else MIN_TEMP,
                "current_temperature": response[5] if len(response) > 5 else MIN_TEMP,
                "fan_speed": response[6] if len(response) > 6 else 1,
                "error_code": response[7] if len(response) > 7 else 0,
            }
            
            _LOGGER.debug("Parsed status: %s", status)
            return status
        except Exception as err:
            _LOGGER.error("Error getting status: %s", err)
            return self._get_default_status()

    def _get_default_status(self) -> dict[str, Any]:
        """Return default status when device is unreachable."""
        return {
            "is_on": False,
            "target_temperature": MIN_TEMP,
            "current_temperature": MIN_TEMP,
            "fan_speed": 1,
            "error_code": 0,
        }

    async def set_power(self, power_on: bool) -> None:
        """Turn the heater on or off."""
        command = CMD_POWER_ON if power_on else CMD_POWER_OFF
        await self._send_command(command)
        _LOGGER.info("Set power to %s", "ON" if power_on else "OFF")

    async def set_temperature(self, temperature: int) -> None:
        """Set target temperature."""
        if not MIN_TEMP <= temperature <= MAX_TEMP:
            raise ValueError(f"Temperature must be between {MIN_TEMP} and {MAX_TEMP}")

        # Command format for setting temperature
        command = self._build_command(0x18, bytes([temperature]))
        await self._send_command(command)
        _LOGGER.info("Set temperature to %d°C", temperature)

    async def set_fan_speed(self, fan_speed: int) -> None:
        """Set fan speed (1-5)."""
        if not 1 <= fan_speed <= 5:
            raise ValueError("Fan speed must be between 1 and 5")

        # Command format for setting fan speed
        command = self._build_command(0x19, bytes([fan_speed]))
        await self._send_command(command)
        _LOGGER.info("Set fan speed to %d", fan_speed)
