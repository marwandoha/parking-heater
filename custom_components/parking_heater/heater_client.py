"""Bluetooth client for Parking Heater."""
from __future__ import annotations

import asyncio
import logging
import struct
from typing import Any, Callable

from bleak import BleakClient, BleakGATTCharacteristic, BleakScanner
from bleak.exc import BleakError
from bleak_retry_connector import establish_connection, BleakClientWithServiceCache

from homeassistant.core import HomeAssistant

from .const import (
    CMD_GET_STATUS,
    MAX_TEMP,
    MIN_TEMP,
    NOTIFY_CHAR_UUID,
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

            device = await BleakScanner.find_device_by_address(
                self.mac_address, timeout=20.0
            )
            if not device:
                raise BleakError(f"Device with address {self.mac_address} not found")

            self._client = await establish_connection(
                BleakClientWithServiceCache,
                device,
                self.mac_address,
                disconnected_callback=self._on_disconnect,
            )

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
        # Sum of bytes 2 to end (excluding checksum itself if present)
        # But for our build_command, we sum bytes 2-6
        return sum(data[2:]) & 0xFF

    def _build_command(self, cmd_type: int, data1: int = 0, data2: int = 0) -> bytes:
        """Build a command with checksum."""
        # Structure: AA 55 0C 22 [CMD] [DATA1] [DATA2] [CS]
        # 0C 22 is fixed password "1234"
        cmd = bytearray([0xAA, 0x55, 0x0C, 0x22, cmd_type, data1, data2, 0x00])
        cmd[7] = sum(cmd[2:7]) & 0xFF
        return bytes(cmd)

    def _decrypt_data(self, data: bytearray) -> bytearray:
        """Decrypts data by XORing with 'password'."""
        key = b"password"
        decrypted = bytearray(data)
        for i in range(len(decrypted)):
            decrypted[i] ^= key[i % 8]
        return decrypted

    def _notification_handler(
        self, sender: BleakGATTCharacteristic, data: bytearray
    ) -> None:
        """Handle notification data."""
        _LOGGER.debug("Received notification: %s", data.hex())
        
        # Check for Encrypted Packet (starts with DA)
        if len(data) > 0 and data[0] == 0xDA:
            try:
                decrypted = self._decrypt_data(data)
                _LOGGER.debug("Decrypted Data: %s", decrypted.hex())
                
                if decrypted[0] == 0xAA and decrypted[1] == 0x55:
                    self._notification_data = decrypted
                    self._notification_event.set()
            except Exception as err:
                _LOGGER.error("Decryption failed: %s", err)

    async def _send_command(self, command: bytes, wait_for_response: bool = True) -> bytearray:
        """Send a command and wait for response."""
        if not self.is_connected:
            raise BleakError("Not connected to device")

        self._notification_event.clear()
        self._notification_data = bytearray()

        try:
            _LOGGER.debug("Sending command: %s", command.hex())
            await self._client.write_gatt_char(WRITE_CHAR_UUID, command, response=False)
            
            if not wait_for_response:
                return bytearray()

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

    async def get_status(self) -> dict[str, Any]:
        """Get current status from the heater."""
        try:
            # Active Polling: Send CMD_GET_STATUS
            response = await self._send_command(CMD_GET_STATUS)
            
            if not response or len(response) < 13:
                _LOGGER.warning("Invalid response received")
                return self._get_default_status()

            # Parse Decrypted Data
            # Byte 3: Running State (0=Off, 1=On, 2=Ignition, 3=Heating, 4=Shutdown)
            # Byte 11, 12: Voltage
            # Byte 13, 14: Case Temp
            # Byte 32, 33: Chamber Temp (if available, usually in 48-byte packet)
            
            run_state = response[3]
            # err_code = response[4]
            # voltage = (response[12] + (response[11] << 8)) / 10.0
            case_temp = response[14] + (response[13] << 8)
            if case_temp > 32767: case_temp -= 65536
            
            chamber_temp = 0
            if len(response) >= 34:
                chamber_temp = response[33] + (response[32] << 8)
                if chamber_temp > 32767: chamber_temp -= 65536
                chamber_temp = chamber_temp / 10.0 # Often scaled by 10

            is_on = run_state in [1, 2, 3, 4] 
            
            status = {
                "is_on": is_on,
                "run_state": run_state,
                "target_temperature": MIN_TEMP, # TODO: Parse set temp from byte 9
                "current_temperature": case_temp,
                "chamber_temperature": chamber_temp,
                "fan_speed": 1, # Placeholder
                "error_code": response[4],
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
            "chamber_temperature": MIN_TEMP,
            "fan_speed": 1,
            "error_code": 0,
        }

    async def set_power(self, power_on: bool) -> None:
        """Turn the heater on or off."""
        # Turn On: 03 01 00
        # Turn Off: 03 00 00
        command = self._build_command(0x03, 0x01 if power_on else 0x00)
        
        # We wait for response to ensure the command is processed
        # The heater sends a specific response packet starting with AA 55 03 ...
        await self._send_command(command, wait_for_response=True)
        await asyncio.sleep(0.5) # Give it a moment
        _LOGGER.info("Set power to %s", "ON" if power_on else "OFF")

    async def set_mode(self, mode: int) -> None:
        """Set running mode (1=Manual/Level, 2=Auto/Temp)."""
        # Command: 02 [Mode] 00
        command = self._build_command(0x02, mode)
        await self._send_command(command, wait_for_response=False)
        _LOGGER.info("Set mode to %d", mode)

    async def set_temperature(self, temperature: int) -> None:
        """Set target temperature (Auto Mode)."""
        if not MIN_TEMP <= temperature <= MAX_TEMP:
            raise ValueError(f"Temperature must be between {MIN_TEMP} and {MAX_TEMP}")

        # Ensure Auto Mode (2) first
        await self.set_mode(2)
        await asyncio.sleep(0.2)
        
        # Command: 04 [Temp] 00
        command = self._build_command(0x04, temperature)
        await self._send_command(command, wait_for_response=False)
        _LOGGER.info("Set temperature to %d°C", temperature)

    async def set_level(self, level: int) -> None:
        """Set power level (Manual Mode)."""
        if not 1 <= level <= 10:
            raise ValueError("Level must be between 1 and 10")

        # Ensure Manual Mode (1) first
        await self.set_mode(1)
        await asyncio.sleep(0.2)

        # Command: 04 [Level] 00
        command = self._build_command(0x04, level)
        await self._send_command(command, wait_for_response=False)
        _LOGGER.info("Set level to %d", level)

    async def set_fan_speed(self, fan_speed: int) -> None:
        """Set fan speed (1-5)."""
        # Not implemented in this protocol version yet
        _LOGGER.warning("Set fan speed not implemented")
