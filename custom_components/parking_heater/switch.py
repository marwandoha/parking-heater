"""Switch platform for Parking Heater."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
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
    """Set up the Parking Heater switches from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    switches = [
        ParkingHeaterConnectionSwitch(coordinator),
    ]
    async_add_entities(switches)


class ParkingHeaterConnectionSwitch(CoordinatorEntity[ParkingHeaterCoordinator], SwitchEntity):
    """Represents the connection switch for the Parking Heater."""

    def __init__(self, coordinator: ParkingHeaterCoordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_name = f"{coordinator.entry.title} Connection"
        self._attr_unique_id = f"{coordinator.mac_address}_connection"
        self._attr_unique_id = f"{coordinator.mac_address}_connection"
        self._attr_icon = "mdi:bluetooth-connect"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info."""
        return self.coordinator.device_info

    @property
    def is_on(self) -> bool:
        """Return True if the client is connected."""
        return self.coordinator.client.is_connected

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Connect to the heater."""
        await self.coordinator.async_connect()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disconnect from the heater."""
        await self.coordinator.async_disconnect()
        self.async_write_ha_state()
    
    @property
    def available(self) -> bool:
        """Return True, as this switch controls connection."""
        return True
