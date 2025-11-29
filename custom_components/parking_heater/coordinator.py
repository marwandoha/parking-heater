"""Data coordinator for Parking Heater integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_MAC_ADDRESS, DOMAIN, UPDATE_INTERVAL
from .heater_client import ParkingHeaterClient

_LOGGER = logging.getLogger(__name__)


class ParkingHeaterCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Parking Heater data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.entry = entry
        self.mac_address = entry.data[CONF_MAC_ADDRESS]
        self.client = ParkingHeaterClient(self.mac_address, hass)
        self.client = ParkingHeaterClient(self.mac_address, hass)
        self._lock = asyncio.Lock()
        self._desired_connection_status = True # Default to auto-connect

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self.mac_address)},
            "name": self.entry.title,
            "manufacturer": "Parking Heater",
            "model": "BLE Controller",
            "sw_version": "1.0",
        }

    async def async_connect(self) -> None:
        """Connect to the device."""
        self._desired_connection_status = True
        try:
            await self.client.connect()
            _LOGGER.info("Successfully connected to parking heater at %s", self.mac_address)
        except Exception as err:
            _LOGGER.error("Failed to connect to parking heater: %s", err)
            raise

    async def async_disconnect(self) -> None:
        """Disconnect from the device."""
        self._desired_connection_status = False
        await self.client.disconnect()
        _LOGGER.info("Disconnected from parking heater at %s", self.mac_address)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the device."""
        # Initialize default data structure if not present
        if self.data is None:
            self.data = self.client._get_default_status()
            self.data["connection_status"] = "Initializing"

        # If manual disconnect was requested, don't poll
        if not self._desired_connection_status:
            if self.client.is_connected:
                await self.client.disconnect()
            
            data = self.client._get_default_status()
            data["connection_status"] = "Disconnected (Manual)"
            return data

        async with self._lock:
            try:
                if not self.client.is_connected:
                    # Update status to Connecting
                    if self.data:
                        self.data["connection_status"] = "Connecting..."
                        self.async_set_updated_data(self.data) # Force update to show "Connecting"
                    
                    await self.client.connect()
                
                # Fetch data
                data = await self.client.get_status()
                data["connection_status"] = "Connected"
                _LOGGER.debug("Received data from parking heater: %s", data)
                return data

            except Exception as err:
                _LOGGER.error("Error communicating with parking heater: %s", err)
                # Try to disconnect to clean up state
                try:
                    await self.client.disconnect()
                except:
                    pass
                
                # Return default data with error status
                # We do NOT raise UpdateFailed so that the "Connection Status" sensor remains visible
                data = self.client._get_default_status()
                data["connection_status"] = f"Error: {str(err)[:20]}..." # Truncate error
                return data

    async def async_set_power(self, power_on: bool) -> None:
        """Turn the heater on or off."""
        async with self._lock:
            try:
                if not self.client.is_connected:
                    await self.client.connect()
                
                await self.client.set_power(power_on)
                # Request immediate update
                await asyncio.sleep(1)
                await self.async_request_refresh()
            except Exception as err:
                _LOGGER.error("Error setting power state: %s", err)
                raise

    async def async_set_temperature(self, temperature: int) -> None:
        """Set the target temperature."""
        async with self._lock:
            try:
                if not self.client.is_connected:
                    await self.client.connect()
                
                await self.client.set_temperature(temperature)
                # Request immediate update
                await asyncio.sleep(1)
                await self.async_request_refresh()
            except Exception as err:
                _LOGGER.error("Error setting temperature: %s", err)
                raise

    async def async_set_fan_speed(self, fan_speed: int) -> None:
        """Set the fan speed."""
        async with self._lock:
            try:
                if not self.client.is_connected:
                    await self.client.connect()
                
                await self.client.set_fan_speed(fan_speed)
                # Request immediate update
                await asyncio.sleep(1)
                await self.async_request_refresh()
            except Exception as err:
                _LOGGER.error("Error setting fan speed: %s", err)
                raise
