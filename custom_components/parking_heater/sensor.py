"""Sensor platform for Parking Heater."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
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
    """Set up the Parking Heater sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    sensors = [
        ParkingHeaterErrorSensor(coordinator),
        ParkingHeaterChamberTempSensor(coordinator),
    ]
    async_add_entities(sensors)


class ParkingHeaterErrorSensor(CoordinatorEntity[ParkingHeaterCoordinator], SensorEntity):
    """Represents the error code sensor for the Parking Heater."""

    def __init__(self, coordinator: ParkingHeaterCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = f"{coordinator.entry.title} Error Code"
        self._attr_unique_id = f"{coordinator.mac_address}_error_code"
        self._attr_unique_id = f"{coordinator.mac_address}_error_code"
        self._attr_icon = "mdi:alert-circle-outline"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info."""
        return self.coordinator.device_info

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("error_code")
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.client.is_connected and self.coordinator.data is not None


class ParkingHeaterChamberTempSensor(CoordinatorEntity[ParkingHeaterCoordinator], SensorEntity):
    """Represents the chamber temperature sensor."""

    def __init__(self, coordinator: ParkingHeaterCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = f"{coordinator.entry.title} Chamber Temperature"
        self._attr_unique_id = f"{coordinator.mac_address}_chamber_temp"
        self._attr_icon = "mdi:thermometer"
        self._attr_native_unit_of_measurement = "°C"
        self._attr_native_unit_of_measurement = "°C"
        self._attr_device_class = "temperature"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info."""
        return self.coordinator.device_info

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("chamber_temperature")
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.client.is_connected and self.coordinator.data is not None
