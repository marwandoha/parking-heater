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
HEATER_MAC = "E0:4E:7A:AD:E8:EE"  # Second heater on hci1
BLUETOOTH_ADAPTER = "hci1"  # F4:4E:FC:13:83:6D
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
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
        _LOGGER.info(f"📨 Notification from {sender}: {data.hex()}")
        _LOGGER.info(f"📨 Decoded: {list(data)}")
        self.last_notification = data
        self.notification_received.set()
    
    async def scan_for_device(self):
        """Scan for the heater device."""
        _LOGGER.info("🔍 Scanning for devices...")
        
        devices = await BleakScanner.discover(adapter=self.adapter, timeout=10.0)
        
        _LOGGER.info(f"\n📡 Found {len(devices)} devices:")
        for device in devices:
            _LOGGER.info(f"  - {device.name or 'Unknown'}: {device.address}")
            if device.address.upper() == self.mac_address.upper():
                _LOGGER.info(f"  ✅ Found our heater: {device.name}")
                return device
        
        return None
    
    async def discover_services(self):
        """Discover all services and characteristics."""
        _LOGGER.info(f"\n🔌 Connecting to {self.mac_address}...")
        
        try:
            self.client = BleakClient(
                self.mac_address,
                adapter=self.adapter,
                timeout=20.0
            )
            
            await self.client.connect()
            _LOGGER.info("✅ Connected!")
            
            _LOGGER.info("\n📋 Discovering services and characteristics...")
            
            for service in self.client.services:
                _LOGGER.info(f"\n🔧 Service: {service.uuid}")
                _LOGGER.info(f"   Description: {service.description}")
                
                for char in service.characteristics:
                    _LOGGER.info(f"   📝 Characteristic: {char.uuid}")
                    _LOGGER.info(f"      Properties: {char.properties}")
                    _LOGGER.info(f"      Description: {char.description}")
            
            return True
            
        except Exception as e:
            _LOGGER.error(f"❌ Connection failed: {e}")
            return False
        finally:
            if self.client and self.client.is_connected:
                await self.client.disconnect()
                _LOGGER.info("🔌 Disconnected")
    
    async def test_password_auth(self, write_uuid: str, notify_uuid: str):
        """Test password authentication."""
        _LOGGER.info(f"\n🔐 Testing password authentication...")
        _LOGGER.info(f"   Write UUID: {write_uuid}")
        _LOGGER.info(f"   Notify UUID: {notify_uuid}")
        
        try:
            # Subscribe to notifications first
            await self.client.start_notify(notify_uuid, self.notification_handler)
            _LOGGER.info("✅ Subscribed to notifications")
            
            # Try sending password
            # Common formats for password authentication
            password_commands = [
                # Format 1: Plain ASCII
                PASSWORD.encode('ascii'),
                
                # Format 2: With header
                bytes([0x76, 0x10, 0x04]) + PASSWORD.encode('ascii') + bytes([sum(bytes([0x76, 0x10, 0x04]) + PASSWORD.encode('ascii')) & 0xFF]),
                
                # Format 3: With different header
                bytes([0xAA, 0x55, 0x04]) + PASSWORD.encode('ascii'),
                
                # Format 4: Hex representation
                bytes([0x01, 0x02, 0x03, 0x04]),  # 1234 as hex
            ]
            
            for i, cmd in enumerate(password_commands):
                _LOGGER.info(f"\n🔑 Trying password format {i+1}: {cmd.hex()}")
                self.notification_received.clear()
                
                await self.client.write_gatt_char(write_uuid, cmd, response=False)
                
                # Wait for response
                try:
                    await asyncio.wait_for(self.notification_received.wait(), timeout=3.0)
                    _LOGGER.info(f"✅ Got response for format {i+1}!")
                    return True
                except asyncio.TimeoutError:
                    _LOGGER.warning(f"⏱️ No response for format {i+1}")
            
            return False
            
        except Exception as e:
            _LOGGER.error(f"❌ Password auth failed: {e}")
            return False
    
    async def test_commands(self, write_uuid: str, notify_uuid: str):
        """Test various commands."""
        _LOGGER.info(f"\n📤 Testing commands...")
        
        # Common command formats
        commands = {
            "Get Status": bytes([0x76, 0x17, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x8E]),
            "Get Status Alt": bytes([0x76, 0x01, 0x00, 0x77]),
            "Power Query": bytes([0x76, 0x10, 0x00, 0x86]),
        }
        
        for name, cmd in commands.items():
            _LOGGER.info(f"\n📨 Sending: {name}")
            _LOGGER.info(f"   Command: {cmd.hex()}")
            
            self.notification_received.clear()
            self.last_notification = None
            
            try:
                await self.client.write_gatt_char(write_uuid, cmd, response=False)
                
                # Wait for response
                try:
                    await asyncio.wait_for(self.notification_received.wait(), timeout=3.0)
                    _LOGGER.info(f"✅ Response received!")
                except asyncio.TimeoutError:
                    _LOGGER.warning(f"⏱️ No response")
            except Exception as e:
                _LOGGER.error(f"❌ Send failed: {e}")
    
    async def full_test(self):
        """Run full connection test."""
        _LOGGER.info("="*60)
        _LOGGER.info("🚗 Parking Heater BLE Connection Tester")
        _LOGGER.info("="*60)
        _LOGGER.info(f"Heater MAC: {self.mac_address}")
        _LOGGER.info(f"Adapter: {self.adapter}")
        _LOGGER.info(f"Password: {PASSWORD}")
        _LOGGER.info("="*60)
        
        # Step 1: Scan for device
        device = await self.scan_for_device()
        if not device:
            _LOGGER.error("❌ Device not found!")
            return
        
        # Step 2: Discover services
        _LOGGER.info(f"\n🔌 Connecting to {self.mac_address}...")
        
        try:
            self.client = BleakClient(
                self.mac_address,
                adapter=self.adapter,
                timeout=20.0
            )
            
            await self.client.connect()
            _LOGGER.info("✅ Connected!")
            
            # Discover services
            await asyncio.sleep(1)
            
            _LOGGER.info("\n📋 Available Services:")
            for service in self.client.services:
                _LOGGER.info(f"\n🔧 Service: {service.uuid}")
                for char in service.characteristics:
                    _LOGGER.info(f"   📝 Char: {char.uuid} - Properties: {char.properties}")
            
            # Step 3: Find write and notify characteristics
            write_char = None
            notify_char = None
            
            for service in self.client.services:
                for char in service.characteristics:
                    if "write" in char.properties:
                        write_char = char.uuid
                        _LOGGER.info(f"✅ Found WRITE characteristic: {write_char}")
                    if "notify" in char.properties:
                        notify_char = char.uuid
                        _LOGGER.info(f"✅ Found NOTIFY characteristic: {notify_char}")
            
            if not write_char or not notify_char:
                _LOGGER.error("❌ Could not find required characteristics!")
                return
            
            # Step 4: Test password authentication
            auth_success = await self.test_password_auth(write_char, notify_char)
            
            if auth_success:
                _LOGGER.info("\n✅ Password authentication successful!")
            else:
                _LOGGER.warning("\n⚠️ Password authentication unclear, trying commands anyway...")
            
            # Step 5: Test commands
            await self.test_commands(write_char, notify_char)
            
            # Keep connection open for a bit
            _LOGGER.info("\n⏱️ Keeping connection open for 10 seconds...")
            await asyncio.sleep(10)
            
        except Exception as e:
            _LOGGER.error(f"❌ Test failed: {e}", exc_info=True)
        finally:
            if self.client and self.client.is_connected:
                await self.client.disconnect()
                _LOGGER.info("\n🔌 Disconnected")
        
        _LOGGER.info("\n" + "="*60)
        _LOGGER.info("✅ Test completed!")
        _LOGGER.info("="*60)


async def main():
    """Main test function."""
    tester = HeaterTester(HEATER_MAC, BLUETOOTH_ADAPTER)
    await tester.full_test()


if __name__ == "__main__":
    asyncio.run(main())
