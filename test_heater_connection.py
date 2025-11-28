"""
Standalone test script for debugging parking heater BLE connection.
Run this directly with Python to test connection without Home Assistant.

Usage:
    python test_heater_connection.py
"""

import asyncio
import logging
from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError

# Configuration
HEATER_MAC = "E0:4E:7A:AD:EA:5D"  # First heater - using one already connected
BLUETOOTH_ADAPTER = "hci0"  # E4:5F:01:9B:D0:AF
PASSWORD = "1234"

# BLE UUIDs (confirmed from scan)
SERVICE_UUIDS = [
    "0000ffe0-0000-1000-8000-00805f9b34fb",  # Confirmed
]

WRITE_CHAR_UUIDS = [
    "0000ffe1-0000-1000-8000-00805f9b34fb",  # Confirmed (read/write/notify)
    "0000ffe3-0000-1000-8000-00805f9b34fb",  # Alternative write
]

NOTIFY_CHAR_UUIDS = [
    "0000ffe1-0000-1000-8000-00805f9b34fb",  # Confirmed (read/write/notify) 
    "0000ffe4-0000-1000-8000-00805f9b34fb",  # Alternative notify
]

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
_LOGGER = logging.getLogger(__name__)


class HeaterTester:
    def __init__(self, mac_address: str, adapter: str = "hci1"):
        self.mac_address = mac_address
        self.adapter = adapter
        self.client = None
        self.notification_received = asyncio.Event()
        self.last_notification = None
        
    def notification_handler(self, sender, data):
        """Handle BLE notifications."""
        _LOGGER.info(f"\U0001f6a9 Notification from {sender}: {data.hex()}")
        self.last_notification = data
        self.notification_received.set()
    
    async def scan_for_device(self):
        """Scan for the heater device."""
        _LOGGER.info("\U0001f50d Scanning for devices...")
        
        try:
            devices = await BleakScanner.discover(adapter=self.adapter, timeout=10.0)
            
            _LOGGER.info(f"\n\U0001f4e1 Found {len(devices)} devices:")
            found = False
            for device in devices:
                _LOGGER.info(f"  - {device.name or 'Unknown'}: {device.address}")
                if device.address.upper() == self.mac_address.upper():
                    _LOGGER.info(f"  \U0001f603 Found our heater: {device.name}")
                    found = True
            
            if not found:
                _LOGGER.warning(f"\U0001f6a7 Heater with MAC {self.mac_address} not found.")
            return found
        except BleakError as e:
            _LOGGER.error(f"\U0001f6a7 BleakError during scan: {e}")
            return False

    async def connect(self):
        if self.client and self.client.is_connected:
            _LOGGER.warning("Already connected.")
            return True
        
        _LOGGER.info(f"\U0001f501 Connecting to {self.mac_address}...")
        try:
            self.client = BleakClient(
                self.mac_address,
                adapter=self.adapter,
                timeout=20.0
            )
            await self.client.connect()
            _LOGGER.info("\U0001f603 Connected!")
            return True
        except Exception as e:
            _LOGGER.error(f"\U0001f6a7 Connection failed: {e}")
            self.client = None
            return False

    async def disconnect(self):
        if not self.client or not self.client.is_connected:
            _LOGGER.warning("Not connected.")
            return
        
        await self.client.disconnect()
        _LOGGER.info("\U0001f501 Disconnected.")
        self.client = None

    async def discover_services(self):
        """Discover all services and characteristics."""
        if not self.client or not self.client.is_connected:
            _LOGGER.warning("Not connected. Please connect first.")
            return

        _LOGGER.info("\n\U0001f4cb Discovering services and characteristics...")
        for service in self.client.services:
            _LOGGER.info(f"\n\U0001f6a7 Service: {service.uuid} ({service.description})")
            for char in service.characteristics:
                _LOGGER.info(f"  - \U0001f4dd Char: {char.uuid} ({char.description})")
                _LOGGER.info(f"     Properties: {', '.join(char.properties)}")

    async def test_password_auth(self):
        """Test password authentication."""
        if not self.client or not self.client.is_connected:
            _LOGGER.warning("Not connected. Please connect first.")
            return
        
        write_uuid = next((u for u in WRITE_CHAR_UUIDS if u in [c.uuid for s in self.client.services for c in s.characteristics]), None)
        notify_uuid = next((u for u in NOTIFY_CHAR_UUIDS if u in [c.uuid for s in self.client.services for c in s.characteristics]), None)

        if not write_uuid or not notify_uuid:
            _LOGGER.error("\U0001f6a7 Could not find required write/notify characteristics!")
            return

        _LOGGER.info(f"\n\U0001f510 Testing password authentication...")
        _LOGGER.info(f"   Write UUID: {write_uuid}")
        _LOGGER.info(f"   Notify UUID: {notify_uuid}")
        
        try:
            await self.client.start_notify(notify_uuid, self.notification_handler)
            _LOGGER.info("\U0001f603 Subscribed to notifications")
            
            password_cmd = PASSWORD.encode('ascii')
            
            _LOGGER.info(f"\U0001f511 Sending password: {password_cmd.hex()}")
            self.notification_received.clear()
            
            await self.client.write_gatt_char(write_uuid, password_cmd, response=False)
            
            try:
                await asyncio.wait_for(self.notification_received.wait(), timeout=5.0)
                _LOGGER.info(f"\U0001f603 Got response to password! Auth likely successful.")
            except asyncio.TimeoutError:
                _LOGGER.warning(f"\U0001f550 No response to password command.")
            
            await self.client.stop_notify(notify_uuid)

        except Exception as e:
            _LOGGER.error(f"\U0001f6a7 Password auth failed: {e}")

    async def send_command(self):
        if not self.client or not self.client.is_connected:
            _LOGGER.warning("Not connected. Please connect first.")
            return

        write_uuid = next((u for u in WRITE_CHAR_UUIDS if u in [c.uuid for s in self.client.services for c in s.characteristics]), None)
        notify_uuid = next((u for u in NOTIFY_CHAR_UUIDS if u in [c.uuid for s in self.client.services for c in s.characteristics]), None)

        if not write_uuid or not notify_uuid:
            _LOGGER.error("\U0001f6a7 Could not find required write/notify characteristics!")
            return

        _LOGGER.info("Enter command to send in hex format (e.g., 76170100000000008E):")
        hex_cmd = await asyncio.get_event_loop().run_in_executor(None, input, "> ")
        try:
            cmd = bytes.fromhex(hex_cmd)
        except ValueError:
            _LOGGER.error("Invalid hex string.")
            return

        _LOGGER.info(f"\n\U0001f4e1 Sending: {cmd.hex()}")
        try:
            await self.client.start_notify(notify_uuid, self.notification_handler)
            self.notification_received.clear()
            
            await self.client.write_gatt_char(write_uuid, cmd, response=False)
            
            try:
                await asyncio.wait_for(self.notification_received.wait(), timeout=5.0)
                _LOGGER.info(f"\U0001f603 Response received!")
            except asyncio.TimeoutError:
                _LOGGER.warning(f"\U0001f550 No response received.")
            
            await self.client.stop_notify(notify_uuid)
        except Exception as e:
            _LOGGER.error(f"\U0001f6a7 Send failed: {e}")


