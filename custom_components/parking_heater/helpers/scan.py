"""BLE scanning helper for Parking Heater integration.

This uses bleak to perform a short scan and returns a map of
address -> BluetoothServiceInfo-like dict with name, rssi, uuids, adapter.
"""
from __future__ import annotations

from typing import Dict, Any
import asyncio
import logging

from bleak import BleakScanner

_LOGGER = logging.getLogger(__name__)


async def async_ble_scan(timeout: float = 8.0) -> Dict[str, Dict[str, Any]]:
    """Perform a BLE scan and return discovered devices.

    Returns a dict keyed by address with fields: name, rssi, uuids, metadata.
    """
    _LOGGER.debug("Starting BLE scan for %ss", timeout)
    devices = {}
    discovered = []

    def detection_callback(device, advertisement_data):
        """Handle device discovery."""
        discovered.append((device, advertisement_data))

    scanner = BleakScanner(detection_callback=detection_callback)
    try:
        await scanner.start()
        await asyncio.sleep(timeout)
        await scanner.stop()
    except Exception as exc:
        _LOGGER.exception("BLE scan failed: %s", exc)
        try:
            await scanner.stop()
        except Exception:
            pass
        return {}

    for d, ad in discovered:
        # bleak BLEDevice
        try:
            uuids = []
            if hasattr(ad, 'service_uuids'):
                uuids = ad.service_uuids or []
        except Exception:
            uuids = []

        devices[d.address] = {
            "name": d.name or d.address,
            "rssi": ad.rssi,
            "uuids": [u.lower() for u in uuids],
            "address": d.address,
        }

    _LOGGER.debug("BLE scan found %d devices", len(devices))
    return devices
