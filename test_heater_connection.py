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
    "ffe1": "0000ffe1-0000-1000-8000-00805f9b34fb",  # Auth, Command Write, and Notification
}
# Discovered correct UUIDs for auth
COMMAND_WRITE_UUID = CHAR_UUIDS["ffe1"]
NOTIFY_UUID = CHAR_UUIDS["ffe1"]

# --- Predefined Commands ---
CMD_POWER_ON_CMD_TYPE = 0x16
CMD_POWER_OFF_CMD_TYPE = 0x16
CMD_GET_STATUS_CMD_TYPE = 0x17


# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
_LOGGER = logging.getLogger(__name__)


class HeaterCommander:
    def __init__(self, mac_address: str, adapter: str):
        self.mac_address = mac_address
        self.adapter = adapter
        self.client = None
        self.is_authenticated = False
        self.notification_queue = asyncio.Queue() # Keep for auth if it relies on queue
        self._notification_data = bytearray()
        self._notification_event = asyncio.Event()

    def notification_handler(self, sender, data):
        """Handle BLE notifications and set event."""
        _LOGGER.info(f"[RECV] Notification from {sender}: {data.hex()}")
        self._notification_data = data
        self._notification_event.set()

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
        Send a command to the heater and optionally wait for a response notification.
        """
        if not self.is_authenticated:
            _LOGGER.warning("Not authenticated. Please authenticate first.")
            return

        _LOGGER.info(f"\n>>> Sending command: {cmd_name} <<<")
        _LOGGER.info(f"  Payload: {cmd.hex()}")

        self._notification_event.clear()
        self._notification_data = bytearray()

        try:
            await self.client.write_gatt_char(COMMAND_WRITE_UUID, cmd, response=False)
            
            if expect_response:
                _LOGGER.info("  Command sent. Waiting 5s for a notification...")
                try:
                    await asyncio.wait_for(self._notification_event.wait(), timeout=5.0)
                    response = self._notification_data
                    _LOGGER.info(f"  ✅ SUCCESS! Received response: {response.hex()}")

                    if cmd_name == "Get Status":
                        self.parse_status_response(response)
                except asyncio.TimeoutError:
                    _LOGGER.warning("  No notification received within the timeout.")
                    response = bytearray()
            else:
                _LOGGER.info("  Command sent. No notification expected.")
                _LOGGER.info(f"  ✅ SUCCESS! Command '{cmd_name}' sent successfully.")
                response = bytearray() # No response expected, so set to empty

            return response

        except BleakError as e:
            _LOGGER.error(f"  BLEAK ERROR: {e}")
            return bytearray()
        except Exception as e:
            _LOGGER.error(f"  UNEXPECTED ERROR: {e}", exc_info=True)
            return bytearray()

    def parse_status_response(self, response: bytearray):
        """
        Parses the status response from the heater.
        Heater's on/off status is extracted from the 4th byte (index 3) of this response.
        0x01 means ON, 0x00 means OFF.
        Other status: target_temperature (index 4), current_temperature (index 5),
        fan_speed (index 6), and error_code (index 7).
        """
        if len(response) > 7: # Ensure all expected bytes are present
            power_status_byte = response[3]
            heater_status = "UNKNOWN"
            if power_status_byte == 0x01:
                heater_status = "ON"
            elif power_status_byte == 0x00:
                heater_status = "OFF"
            
            target_temperature = response[4]
            current_temperature = response[5]
            fan_speed = response[6]
            error_code = response[7]

            _LOGGER.info(f"  Heater Status: {heater_status}")
            _LOGGER.info(f"  Target Temperature: {target_temperature}°C")
            _LOGGER.info(f"  Current Temperature: {current_temperature}°C")
            _LOGGER.info(f"  Fan Speed: {fan_speed}")
            _LOGGER.info(f"  Error Code: {error_code}")
            return heater_status
        else:
            _LOGGER.warning(f"  Status response too short to parse all states. Expected at least 8 bytes, got {len(response)}. Full response: {response.hex()}")
            return "UNKNOWN"

    def _calculate_checksum(self, data: bytes) -> int:
        """Calculate checksum for command."""
        return sum(data) & 0xFF

    def _build_command(self, cmd_type: int, data: bytes = b"") -> bytes:
        """Build a command with checksum."""
        # Command format: [0x76, cmd_type, length, data..., checksum]
        length = len(data)
        command = bytes([0x76, cmd_type, length]) + data
        checksum = self._calculate_checksum(command)
        return command + bytes([checksum])

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
                if cmd_choice == '1': 
                    cmd = self._build_command(CMD_POWER_ON_CMD_TYPE, bytes([0x01]))
                    name = "Power On"
                elif cmd_choice == '2': 
                    cmd = self._build_command(CMD_POWER_OFF_CMD_TYPE, bytes([0x00]))
                    name = "Power Off"
                elif cmd_choice == '3': 
                    cmd = self._build_command(CMD_GET_STATUS_CMD_TYPE)
                    name = "Get Status"
                
                if cmd:
                    if name == "Power On" or name == "Power Off": # Power commands do not expect a notification response
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