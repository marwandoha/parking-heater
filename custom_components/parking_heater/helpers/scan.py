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

    scanner = BleakScanner()
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

    for d in await scanner.get_discovered_devices():
        # bleak BLEDevice
        try:
            uuids = []
            if hasattr(d, 'metadata') and d.metadata:
                uuids = d.metadata.get('uuids', []) or []
        except Exception:
            uuids = []

        devices[d.address] = {
            "name": d.name or d.address,
            "rssi": d.rssi,
            "uuids": [u.lower() for u in uuids],
            "address": d.address,
        }

    _LOGGER.debug("BLE scan found %d devices", len(devices))
    return devices
