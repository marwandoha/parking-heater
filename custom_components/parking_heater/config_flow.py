"""Config flow for Parking Heater integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from bleak import BleakScanner
from bleak.backends.device import BLEDevice

from .helpers.scan import async_ble_scan

from homeassistant import config_entries
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.const import CONF_ADDRESS
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_DEVICE_NAME, CONF_MAC_ADDRESS, DOMAIN, SERVICE_UUID

_LOGGER = logging.getLogger(__name__)


class ParkingHeaterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Parking Heater."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_devices: dict[str, BluetoothServiceInfoBleak] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            mac_address = user_input[CONF_MAC_ADDRESS]
            await self.async_set_unique_id(mac_address.lower())
            self._abort_if_unique_id_configured()

            device_name = user_input.get(CONF_DEVICE_NAME, f"Parking Heater {mac_address[-5:]}")

            return self.async_create_entry(
                title=device_name,
                data={
                    CONF_MAC_ADDRESS: mac_address,
                    CONF_DEVICE_NAME: device_name,
                },
            )

        # Scan for Bluetooth devices using helper (covers adapters)
        discovered_devices = await async_ble_scan(timeout=8.0)

        # Convert to BluetoothServiceInfo-like dict used below
        # discovered_devices is address -> {name, rssi, uuids, address}

        if not discovered_devices:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_MAC_ADDRESS): str,
                        vol.Optional(CONF_DEVICE_NAME, default="Parking Heater"): str,
                    }
                ),
                errors={"base": "no_devices_found"} if not discovered_devices else errors,
                description_placeholders={
                    "info": "No devices found automatically. Please enter MAC address manually."
                },
            )

        # Create a dropdown with discovered devices
        device_options = {}
        for mac, info in discovered_devices.items():
            name = info.get("name") if isinstance(info, dict) else getattr(info, "name", None)
            display = f"{name or 'Unknown'} ({mac})"
            device_options[mac] = display

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_MAC_ADDRESS): vol.In(device_options),
                    vol.Optional(CONF_DEVICE_NAME, default="Parking Heater"): str,
                }
            ),
            errors=errors,
        )

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle bluetooth discovery."""
        _LOGGER.debug("Discovered device: %s", discovery_info)
        
        await self.async_set_unique_id(discovery_info.address.lower())
        self._abort_if_unique_id_configured()

        self.context["title_placeholders"] = {
            "name": discovery_info.name or discovery_info.address
        }

        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm bluetooth discovery."""
        if user_input is not None:
            discovery_info = self._discovered_devices[self.unique_id]
            device_name = user_input.get(
                CONF_DEVICE_NAME, discovery_info.name or "Parking Heater"
            )

            return self.async_create_entry(
                title=device_name,
                data={
                    CONF_MAC_ADDRESS: discovery_info.address,
                    CONF_DEVICE_NAME: device_name,
                },
            )

        return self.async_show_form(
            step_id="bluetooth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_DEVICE_NAME, default="Parking Heater"): str,
                }
            ),
            description_placeholders=self.context.get("title_placeholders", {}),
        )

    async def _async_discover_devices(self) -> dict[str, BluetoothServiceInfoBleak]:
        """Discover Bluetooth devices."""
        _LOGGER.debug("Discovering Bluetooth devices")
        
        # First, check Home Assistant's bluetooth integration for already discovered devices
        discovered = {}
        for service_info in async_discovered_service_info(self.hass):
            # Look for devices with the parking heater service UUID or matching name pattern
            if SERVICE_UUID.lower() in [uuid.lower() for uuid in service_info.service_uuids]:
                discovered[service_info.address] = service_info
                self._discovered_devices[service_info.address] = service_info
            elif service_info.name and any(
                pattern in service_info.name.lower()
                for pattern in ["air", "heater", "parking"]
            ):
                discovered[service_info.address] = service_info
                self._discovered_devices[service_info.address] = service_info

        _LOGGER.debug("Found %d devices", len(discovered))
        return discovered
