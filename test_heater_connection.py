"""
Standalone test script for parking heater BLE connection.
This version uses the discovered authentication method and now focuses on
finding the correct way to send commands.
"""

import asyncio
import logging
from bleak import BleakClient, BleakError, BleakScanner

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
NOTIFY_UUID = CHAR_UUIDS["ffe1"]  # APK uses FFE1 for both write and notify

# --- Command Builder ---
def build_command(command: int, data: int, mode: int = 0x55, passkey: str = "1234") -> bytearray:
    """
    Builds the command payload.
    Mode 0x55 (85): Standard command with password.
    Mode 0x88 (136): Handshake/Random confirmation.
    """
    payload = bytearray(8)
    payload[0] = 0xAA
    payload[1] = mode

    if mode == 0x88: # 136
        # Use random bytes for handshake
        import random
        payload[2] = random.randint(0, 255)
        payload[3] = random.randint(0, 255)
    else:
        # Use password for standard commands
        try:
            pk = int(passkey)
            payload[2] = pk // 100
            payload[3] = pk % 100
        except ValueError:
            # Fallback if passkey is not numeric (shouldn't happen with default)
            payload[2] = 0x0C
            payload[3] = 0x22

    payload[4] = command
    payload[5] = data % 256
    payload[6] = data // 256
    
    # Checksum: Sum of bytes 2-6
    checksum = sum(payload[2:7]) & 0xFF
    payload[7] = checksum
    
    return payload

# --- Predefined Commands ---
# Commands are now built dynamically in the menu to ensure they use the correct PASSWORD



# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
_LOGGER = logging.getLogger(__name__)


