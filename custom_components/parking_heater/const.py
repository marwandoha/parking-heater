"""Constants for the Parking Heater integration."""
from typing import Final
from datetime import timedelta

DOMAIN: Final = "parking_heater"

# Configuration
CONF_MAC_ADDRESS: Final = "mac_address"
CONF_DEVICE_NAME: Final = "device_name"

# Default values
DEFAULT_NAME: Final = "Parking Heater"
DEFAULT_SCAN_INTERVAL: Final = 30  # seconds

# BLE Service and Characteristic UUIDs
# Based on actual BYD parking heaters (confirmed from scan)
SERVICE_UUID: Final = "0000ffe0-0000-1000-8000-00805f9b34fb"
WRITE_CHAR_UUID: Final = "0000ffe1-0000-1000-8000-00805f9b34fb"
NOTIFY_CHAR_UUID: Final = "0000ffe1-0000-1000-8000-00805f9b34fb"  # Same as write

# Command bytes
# Protocol: AA 55 [PW_1] [PW_2] [CMD] [DATA1] [DATA2] [CS]
# Password is fixed "1234" -> 0x0C 0x22
PASSWORD_BYTES: Final = bytes([0x0C, 0x22])

# Base Commands (Before Checksum)
# Get Status: AA 55 0C 22 01 00 00 2F
CMD_GET_STATUS: Final = bytes([0xAA, 0x55, 0x0C, 0x22, 0x01, 0x00, 0x00, 0x2F])

# Turn On: AA 55 0C 22 03 01 00 [CS]
CMD_TURN_ON_BASE: Final = bytes([0xAA, 0x55, 0x0C, 0x22, 0x03, 0x01, 0x00])

# Turn Off: AA 55 0C 22 03 00 00 [CS]
CMD_TURN_OFF_BASE: Final = bytes([0xAA, 0x55, 0x0C, 0x22, 0x03, 0x00, 0x00])

# Set Mode: AA 55 0C 22 02 [Mode] 00 [CS]
# Mode 1 = Manual (Level Control), Mode 2 = Auto (Temp Control)
CMD_SET_MODE_BASE: Final = bytes([0xAA, 0x55, 0x0C, 0x22, 0x02])

# Set Value: AA 55 0C 22 04 [Value] 00 [CS]
# Used for both Level (1-10) and Temp (8-36) depending on Mode
CMD_SET_VALUE_BASE: Final = bytes([0xAA, 0x55, 0x0C, 0x22, 0x04])

# Temperature range
MIN_TEMP: Final = 8
MAX_TEMP: Final = 36
TEMP_STEP: Final = 1

# Level range
MIN_LEVEL: Final = 1
MAX_LEVEL: Final = 10
LEVEL_STEP: Final = 1

# Fan speeds (Not directly controllable in this protocol, usually auto)
FAN_SPEEDS: Final = {
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
}

# Update interval
UPDATE_INTERVAL: Final = timedelta(seconds=5)  # Fast polling for active status
