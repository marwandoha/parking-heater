"""
Standalone test script for parking heater BLE connection.
This version uses the discovered authentication method and now focuses on
finding the correct way to send commands.
"""

import asyncio
import logging
from bleak import BleakClient, BleakError

# --- Configuration ---
HEATER_MAC = "E0:4E:7A:AD:EA:5D"
BLUETOOTH_ADAPTER = "hci0"
PASSWORD = "1234"

# --- UUIDs ---
# Service UUID
SERVICE_UUID = "0000ffe0-0000-1000-8000-00805f9b34fb"
# All known characteristics
CHAR_UUIDS = {
    "ffe1": "0000ffe1-0000-1000-8000-00805f9b34fb",  # Auth Write
    "ffe3": "0000ffe3-0000-1000-8000-00805f9b34fb",  # Possible Command Write?
    "ffe4": "0000ffe4-0000-1000-8000-00805f9b34fb",  # Notification
}
# Discovered correct UUIDs for auth
AUTH_WRITE_UUID = CHAR_UUIDS["ffe1"]
NOTIFY_UUID = CHAR_UUIDS["ffe4"]

# --- Predefined Commands ---
CMD_POWER_ON = bytes.fromhex("76160101000000008e")
CMD_POWER_OFF = bytes.fromhex("76160100000000008d")
CMD_GET_STATUS = bytes.fromhex("76170100000000008e")

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
_LOGGER = logging.getLogger(__name__)


class HeaterCommander:
    def __init__(self, mac_address: str, adapter: str):
        self.mac_address = mac_address
        self.adapter = adapter
        self.client = None
        self.is_authenticated = False
        self.notification_queue = asyncio.Queue()

    def notification_handler(self, sender, data):
        """Handle BLE notifications and put them in a queue."""
        _LOGGER.info(f"[RECV] Notification from {sender}: {data.hex()}")
        self.notification_queue.put_nowait(data)

    async def connect(self):
        """Connect to the heater."""
        if self.client and self.client.is_connected:
            _LOGGER.warning("Already connected.")
            return
        _LOGGER.info(f"Connecting to {self.mac_address}...")
        try:
            self.client = BleakClient(self.mac_address, adapter=self.adapter, timeout=20.0)
            await self.client.connect()
            _LOGGER.info("Connected successfully!")
            self.is_authenticated = False
        except Exception as e:
            _LOGGER.error(f"Connection failed: {e}")
            self.client = None

    async def disconnect(self):
        """Disconnect from the heater."""
        if not self.client or not self.client.is_connected:
            _LOGGER.warning("Not connected.")
            return
        await self.client.disconnect()
        _LOGGER.info("Disconnected.")
        self.client = None
        self.is_authenticated = False

    async def authenticate(self):
        """Authenticate using the discovered correct method."""
        if self.is_authenticated:
            _LOGGER.info("Already authenticated.")
            return
        if not self.client or not self.client.is_connected:
            _LOGGER.error("Not connected. Please connect first.")
            return

        _LOGGER.info("Attempting authentication with the known correct method...")
        password_cmd = PASSWORD.encode('ascii')

        try:
            _LOGGER.info(f"Writing '{PASSWORD}' to {AUTH_WRITE_UUID}")
            await self.client.write_gatt_char(AUTH_WRITE_UUID, password_cmd, response=True)

            _LOGGER.info(f"Starting notifications on {NOTIFY_UUID}")
            await self.client.start_notify(NOTIFY_UUID, self.notification_handler)
            
            self.is_authenticated = True
            _LOGGER.info("✅ Authentication Successful! Notification channel is open.")

        except Exception as e:
            _LOGGER.error(f"Authentication failed: {e}", exc_info=True)
            self.is_authenticated = False

    async def send_command_exploratory(self, base_cmd: bytes, cmd_name: str):
        """
        Send a command by exploring different write UUIDs and padding lengths.
        """
        if not self.is_authenticated:
            _LOGGER.warning("Not authenticated. Please authenticate first.")
            return

        _LOGGER.info(f"\n>>> Starting exploratory send for command: {cmd_name} <<<
")

        write_uuids_to_try = [CHAR_UUIDS["ffe1"], CHAR_UUIDS["ffe3"]]
        padding_lengths_to_try = [None, 8, 16, 20] # None = no padding

        for write_uuid in write_uuids_to_try:
            for length in padding_lengths_to_try:
                cmd = base_cmd if length is None else base_cmd.ljust(length, b'\x00')

                _LOGGER.info(f"--- Testing Write UUID: {write_uuid}, Length: {length or 'raw'} ---")
                _LOGGER.info(f"  Payload: {cmd.hex()}")

                try:
                    # Clear notification queue before sending
                    while not self.notification_queue.empty():
                        self.notification_queue.get_nowait()

                    await self.client.write_gatt_char(write_uuid, cmd, response=False)
                    
                    _LOGGER.info("  Command sent. Waiting 5s for a notification...")
                    response = await asyncio.wait_for(self.notification_queue.get(), timeout=5.0)
                    
                    _LOGGER.info(f"  ✅ SUCCESS! Received response: {response.hex()}")
                    _LOGGER.info(f"  Correct combination for '{cmd_name}' is likely: Write UUID={write_uuid}, Length={length}")
                    return # Stop on first success

                except asyncio.TimeoutError:
                    _LOGGER.warning("  No notification received.")
                except BleakError as e:
                    _LOGGER.error(f"  BLEAK ERROR: {e}")
                    if "Invalid Length" in str(e):
                        _LOGGER.warning("  --> Rejected by bluetoothd. Incorrect length for this characteristic.")
                except Exception as e:
                    _LOGGER.error(f"  UNEXPECTED ERROR: {e}", exc_info=True)

    async def menu(self):
        """Display the interactive main menu."""
        while True:
            print("\n--- Main Menu ---")
            status = f"Status: {'Connected' if self.client and self.client.is_connected else 'Disconnected'}"
            status += f" | {'Authenticated' if self.is_authenticated else 'Not Authenticated'}"
            print(status)
            print("1. Connect | 2. Authenticate | 3. Send Command (Exploratory) | 4. Disconnect | 5. Exit")
            choice = await asyncio.get_event_loop().run_in_executor(None, input, "Enter your choice: ")

            if choice == '1':
                await self.connect()
            elif choice == '2':
                await self.authenticate()
            elif choice == '3':
                print("\n--- Select Command to Send ---")
                print("1. Turn On | 2. Turn Off | 3. Get Status")
                cmd_choice = await asyncio.get_event_loop().run_in_executor(None, input, "Enter your choice: ")
                cmd, name = None, None
                if cmd_choice == '1': cmd, name = CMD_POWER_ON, "Power On"
                elif cmd_choice == '2': cmd, name = CMD_POWER_OFF, "Power Off"
                elif cmd_choice == '3': cmd, name = CMD_GET_STATUS, "Get Status"
                
                if cmd:
                    await self.send_command_exploratory(cmd, name)
            elif choice == '4':
                await self.disconnect()
            elif choice == '5':
                if self.client and self.client.is_connected:
                    await self.disconnect()
                break
            else:
                _LOGGER.warning("Invalid choice.")


async def main():
    _LOGGER.info("="*50)
    _LOGGER.info("Parking Heater BLE Commander")
    _LOGGER.info("="*50)
    
    commander = HeaterCommander(HEATER_MAC, BLUETOOTH_ADAPTER)
    await commander.menu()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        _LOGGER.info("\nExiting...")