class HeaterCommander:
    def __init__(self, address: str, adapter: str):
        self.address = address
        self.adapter = adapter
        self.client = None
        self.is_authenticated = False
        self.notification_queue = asyncio.Queue()

    def parse_notification(self, data: bytearray):
        """
        Parses the notification data from the heater.
        Based on APK logic:
        0xAA 0x55 ...
        Byte 3: Running State
        Byte 4: Error Code
        Byte 5: Running Step
        Byte 8: Running Mode
        Byte 11, 12: Voltage (Low, High) -> (High*256 + Low) / 10
        Byte 13, 14: Case Temp (Low, High) -> Signed
        Byte 15, 16: Cab Temp (Low, High) -> Signed
        """
        if len(data) < 17:
            _LOGGER.warning(f"Notification data too short: {data.hex()}")
            # Even if too short, check header for potential ASCII message
            if len(data) >= 2 and (data[0] != 0xAA or data[1] != 0x55):
                try:
                    ascii_msg = data.decode('ascii', errors='ignore')
                    _LOGGER.warning(f"Unknown header/short data: {data.hex()}")
                    _LOGGER.warning(f"Decoded as ASCII: {ascii_msg}")
                except Exception:
                    _LOGGER.warning(f"Unknown header/short data: {data.hex()}")
            return

        if data[0] != 0xAA or data[1] != 0x55:
            _LOGGER.warning(f"Unknown header: {data.hex()}")
            # Try to decode as ASCII to see if it's a text message (e.g. error)
            try:
                ascii_msg = data.decode('ascii', errors='ignore')
                _LOGGER.warning(f"Decoded as ASCII: {ascii_msg}")
            except Exception:
                pass # Ignore if not ASCII
            return

        # Parsing
        running_state = data[3]
        error_code = data[4]
        running_step = data[5]
        running_mode = data[8]
        
        # Voltage: (High * 256 + Low) / 10
        # JS: (256*je[12]+je[11])/10
        voltage = (data[12] * 256 + data[11]) / 10.0
        
        # Temps: Signed 16-bit Little Endian
        # JS: UnsignToSign(256*je[14]+je[13])
        case_temp = int.from_bytes(data[13:15], byteorder='little', signed=True)
        cab_temp = int.from_bytes(data[15:17], byteorder='little', signed=True)

        status_str = "ON" if running_state > 0 else "OFF"
        
        _LOGGER.info(f"\n--- HEATER STATUS ---")
        _LOGGER.info(f"  State:       {status_str} (Code: {running_state})")
        _LOGGER.info(f"  Error:       {error_code}")
        _LOGGER.info(f"  Mode:        {running_mode}")
        _LOGGER.info(f"  Step:        {running_step}")
        _LOGGER.info(f"  Voltage:     {voltage}V")
        _LOGGER.info(f"  Case Temp:   {case_temp}°C")
        _LOGGER.info(f"  Cab Temp:    {cab_temp}°C")
        _LOGGER.info(f"---------------------\n")

    def notification_handler(self, sender, data):
        """Handle BLE notifications and put them in a queue."""
        _LOGGER.info(f"[RECV] Notification from {sender}: {data.hex()}")
        self.parse_notification(data)
        self.notification_queue.put_nowait(data)

    async def connect(self):
        """Connect to the heater."""
        if self.client and self.client.is_connected:
            _LOGGER.warning("Already connected.")
            return
        _LOGGER.info(f"Connecting to {self.address}...")
        try:
            self.client = BleakClient(self.address, adapter=BLUETOOTH_ADAPTER, timeout=20.0)
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

    async def handshake(self, passkey: str) -> bool:
        """
        Performs the initialization handshake with a specific passkey.
        Returns True ONLY if successful (AA 55 received), False otherwise.
        """
        _LOGGER.info(f"Performing handshake with passkey '{passkey}'...")
        
        # Clear queue
        while not self.notification_queue.empty():
            self.notification_queue.get_nowait()

        # Step 1: Send Command 1, Mode 85 (AA 55 ...) with passkey
        cmd1 = build_command(1, 0, mode=0x55, passkey=passkey)
        _LOGGER.info(f"Handshake Step 1: {cmd1.hex()}")
        await self.client.write_gatt_char(COMMAND_WRITE_UUID, cmd1)
        
        # Wait for response - STRICT CHECK
        try:
            response = await asyncio.wait_for(self.notification_queue.get(), timeout=3.0)
            
            # Check for "password" error (da header or ascii decode)
            if len(response) > 0 and response[0] == 0xDA:
                 _LOGGER.warning(f"Passkey '{passkey}' rejected (Header DA).")
                 return False
            
            # Try decoding as ASCII just in case
            try:
                ascii_msg = response.decode('ascii', errors='ignore')
                if "password" in ascii_msg.lower() or "sword" in ascii_msg.lower():
                    _LOGGER.warning(f"Passkey '{passkey}' rejected (ASCII match).")
                    return False
            except:
                pass
            
            # Check for success response (AA 55)
            if len(response) >= 2 and response[0] == 0xAA and response[1] == 0x55:
                _LOGGER.info("Handshake Step 1 accepted (Status AA 55 received).")
                # Proceed to Step 2
            else:
                _LOGGER.warning(f"Unexpected response: {response.hex()}. Treating as failure.")
                return False

        except asyncio.TimeoutError:
            # No response means failure in strict mode
            _LOGGER.warning("No response to Step 1. Treating as failure (Strict Mode).")
            return False

        # Step 2: Send Command 1, Mode 136 (AA 88 ...)
        cmd2 = build_command(1, 0, mode=0x88, passkey=passkey)
        _LOGGER.info(f"Handshake Step 2: {cmd2.hex()}")
        await self.client.write_gatt_char(COMMAND_WRITE_UUID, cmd2)
        await asyncio.sleep(0.5)
        _LOGGER.info("Handshake complete.")
        return True

    async def authenticate(self):
        if not self.client or not self.client.is_connected:
            _LOGGER.error("Not connected. Please connect first.")
            return
        if self.is_authenticated:
            _LOGGER.info("Already authenticated.")
            return

        _LOGGER.info("Attempting authentication...")
        
        try:
            # Start notifications first
            _LOGGER.info(f"Starting notifications on {NOTIFY_UUID}")
            try:
                await self.client.start_notify(NOTIFY_UUID, self.notification_handler)
            except Exception as e:
                _LOGGER.warning(f"Could not start notify (might be already started): {e}")

            # Try common passwords
            passwords = ["1234", "0000", "1111", "8888", "9999", "1688", "54321", "6666", "123456", "654321"]
            
            for pk in passwords:
                if await self.handshake(pk):
                    _LOGGER.info(f"✅ Authentication Successful with passkey '{pk}'!")
                    self.is_authenticated = True
                    # Update global password for future commands
                    global PASSWORD
                    PASSWORD = pk
                    return
                _LOGGER.warning(f"Authentication failed with passkey '{pk}'. Retrying...")
                await asyncio.sleep(1.0)

            _LOGGER.error("❌ All passwords failed.")
            self.is_authenticated = False

        except Exception as e:
            _LOGGER.error(f"Authentication failed: {e}", exc_info=True)
            self.is_authenticated = False

    async def send_command(self, command: bytearray, command_name: str, expect_response: bool = True, bypass_auth: bool = False):
        """Sends a command to the heater."""
        if not self.client or not self.client.is_connected:
            _LOGGER.error("Not connected.")
            return

        if not self.is_authenticated and not bypass_auth:
            _LOGGER.warning("Not authenticated. Please authenticate first.")
            return

        _LOGGER.info(f"\n>>> Sending command: {command_name} <<<")
        _LOGGER.info(f"  Payload: {command.hex()}")
        
        try:
            # Clear queue before sending
            while not self.notification_queue.empty():
                self.notification_queue.get_nowait()
                
            await self.client.write_gatt_char(COMMAND_WRITE_UUID, command)
            
            if expect_response:
                _LOGGER.info("  Command sent. Waiting 5s for a notification...")
                try:
                    response = await asyncio.wait_for(self.notification_queue.get(), timeout=5.0)
                    _LOGGER.info(f"  ✅ SUCCESS! Received response: {response.hex()}")
                except asyncio.TimeoutError:
                    _LOGGER.warning("  No notification received within 5s.")
            else:
                _LOGGER.info("  Command sent (no response expected).")
                _LOGGER.info(f"  ✅ SUCCESS! Command '{command_name}' sent successfully.")

        except BleakError as e:
            _LOGGER.error(f"  BLEAK ERROR: {e}")
        except Exception as e:
            _LOGGER.error(f"  UNEXPECTED ERROR: {e}", exc_info=True)

    async def scan_devices(self):
        """Scan for available Bluetooth devices."""
        print(f"\nScanning for devices on {self.adapter} (5s)...")
        try:
            devices = await BleakScanner.discover(adapter=self.adapter, timeout=5.0)
            print(f"Found {len(devices)} devices:")
            for d in devices:
                print(f"  {d.address} - {d.name} ({d.rssi} dBm)")
        except Exception as e:
            _LOGGER.error(f"Scan failed: {e}")

    async def monitor_status(self):
        """Continuously polls for status."""
        if not self.client or not self.client.is_connected:
            _LOGGER.error("Not connected.")
            return
            
        _LOGGER.info("Starting Status Monitor. Press Ctrl+C to stop.")
        _LOGGER.info(f"Using passkey: '{PASSWORD}'")
        
        try:
            while True:
                cmd = build_command(1, 0, passkey=PASSWORD)
                # We use bypass_auth=True to ensure it sends even if auth state is False
                await self.send_command(cmd, "Get Status", expect_response=True, bypass_auth=True)
                await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            _LOGGER.info("Monitor stopped.")
        except KeyboardInterrupt:
            _LOGGER.info("Monitor stopped by user.")
        except Exception as e:
            _LOGGER.error(f"Monitor error: {e}")

    async def menu(self):
        """Display the interactive main menu."""
        while True:
            print("\n--- Main Menu ---")
            status = "Connected" if self.client and self.client.is_connected else "Disconnected"
            auth_status = "Authenticated" if self.is_authenticated else "Not Authenticated"
            print(f"Status: {status} | {auth_status}")
            print("1. Connect | 2. Authenticate | 3. Send Command | 4. Disconnect | 5. Scan Devices | 6. Exit | 7. Set Password Manually | 8. Force Turn On (Bypass Auth) | 9. Monitor Status (Continuous)")
            
            choice = await asyncio.get_event_loop().run_in_executor(None, input, "Enter your choice: ")
            
            if choice == '1':
                await self.connect()
            elif choice == '2':
                await self.authenticate()
            elif choice == '3':
                print("\n--- Select Command to Send ---")
                print("1. Turn On | 2. Turn Off | 3. Get Status | 4. Get Status (Mode 102)")
                cmd_choice = await asyncio.get_event_loop().run_in_executor(None, input, "Enter your choice: ")
                cmd, name = None, None
                
                # Check auth and ask for bypass if needed
                bypass = False
                if not self.is_authenticated:
                    print("⚠️  Not authenticated.")
                    force = await asyncio.get_event_loop().run_in_executor(None, input, "Force command anyway? (y/n): ")
                    if force.lower() == 'y':
                        bypass = True
                    else:
                        print("Command cancelled.")
                        continue

                # Build commands dynamically to use the authenticated PASSWORD
                if cmd_choice == '1': 
                    cmd = build_command(3, 1, passkey=PASSWORD)
                    name = "Power On"
                elif cmd_choice == '2': 
                    cmd = build_command(3, 0, passkey=PASSWORD)
                    name = "Power Off"
                elif cmd_choice == '3': 
                    cmd = build_command(1, 0, passkey=PASSWORD)
                    name = "Get Status"
                elif cmd_choice == '4':
                    # Try Mode 102 (0x66)
                    # Note: build_command takes mode as 3rd arg.
                    # We need to pass passkey too if we want it embedded? 
                    # Or does Mode 102 use random bytes?
                    # Let's assume it uses passkey for now, similar to Mode 85.
                    cmd = build_command(1, 0, mode=0x66, passkey=PASSWORD)
                    name = "Get Status (Mode 102)"
                
                if cmd:
                    # For Power On, we might not expect a response if it's just a write
                    # But for Get Status, we definitely want to see what comes back
                    expect_resp = False if name == "Power On" else True
                    await self.send_command(cmd, name, expect_response=expect_resp, bypass_auth=bypass)
            elif choice == '4':
                await self.disconnect()
            elif choice == '5':
                await self.scan_devices()
            elif choice == '6':
                if self.client and self.client.is_connected:
                    await self.disconnect()
                break
            elif choice == '7':
                await self.set_manual_password()
            elif choice == '8':
                # Force Turn On using current PASSWORD (default 1234 if not set)
                _LOGGER.info(f"Forcing Turn On with passkey '{PASSWORD}'...")
                cmd = build_command(3, 1, passkey=PASSWORD)
                await self.send_command(cmd, "Power On (Forced)", expect_response=False, bypass_auth=True)
            elif choice == '9':
                await self.monitor_status()
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