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
        self._lock = asyncio.Lock()

    async def async_connect(self) -> None:
        """Connect to the device."""
        try:
            await self.client.connect()
            _LOGGER.info("Successfully connected to parking heater at %s", self.mac_address)
        except Exception as err:
            _LOGGER.error("Failed to connect to parking heater: %s", err)
            raise

    async def async_disconnect(self) -> None:
        """Disconnect from the device."""
        await self.client.disconnect()
        _LOGGER.info("Disconnected from parking heater at %s", self.mac_address)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the device."""
        async with self._lock:
            try:
                if not self.client.is_connected:
                    await self.client.connect()
                
                data = await self.client.get_status()
                _LOGGER.debug("Received data from parking heater: %s", data)
                return data
            except Exception as err:
                _LOGGER.error("Error fetching parking heater data: %s", err)
                # Try to reconnect on next update
                await self.client.disconnect()
                raise UpdateFailed(f"Error communicating with device: {err}") from err

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
