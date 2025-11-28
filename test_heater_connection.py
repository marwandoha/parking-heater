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
    "ffe1": "0000ffe1-0000-1000-8000-00805f9b34fb",  # Auth and Command Write
    "ffe4": "0000ffe4-0000-1000-8000-00805f9b34fb",  # Notification
}
# Discovered correct UUIDs for auth
COMMAND_WRITE_UUID = CHAR_UUIDS["ffe1"]
NOTIFY_UUID = CHAR_UUIDS["ffe4"]

# --- Command Builder ---
def build_command(command: int, data: int, passkey: str = "1234") -> bytearray:
    """Builds the command payload based on reverse-engineered protocol."""
    payload = bytearray(8)
    payload[0] = 0xAA
    payload[1] = 0x55
    payload[2] = int(passkey) // 100
    payload[3] = int(passkey) % 100
    payload[4] = command
    payload[5] = data & 0xFF
    payload[6] = (data >> 8) & 0xFF
    
    checksum = sum(payload[2:7])
    payload[7] = checksum & 0xFF
    
    return payload

# --- Predefined Commands ---
CMD_POWER_ON = build_command(3, 1, PASSWORD)
CMD_POWER_OFF = build_command(3, 0, PASSWORD)
CMD_GET_STATUS = build_command(1, 0, PASSWORD)


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
            _LOGGER.info(f"Writing '{PASSWORD}' to {COMMAND_WRITE_UUID}")
            await self.client.write_gatt_char(COMMAND_WRITE_UUID, password_cmd, response=True)

            _LOGGER.info(f"Starting notifications on {NOTIFY_UUID}")
            await self.client.start_notify(NOTIFY_UUID, self.notification_handler)

            self.is_authenticated = True
            _LOGGER.info("✅ Authentication Successful! Notification channel is open.")

        except Exception as e:
            _LOGGER.error(f"Authentication failed: {e}", exc_info=True)
            self.is_authenticated = False

    async def send_command(self, cmd: bytes, cmd_name: str, expect_response: bool = True):
        """
        Send a command to the heater.
        """
        if not self.is_authenticated:
            _LOGGER.warning("Not authenticated. Please authenticate first.")
            return

        _LOGGER.info(f"\n>>> Sending command: {cmd_name} <<<")
        _LOGGER.info(f"  Payload: {cmd.hex()}")

        try:
            # Clear notification queue before sending
            while not self.notification_queue.empty():
                self.notification_queue.get_nowait()

            await self.client.write_gatt_char(COMMAND_WRITE_UUID, cmd, response=True)
            
            if expect_response:
                _LOGGER.info("  Command sent. Waiting 5s for a notification...")
                response = await asyncio.wait_for(self.notification_queue.get(), timeout=5.0)
                _LOGGER.info(f"  ✅ SUCCESS! Received response: {response.hex()}")

                if cmd_name == "Get Status":
                    self.parse_status_response(response)
            else:
                _LOGGER.info("  Command sent. No notification expected.")
                _LOGGER.info(f"  ✅ SUCCESS! Command '{cmd_name}' sent successfully.")

        except asyncio.TimeoutError:
            _LOGGER.warning("  No notification received.")
        except BleakError as e:
            _LOGGER.error(f"  BLEAK ERROR: {e}")
        except Exception as e:
            _LOGGER.error(f"  UNEXPECTED ERROR: {e}", exc_info=True)

    def parse_status_response(self, response: bytearray):
        """
        Parses the status response from the heater.
        Assumes the power status is in the 5th byte (index 4) of the response.
        1 means ON, 0 means OFF. (This is an assumption and needs verification).
        """
        if len(response) > 4:
            power_status_byte = response[4]
            if power_status_byte == 1:
                _LOGGER.info("  Heater Status: ON")
                return "ON"
            elif power_status_byte == 0:
                _LOGGER.info("  Heater Status: OFF")
                return "OFF"
            else:
                _LOGGER.warning(f"  Unknown power status byte: {power_status_byte}. Full response: {response.hex()}")
                return "UNKNOWN"
        else:
            _LOGGER.warning(f"  Status response too short to parse power state. Full response: {response.hex()}")
            return "UNKNOWN"

    async def menu(self):
        """Display the interactive main menu."""
        while True:
            print("\n--- Main Menu ---")
            status = f"Status: {'Connected' if self.client and self.client.is_connected else 'Disconnected'}"
            status += f" | {'Authenticated' if self.is_authenticated else 'Not Authenticated'}"
            print(status)
            print("1. Connect | 2. Authenticate | 3. Send Command | 4. Disconnect | 5. Exit")
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
                    if name == "Power On":
                        await self.send_command(cmd, name, expect_response=False)
                    else:
                        await self.send_command(cmd, name)
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