async def main():
    """Main interactive test function."""
    _LOGGER.info("="*60)
    _LOGGER.info("🚗 Parking Heater BLE Interactive Tester")
    _LOGGER.info(f"Heater MAC: {HEATER_MAC} | Adapter: {BLUETOOTH_ADAPTER}")
    _LOGGER.info("="*60)
    
    tester = HeaterTester(HEATER_MAC, BLUETOOTH_ADAPTER)
    
    while True:
        print("\n--- Menu ---")
        print("1. Scan for heater")
        print("2. Connect to heater")
        print("3. Discover services")
        print("4. Test password authentication")
        print("5. Send custom command")
        print("6. Disconnect")
        print("7. Exit")
        
        choice = await asyncio.get_event_loop().run_in_executor(None, input, "Enter your choice: ")

        if choice == '1':
            await tester.scan_for_device()
        elif choice == '2':
            await tester.connect()
        elif choice == '3':
            await tester.discover_services()
        elif choice == '4':
            await tester.test_password_auth()
        elif choice == '5':
            await tester.send_command()
        elif choice == '6':
            await tester.disconnect()
        elif choice == '7':
            await tester.disconnect()
            break
        else:
            _LOGGER.warning("Invalid choice, please try again.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        _LOGGER.info("\nExiting...")