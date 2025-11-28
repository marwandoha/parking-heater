"""
Simple BLE scanner to find your heater and check Bluetooth setup.
Run this first to diagnose connection issues.
"""

import asyncio
import logging
from bleak import BleakScanner

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
_LOGGER = logging.getLogger(__name__)

HEATER_MAC = "E0:4E:7A:AD:EA:5D"
BLUETOOTH_ADAPTER = "hci1"


async def scan_bluetooth():
    """Scan for BLE devices."""
    _LOGGER.info("="*60)
    _LOGGER.info("🔍 Bluetooth Scanner - Diagnostic Tool")
    _LOGGER.info("="*60)
    _LOGGER.info(f"Looking for heater: {HEATER_MAC}")
    _LOGGER.info(f"Using adapter: {BLUETOOTH_ADAPTER}")
    _LOGGER.info("")
    _LOGGER.info("🔍 Scanning for 15 seconds...")
    _LOGGER.info("")
    
    try:
        # Scan with specific adapter
        devices = await BleakScanner.discover(
            adapter=BLUETOOTH_ADAPTER,
            timeout=15.0,
            return_adv=True
        )
        
        _LOGGER.info(f"📡 Found {len(devices)} devices:")
        _LOGGER.info("")
        
        heater_found = False
        
        for address, (device, adv_data) in devices.items():
            name = device.name or "Unknown"
            rssi = adv_data.rssi if hasattr(adv_data, 'rssi') else "N/A"
            
            # Check if this is our heater
            is_our_heater = address.upper() == HEATER_MAC.upper()
            
            if is_our_heater:
                _LOGGER.info("="*60)
                _LOGGER.info(f"✅ FOUND YOUR HEATER!")
                _LOGGER.info("="*60)
                heater_found = True
            
            _LOGGER.info(f"{'🎯' if is_our_heater else '📱'} Device: {name}")
            _LOGGER.info(f"   Address: {address}")
            _LOGGER.info(f"   RSSI: {rssi} dBm")
            
            if hasattr(adv_data, 'service_uuids') and adv_data.service_uuids:
                _LOGGER.info(f"   Services: {adv_data.service_uuids}")
            
            if hasattr(adv_data, 'manufacturer_data') and adv_data.manufacturer_data:
                _LOGGER.info(f"   Manufacturer: {adv_data.manufacturer_data}")
            
            _LOGGER.info("")
            
            if is_our_heater:
                _LOGGER.info("="*60)
        
        _LOGGER.info("")
        _LOGGER.info("="*60)
        
        if heater_found:
            _LOGGER.info("✅ Your heater is visible and advertising!")
            _LOGGER.info("   The connection timeout might be due to:")
            _LOGGER.info("   1. Heater is paired with another device (phone app)")
            _LOGGER.info("   2. Heater requires password before connection")
            _LOGGER.info("   3. Heater is too far (check RSSI, should be > -80)")
            _LOGGER.info("   4. Bluetooth interference")
        else:
            _LOGGER.info("❌ Your heater was NOT found!")
            _LOGGER.info("   Troubleshooting:")
            _LOGGER.info("   1. Is the heater powered ON?")
            _LOGGER.info("   2. Is the MAC address correct?")
            _LOGGER.info("   3. Is the heater in range?")
            _LOGGER.info("   4. Try scanning with phone app to confirm it works")
        
        _LOGGER.info("="*60)
        
    except Exception as e:
        _LOGGER.error(f"❌ Scan failed: {e}", exc_info=True)


async def check_adapter():
    """Check if the Bluetooth adapter is available."""
    _LOGGER.info("🔧 Checking Bluetooth adapter...")
    
    try:
        # Try scanning with default adapter
        devices_default = await BleakScanner.discover(timeout=2.0)
        _LOGGER.info(f"✅ Default adapter works ({len(devices_default)} devices)")
    except Exception as e:
        _LOGGER.error(f"❌ Default adapter issue: {e}")
    
    try:
        # Try scanning with hci1
        devices_hci1 = await BleakScanner.discover(adapter=BLUETOOTH_ADAPTER, timeout=2.0)
        _LOGGER.info(f"✅ {BLUETOOTH_ADAPTER} works ({len(devices_hci1)} devices)")
    except Exception as e:
        _LOGGER.error(f"❌ {BLUETOOTH_ADAPTER} issue: {e}")
        _LOGGER.info("💡 Try using default adapter (remove adapter parameter)")
    
    _LOGGER.info("")


async def main():
    """Main function."""
    await check_adapter()
    await scan_bluetooth()


if __name__ == "__main__":
    asyncio.run(main())
