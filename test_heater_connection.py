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
HEATER_MAC = "E0:4E:7A:AD:EA:5D"
BLUETOOTH_ADAPTER = "hci0"
PASSWORD = "1234"

# --- UUIDs discovered from user's device scan ---
SERVICE_UUID = "0000ffe0-0000-1000-8000-00805f9b34fb"
CHAR_UUIDS = {
    "ffe1": "0000ffe1-0000-1000-8000-00805f9b34fb",  # supports read, write, notify
    "ffe3": "0000ffe3-0000-1000-8000-00805f9b34fb",  # supports write
    "ffe4": "0000ffe4-0000-1000-8000-00805f9b34fb",  # supports notify
}
# --- End of UUIDs ---

# Command bytes
CMD_POWER_ON = bytes([0x76, 0x16, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x8E])
CMD_POWER_OFF = bytes([0x76, 0x16, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x8D])
CMD_GET_STATUS = bytes([0x76, 0x17, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x8E])

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
_LOGGER = logging.getLogger(__name__)


class HeaterTester:
    def __init__(self, mac_address: str, adapter: str):
        self.mac_address = mac_address
        self.adapter = adapter
        self.client = None
        self.notification_received = asyncio.Event()
        self.last_notification = None
        self.write_uuid = CHAR_UUIDS["ffe1"]
        self.notify_uuid = CHAR_UUIDS["ffe1"]
        self.is_authenticated = False
        
    def notification_handler(self, sender, data):
        """Handle BLE notifications."""
        _LOGGER.info(f"📨 Notification from {sender}: {data.hex()}")
        self.last_notification = data
        self.notification_received.set()
    
    async def scan_for_device(self):
        _LOGGER.info("🔍 Scanning for devices...")
        try:
            devices = await BleakScanner.discover(adapter=self.adapter, timeout=10.0)
            _LOGGER.info(f"\n📡 Found {len(devices)} devices:")
            found = any(d.address.upper() == self.mac_address.upper() for d in devices)
            for device in devices:
                _LOGGER.info(f"  - {device.name or 'Unknown'}: {device.address} {'✅' if device.address.upper() == self.mac_address.upper() else ''}")
            if not found:
                _LOGGER.warning(f"⚠️ Heater with MAC {self.mac_address} not found.")
        except BleakError as e:
            _LOGGER.error(f"❌ BleakError during scan: {e}")

    async def connect(self):
        if self.client and self.client.is_connected:
            _LOGGER.warning("Already connected.")
            return
        _LOGGER.info(f"🔌 Connecting to {self.mac_address}...")
        try:
            self.client = BleakClient(self.mac_address, adapter=self.adapter, timeout=20.0)
            await self.client.connect()
            _LOGGER.info("✅ Connected!")
            self.is_authenticated = False # Reset auth status on new connection
        except Exception as e:
            _LOGGER.error(f"❌ Connection failed: {e}")
            self.client = None

    async def disconnect(self):
        if not self.client or not self.client.is_connected:
            _LOGGER.warning("Not connected.")
            return
        await self.client.disconnect()
        _LOGGER.info("🔌 Disconnected.")
        self.client = None
        self.is_authenticated = False

    async def discover_services(self):
        if not self.client or not self.client.is_connected:
            _LOGGER.warning("Not connected. Please connect first.")
            return
        _LOGGER.info("\n📋 Discovering services and characteristics...")
        for service in self.client.services:
            _LOGGER.info(f"\n🔧 Service: {service.uuid} ({service.description})")
            for char in service.characteristics:
                _LOGGER.info(f"  - 📝 Char: {char.uuid} ({char.description}) | Properties: {', '.join(char.properties)}")

    async def select_characteristics(self):
        print("\n--- Select Characteristics ---")
        print("Available Write Characteristics: ffe1 (rw), ffe3 (w)")
        write_choice = await asyncio.get_event_loop().run_in_executor(None, input, "Choose write characteristic (ffe1/ffe3): ")
        if write_choice in CHAR_UUIDS:
            self.write_uuid = CHAR_UUIDS[write_choice]
            _LOGGER.info(f"Write characteristic set to {self.write_uuid}")
        else:
            _LOGGER.warning("Invalid choice. Keeping existing value.")

        print("\nAvailable Notify Characteristics: ffe1 (rn), ffe4 (n)")
        notify_choice = await asyncio.get_event_loop().run_in_executor(None, input, "Choose notify characteristic (ffe1/ffe4): ")
        if notify_choice in CHAR_UUIDS:
            self.notify_uuid = CHAR_UUIDS[notify_choice]
            _LOGGER.info(f"Notify characteristic set to {self.notify_uuid}")
        else:
            _LOGGER.warning("Invalid choice. Keeping existing value.")

    async def authenticate(self):
        """Send the password to the device."""
        if not self.client or not self.client.is_connected:
            _LOGGER.warning("Not connected. Please connect first.")
            return

        _LOGGER.info("🔐 Attempting to authenticate...")
        password_cmd = PASSWORD.encode('ascii')
        
        _LOGGER.info(f"📡 Using Write: {self.write_uuid}")
        _LOGGER.info(f"📡 Using Notify: {self.notify_uuid}")
        _LOGGER.info(f"🔑 Sending password: {password_cmd.hex()}")
        
        try:
            self.notification_received.clear()
            await self.client.start_notify(self.notify_uuid, self.notification_handler)
            await self.client.write_gatt_char(self.write_uuid, password_cmd, response=False)
            
            try:
                await asyncio.wait_for(self.notification_received.wait(), timeout=5.0)
                _LOGGER.info("✅ Got a response to password. Authentication likely successful!")
                self.is_authenticated = True
            except asyncio.TimeoutError:
                _LOGGER.warning("⏱️ No response to password command. Authentication may have failed.")
                self.is_authenticated = False
            
            await self.client.stop_notify(self.notify_uuid)
        except Exception as e:
            _LOGGER.error(f"❌ Authentication failed: {e}", exc_info=True)
            self.is_authenticated = False

    async def _send_and_wait(self, cmd: bytes):
        if not self.client or not self.client.is_connected:
            _LOGGER.warning("Not connected. Please connect first.")
            return
            
        _LOGGER.info(f"📡 Using Write: {self.write_uuid}")
        _LOGGER.info(f"📡 Using Notify: {self.notify_uuid}")
        _LOGGER.info(f"📨 Sending: {cmd.hex()}")
        
        try:
            self.notification_received.clear()
            await self.client.start_notify(self.notify_uuid, self.notification_handler)
            await self.client.write_gatt_char(self.write_uuid, cmd, response=False)
            
            try:
                await asyncio.wait_for(self.notification_received.wait(), timeout=5.0)
                _LOGGER.info("✅ Response received!")
            except asyncio.TimeoutError:
                _LOGGER.warning("⏱️ No response received.")
            
            await self.client.stop_notify(self.notify_uuid)
        except Exception as e:
            _LOGGER.error(f"❌ Send failed: {e}", exc_info=True)

    async def send_predefined_command(self):
        print("\n--- Predefined Commands ---")
        print("1. Turn On | 2. Turn Off | 3. Get Status | 4. Back")
        choice = await asyncio.get_event_loop().run_in_executor(None, input, "Enter your choice: ")
        
        cmd = None
        if choice == '1': cmd = CMD_POWER_ON
        elif choice == '2': cmd = CMD_POWER_OFF
        elif choice == '3': cmd = CMD_GET_STATUS
        else: return
        
        await self._send_and_wait(cmd)

    async def send_custom_command(self):
        hex_cmd = await asyncio.get_event_loop().run_in_executor(None, input, "Enter custom hex command: ")
        try:
            cmd = bytes.fromhex(hex_cmd)
            await self._send_and_wait(cmd)
        except ValueError:
            _LOGGER.error("Invalid hex string.")

