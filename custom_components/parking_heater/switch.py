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
        ParkingHeaterPowerSwitch(coordinator),
        ParkingHeaterConnectionSwitch(coordinator),
    ]
    async_add_entities(switches)


class ParkingHeaterPowerSwitch(CoordinatorEntity[ParkingHeaterCoordinator], SwitchEntity):
    """Represents the power switch for the Parking Heater."""

    def __init__(self, coordinator: ParkingHeaterCoordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_name = f"{coordinator.entry.title} Power"
        self._attr_unique_id = f"{coordinator.mac_address}_power"
        self._attr_icon = "mdi:power"

    @property
    def is_on(self) -> bool:
        """Return True if the heater is on."""
        if self.coordinator.data:
            return self.coordinator.data.get("is_on", False)
        return False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the heater on."""
        await self.coordinator.async_set_power(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the heater off."""
        await self.coordinator.async_set_power(False)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.client.is_connected


class ParkingHeaterConnectionSwitch(CoordinatorEntity[ParkingHeaterCoordinator], SwitchEntity):
    """Represents the connection switch for the Parking Heater."""

    def __init__(self, coordinator: ParkingHeaterCoordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_name = f"{coordinator.entry.title} Connection"
        self._attr_unique_id = f"{coordinator.mac_address}_connection"
        self._attr_icon = "mdi:bluetooth-connect"

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
