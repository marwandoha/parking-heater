"""Climate platform for Parking Heater integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_DEVICE_NAME,
    CONF_MAC_ADDRESS,
    DOMAIN,
    FAN_SPEEDS,
    MAX_TEMP,
    MIN_TEMP,
    TEMP_STEP,
)
from .coordinator import ParkingHeaterCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the climate platform."""
    coordinator: ParkingHeaterCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    async_add_entities(
        [ParkingHeaterClimate(coordinator, entry)],
        update_before_add=True,
    )


class ParkingHeaterClimate(CoordinatorEntity, ClimateEntity):
    """Representation of a Parking Heater climate device."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = TEMP_STEP
    _attr_min_temp = MIN_TEMP
    _attr_max_temp = MAX_TEMP
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
    )
    _attr_fan_modes = list(FAN_SPEEDS.keys())

    def __init__(
        self,
        coordinator: ParkingHeaterCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the climate device."""
        super().__init__(coordinator)
        self._attr_unique_id = entry.data[CONF_MAC_ADDRESS].replace(":", "").lower()
        self._attr_name = entry.data.get(CONF_DEVICE_NAME, "Parking Heater")
        self._mac_address = entry.data[CONF_MAC_ADDRESS]
        
        # Device info for proper grouping in HA
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._mac_address)},
            "name": self._attr_name,
            "manufacturer": "Generic",
            "model": "BLE Parking Heater",
            "sw_version": "1.0",
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current HVAC mode."""
        if self.coordinator.data and self.coordinator.data.get("is_on"):
            return HVACMode.HEAT
        return HVACMode.OFF

    @property
    def hvac_action(self) -> HVACAction:
        """Return current HVAC action."""
        if not self.coordinator.data or not self.coordinator.data.get("is_on"):
            return HVACAction.OFF
        
        current_temp = self.coordinator.data.get("current_temperature", MIN_TEMP)
        target_temp = self.coordinator.data.get("target_temperature", MIN_TEMP)
        
        if current_temp < target_temp:
            return HVACAction.HEATING
        return HVACAction.IDLE

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        if self.coordinator.data:
            return float(self.coordinator.data.get("current_temperature", MIN_TEMP))
        return None

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        if self.coordinator.data:
            return float(self.coordinator.data.get("target_temperature", MIN_TEMP))
        return None

    @property
    def fan_mode(self) -> str | None:
        """Return the current fan mode."""
        if self.coordinator.data:
            fan_speed = self.coordinator.data.get("fan_speed", 1)
            return str(fan_speed)
        return "1"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attrs = {}
        if self.coordinator.data:
            attrs["mac_address"] = self._mac_address
            error_code = self.coordinator.data.get("error_code", 0)
            if error_code != 0:
                attrs["error_code"] = error_code
        return attrs

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.HEAT:
            await self.coordinator.async_set_power(True)
        elif hvac_mode == HVACMode.OFF:
            await self.coordinator.async_set_power(False)
        else:
            _LOGGER.warning("Unsupported HVAC mode: %s", hvac_mode)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        temperature = int(temperature)
        if not MIN_TEMP <= temperature <= MAX_TEMP:
            _LOGGER.warning(
                "Temperature %d out of range (%d-%d)",
                temperature,
                MIN_TEMP,
                MAX_TEMP,
            )
            return

        await self.coordinator.async_set_temperature(temperature)

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new fan mode."""
        if fan_mode not in FAN_SPEEDS:
            _LOGGER.warning("Invalid fan mode: %s", fan_mode)
            return

        fan_speed = FAN_SPEEDS[fan_mode]
        await self.coordinator.async_set_fan_speed(fan_speed)
