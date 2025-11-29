"""Sensor platform for Parking Heater."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
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
        ParkingHeaterCaseTempSensor(coordinator),
        ParkingHeaterRunStateSensor(coordinator),
        ParkingHeaterConnectionStatusSensor(coordinator),
    ]
    async_add_entities(sensors)


class ParkingHeaterConnectionStatusSensor(CoordinatorEntity[ParkingHeaterCoordinator], SensorEntity):
    """Represents the connection status of the heater."""

    def __init__(self, coordinator: ParkingHeaterCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = f"{coordinator.entry.title} Connection Status"
        self._attr_unique_id = f"{coordinator.mac_address}_connection_status"
        self._attr_icon = "mdi:bluetooth-connect"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info."""
        return self.coordinator.device_info

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("connection_status", "Unknown")
        return "Unknown"
    
    @property
    def available(self) -> bool:
        """Always available to show status."""
        return True


class ParkingHeaterErrorSensor(CoordinatorEntity[ParkingHeaterCoordinator], SensorEntity):
    """Represents the error code sensor for the Parking Heater."""

    def __init__(self, coordinator: ParkingHeaterCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = f"{coordinator.entry.title} Error Code"
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
        return self.coordinator.data is not None


class ParkingHeaterRunStateSensor(CoordinatorEntity[ParkingHeaterCoordinator], SensorEntity):
    """Represents the run state of the heater."""

    def __init__(self, coordinator: ParkingHeaterCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = f"{coordinator.entry.title} State"
        self._attr_unique_id = f"{coordinator.mac_address}_run_state"
        self._attr_icon = "mdi:fire-alert"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info."""
        return self.coordinator.device_info

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            state_code = self.coordinator.data.get("run_state")
            # Map state code to text
            # 0=Off, 1=On, 2=Ignition, 3=Heating, 4=Shutdown, 5=Standby
            return {
                0: "Off",
                1: "On (Startup)",
                2: "Ignition",
                3: "Heating",
                4: "Shutdown/Cooling",
                5: "Standby"
            }.get(state_code, f"Unknown ({state_code})")
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.data is not None


class ParkingHeaterChamberTempSensor(CoordinatorEntity[ParkingHeaterCoordinator], SensorEntity):
    """Represents the chamber temperature sensor."""

    def __init__(self, coordinator: ParkingHeaterCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = f"{coordinator.entry.title} Chamber Temperature"
        self._attr_unique_id = f"{coordinator.mac_address}_chamber_temp"
        self._attr_icon = "mdi:thermometer"
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT

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
        return self.coordinator.data is not None


class ParkingHeaterCaseTempSensor(CoordinatorEntity[ParkingHeaterCoordinator], SensorEntity):
    """Represents the case (room) temperature sensor."""

    def __init__(self, coordinator: ParkingHeaterCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = f"{coordinator.entry.title} Room Temperature"
        self._attr_unique_id = f"{coordinator.mac_address}_room_temperature"
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info."""
        return self.coordinator.device_info

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("current_temperature")
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.data is not None
