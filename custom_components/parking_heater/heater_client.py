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
        _LOGGER.info("Initializing Parking Heater Client v1.0.3")
        self._client: BleakClient | None = None
        self._notification_data: bytearray = bytearray()
        self._notification_event = asyncio.Event()
        self._is_connected = False
        
        # Command Queue
        self._command_queue: asyncio.Queue = asyncio.Queue()
        self._command_worker_task: asyncio.Task | None = None
        
        # Local State Tracking (Fallback)
        self._last_set_level: int | None = None

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
            
            # Start Command Worker
            if self._command_worker_task is None or self._command_worker_task.done():
                self._command_worker_task = asyncio.create_task(self._command_worker())
            
            _LOGGER.info("Connected to parking heater at %s", self.mac_address)
        except Exception as err:
            _LOGGER.error("Failed to connect to %s: %s", self.mac_address, err)
            self._is_connected = False
            raise

    async def disconnect(self) -> None:
        """Disconnect from the device."""
        # Stop Command Worker
        if self._command_worker_task:
            self._command_worker_task.cancel()
            try:
                await self._command_worker_task
            except asyncio.CancelledError:
                pass
            self._command_worker_task = None

        if self._client is not None:
            try:
                if self._client.is_connected:
                    try:
                        # Try to stop notifications, but don't block forever
                        await asyncio.wait_for(self._client.stop_notify(NOTIFY_CHAR_UUID), timeout=2.0)
                    except Exception as e:
                        _LOGGER.warning("Failed to stop notifications during disconnect: %s", e)
                    
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

    async def _command_worker(self) -> None:
        """Process commands from the queue with a delay."""
        _LOGGER.debug("Command worker started")
        while True:
            try:
                # Get command from queue
                cmd_item = await self._command_queue.get()
                command, wait_for_response, timeout, future = cmd_item
                
                try:
                    if not self.is_connected:
                         raise BleakError("Not connected")

                    # Execute command
                    result = await self._send_command_internal(command, wait_for_response, timeout)
                    if not future.done():
                        future.set_result(result)
                except Exception as e:
                    if not future.done():
                        future.set_exception(e)
                finally:
                    self._command_queue.task_done()
                
                # Buffer delay to prevent overwhelming the device
                await asyncio.sleep(0.8) 
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                _LOGGER.error("Error in command worker: %s", e)
                await asyncio.sleep(1.0)

    def _notification_handler(
        self, sender: BleakGATTCharacteristic, data: bytearray
    ) -> None:
        """Handle notification data."""
        _LOGGER.debug("Received notification: %s", data.hex())
        self._notification_data = data
        self._notification_event.set()

    async def _send_command(self, command: bytes, wait_for_response: bool = True, timeout: float = 5.0) -> bytearray:
        """Queue a command and wait for result."""
        if not self.is_connected:
            raise BleakError("Not connected to device")
            
        future = asyncio.get_running_loop().create_future()
        await self._command_queue.put((command, wait_for_response, timeout, future))
        
        # Wait for the worker to process it
        return await future

    async def _send_command_internal(self, command: bytes, wait_for_response: bool = True, timeout: float = 5.0) -> bytearray:
        """Internal method to send command (executed by worker)."""
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
                await asyncio.wait_for(self._notification_event.wait(), timeout=timeout)
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

    async def _send_command(self, command: bytes, wait_for_response: bool = True, timeout: float = 5.0) -> bytearray:
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
                await asyncio.wait_for(self._notification_event.wait(), timeout=timeout)
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
            # We might receive other packets (like command responses), so we retry a few times
            # until we get a status packet (Byte 2 == 0x01)
            
            max_retries = 3
            for attempt in range(max_retries):
                # Use short timeout for polling to avoid blocking UI
                response = await self._send_command(CMD_GET_STATUS, timeout=2.0)
                
                if not response or len(response) < 13:
                    _LOGGER.warning("Invalid response received")
                    continue
                
                # Check if it's a status packet (0x01)
                if response[2] == 0x01:
                    break
                
                _LOGGER.debug("Received non-status packet (cmd=%02x), retrying...", response[2])
                await asyncio.sleep(0.1)
            else:
                _LOGGER.warning("Failed to get valid status packet after retries")
                raise BleakError("Failed to get valid status packet")

            # Parse Decrypted Data
            _LOGGER.debug("Decrypted Status Packet: %s", response.hex())
            
            run_state = response[3]
            run_mode = response[8]
            
            # Logic from ESPHome (diesel_heater_ble/messages.h)
            # Mode 0: Level = Byte 10 + 1
            # Mode 1: Level = Byte 9
            # Mode 2: Level = Byte 10 + 1 (Temp = Byte 9)
            
            target_level = 1
            target_temp = 20 # Default
            
            if run_mode == 0x00:
                target_level = response[10] + 1
            elif run_mode == 0x01:
                # User logs show Byte 10 is the level (05 = Level 5)
                # Byte 9 was 25 (0x19), which is likely temperature or ignored
                target_level = response[10]
            elif run_mode == 0x02:
                target_temp = response[9]
                target_level = response[10] + 1
            else:
                # Fallback: Try Byte 10 first as it seems more reliable for level
                target_level = response[10] if len(response) > 10 else 1
            
            # Clamp level 1-10
            target_level = max(1, min(10, target_level))
            
            # Local Tracking Override/Fallback
            # If the heater reports 1 (default) but we set it to something else recently, prefer our local value.
            # This handles heaters that don't report back the target level.
            if self._last_set_level is not None:
                # If reported level is 1 (common default) and we have a different local value, use local.
                # Or if we just want to trust local more?
                # Let's trust local if reported is 1, or if we want to be very aggressive.
                # For now, let's just log it and use local if reported is 1.
                if target_level == 1 and self._last_set_level != 1:
                     _LOGGER.debug("Using local level %d instead of reported 1", self._last_set_level)
                     target_level = self._last_set_level
                # Also update local state if reported state changes to something valid
                elif target_level != 1:
                     self._last_set_level = target_level
            
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
                "target_temperature": target_temp, 
                "target_level": target_level, # Add target_level
                "current_temperature": chamber_temp, # Swapped: Bytes 32-33 (Room)
                "chamber_temperature": case_temp,    # Swapped: Bytes 13-14 (Chamber)
                "fan_speed": 1, # Placeholder
                "error_code": response[4],
                "connection_status": "Connected",
            }
            
            _LOGGER.debug("Parsed status: %s", status)
            return status
        except Exception as err:
            _LOGGER.error("Error getting status: %s", err)
            raise

    def _get_default_status(self) -> dict[str, Any]:
        """Return default status when device is unreachable."""
        return {
            "is_on": False,
            "target_temperature": MIN_TEMP,
            "target_level": 1,
            "current_temperature": MIN_TEMP,
            "chamber_temperature": MIN_TEMP,
            "fan_speed": 1,
            "error_code": 0,
            "connection_status": "Unknown",
        }

    async def set_power(self, power_on: bool) -> None:
        """Turn the heater on or off."""
        # Turn On: 03 01 00
        # Turn Off: 03 00 00
        command = self._build_command(0x03, 0x01 if power_on else 0x00)
        
        # We wait for response to ensure the command is processed
        # Retry logic for robustness
        for attempt in range(3):
            try:
                # Use reasonable timeout for commands
                await self._send_command(command, wait_for_response=True, timeout=3.0)
                await asyncio.sleep(0.5) 
                _LOGGER.info("Set power to %s (Attempt %d)", "ON" if power_on else "OFF", attempt + 1)
                return
            except Exception as e:
                _LOGGER.warning("Set power failed (Attempt %d): %s", attempt + 1, e)
                await asyncio.sleep(0.5)
        
        _LOGGER.warning("Failed to set power after 3 attempts, sending blindly")
        try:
            await self._send_command(command, wait_for_response=False)
        except:
            pass

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
        await asyncio.sleep(0.5) # Wait for mode switch

        # Command: 04 [Level] 00
        command = self._build_command(0x04, level)
        
        # Retry logic
        for attempt in range(3):
            try:
                await self._send_command(command, wait_for_response=True)
                await asyncio.sleep(0.5)
                _LOGGER.info("Set level to %d (Attempt %d)", level, attempt + 1)
                self._last_set_level = level # Update local state
                return
            except Exception as e:
                _LOGGER.warning("Set level failed (Attempt %d): %s", attempt + 1, e)
                await asyncio.sleep(1.0)
                
        _LOGGER.error("Failed to set level after 3 attempts")

    async def set_fan_speed(self, fan_speed: int) -> None:
        """Set fan speed (1-5)."""
        # Not implemented in this protocol version yet
        _LOGGER.warning("Set fan speed not implemented")
