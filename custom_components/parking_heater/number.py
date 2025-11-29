"""Number platform for Parking Heater."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MAX_LEVEL, MIN_LEVEL, LEVEL_STEP
from .coordinator import ParkingHeaterCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Parking Heater numbers from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    numbers = [
        ParkingHeaterLevelNumber(coordinator),
    ]
    async_add_entities(numbers)


class ParkingHeaterLevelNumber(CoordinatorEntity[ParkingHeaterCoordinator], NumberEntity):
    """Represents the power level control."""

    def __init__(self, coordinator: ParkingHeaterCoordinator) -> None:
        """Initialize the number."""
        super().__init__(coordinator)
        self._attr_name = f"{coordinator.entry.title} Power Level"
        self._attr_unique_id = f"{coordinator.mac_address}_power_level"
        self._attr_icon = "mdi:speedometer"
        self._attr_native_min_value = MIN_LEVEL
        self._attr_native_max_value = MAX_LEVEL
        self._attr_native_max_value = MAX_LEVEL
        self._attr_native_step = LEVEL_STEP

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info."""
        return self.coordinator.device_info

        """Return the current value."""
        if self.coordinator.data:
            return self.coordinator.data.get("target_level", 1)
        return None 

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        await self.coordinator.client.set_level(int(value))
        # We should probably trigger a refresh
        await self.coordinator.async_request_refresh()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.data is not None
