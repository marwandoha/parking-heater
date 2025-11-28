"""Constants for the Parking Heater integration."""
from typing import Final

DOMAIN: Final = "parking_heater"

# Configuration
CONF_MAC_ADDRESS: Final = "mac_address"
CONF_DEVICE_NAME: Final = "device_name"

# Default values
DEFAULT_NAME: Final = "Parking Heater"
DEFAULT_SCAN_INTERVAL: Final = 30  # seconds

# BLE Service and Characteristic UUIDs
# Based on official protocol documentation
SERVICE_UUID: Final = "0000fff0-0000-1000-8000-00805f9b34fb"
WRITE_CHAR_UUID: Final = "0000fff1-0000-1000-8000-00805f9b34fb"
NOTIFY_CHAR_UUID: Final = "0000fff2-0000-1000-8000-00805f9b34fb"

# Command bytes (these are typical for air heater BLE devices)
# Note: These may need to be reverse-engineered from the actual app
CMD_PREFIX: Final = bytes([0x76])
CMD_SUFFIX: Final = bytes([0x00])

# Commands
CMD_POWER_ON: Final = bytes([0x76, 0x16, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x8E])
CMD_POWER_OFF: Final = bytes([0x76, 0x16, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x8D])
CMD_GET_STATUS: Final = bytes([0x76, 0x17, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x8E])

# Temperature range
MIN_TEMP: Final = 8
MAX_TEMP: Final = 36
TEMP_STEP: Final = 1

# Fan speeds
FAN_SPEEDS: Final = {
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
}

# Update interval
UPDATE_INTERVAL: Final = 30  # seconds