async def main():
    _LOGGER.info("="*60)
    _LOGGER.info("🚗 Parking Heater BLE Interactive Tester")
    _LOGGER.info(f"Heater MAC: {HEATER_MAC} | Adapter: {BLUETOOTH_ADAPTER}")
    _LOGGER.info("="*60)
    
    tester = HeaterTester(HEATER_MAC, BLUETOOTH_ADAPTER)
    
    while True:
        print("\n--- Main Menu ---")
        print(f"Status: {'Connected' if tester.client and tester.client.is_connected else 'Disconnected'} | {'Authenticated' if tester.is_authenticated else 'Not Authenticated'}")
        print("1. Scan | 2. Connect | 3. Discover Services | 4. Select Characteristics | 5. Authenticate | 6. Send Command | 7. Disconnect | 8. Exit")
        choice = await asyncio.get_event_loop().run_in_executor(None, input, "Enter your choice: ")

        if choice == '1': await tester.scan_for_device()
        elif choice == '2': await tester.connect()
        elif choice == '3': await tester.discover_services()
        elif choice == '4': await tester.select_characteristics()
        elif choice == '5': await tester.authenticate()
        elif choice == '6':
            print("\n--- Send Command Menu ---")
            print("1. Predefined (On/Off/Status) | 2. Custom Hex | 3. Back")
            cmd_choice = await asyncio.get_event_loop().run_in_executor(None, input, "Enter your choice: ")
            if cmd_choice == '1': await tester.send_predefined_command()
            elif cmd_choice == '2': await tester.send_custom_command()
        elif choice == '7': await tester.disconnect()
        elif choice == '8':
            if tester.client and tester.client.is_connected:
                await tester.disconnect()
            break
        else:
            _LOGGER.warning("Invalid choice, please try again.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        _LOGGER.info("\nExiting...")
