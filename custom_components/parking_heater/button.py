"""Button platform for Parking Heater."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ParkingHeaterCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Parking Heater buttons from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    buttons = [
        ParkingHeaterTurnOnButton(coordinator),
        ParkingHeaterTurnOffButton(coordinator),
    ]
    async_add_entities(buttons)


class ParkingHeaterTurnOnButton(CoordinatorEntity[ParkingHeaterCoordinator], ButtonEntity):
    """Button to turn on the heater."""

    def __init__(self, coordinator: ParkingHeaterCoordinator) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_name = f"{coordinator.entry.title} Turn On"
        self._attr_unique_id = f"{coordinator.mac_address}_turn_on"
        self._attr_icon = "mdi:power-on"

    @property
    def device_info(self):
        """Return device info."""
        return self.coordinator.device_info

    async def async_press(self) -> None:
        """Press the button."""
        await self.coordinator.async_set_power(True)


class ParkingHeaterTurnOffButton(CoordinatorEntity[ParkingHeaterCoordinator], ButtonEntity):
    """Button to turn off the heater."""

    def __init__(self, coordinator: ParkingHeaterCoordinator) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_name = f"{coordinator.entry.title} Turn Off"
        self._attr_unique_id = f"{coordinator.mac_address}_turn_off"
        self._attr_icon = "mdi:power-off"

    @property
    def device_info(self):
        """Return device info."""
        return self.coordinator.device_info

    async def async_press(self) -> None:
        """Press the button."""
        await self.coordinator.async_set_power(False)
