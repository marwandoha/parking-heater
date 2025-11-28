# Protocol Documentation

This document describes the Bluetooth Low Energy (BLE) protocol used by parking heaters compatible with the AirHeaterBLE app.

## Overview

The parking heaters communicate over Bluetooth Low Energy using a simple command-response protocol. Commands are sent to the device, and responses are received via BLE notifications.

## BLE Service and Characteristics

### Service UUID
```
0000fff0-0000-1000-8000-00805f9b34fb
```

### Characteristics

**Write Characteristic** (for sending commands):
```
0000fff1-0000-1000-8000-00805f9b34fb
```

**Notify Characteristic** (for receiving responses):
```
0000fff2-0000-1000-8000-00805f9b34fb
```

## Command Structure

Commands follow this general format:

```
[Header] [Command Type] [Length] [Data...] [Checksum]
```

### Command Format

| Byte | Description | Value |
|------|-------------|-------|
| 0 | Header | 0x76 |
| 1 | Command Type | Variable (see below) |
| 2 | Data Length | Number of data bytes |
| 3-N | Data | Command-specific data |
| N+1 | Checksum | Sum of all bytes & 0xFF |

### Checksum Calculation

```python
def calculate_checksum(data: bytes) -> int:
    return sum(data) & 0xFF
```

## Commands

### Power Control

**Power ON**
```
0x76 0x16 0x01 0x01 0x00 0x00 0x00 0x00 0x8E
```
- Command Type: 0x16
- Data: 0x01 (ON)

**Power OFF**
```
0x76 0x16 0x01 0x00 0x00 0x00 0x00 0x00 0x8D
```
- Command Type: 0x16
- Data: 0x00 (OFF)

### Get Status

**Request Status**
```
0x76 0x17 0x01 0x00 0x00 0x00 0x00 0x00 0x8E
```
- Command Type: 0x17
- Returns device state, temperature, fan speed

### Set Temperature

**Set Temperature Command**
```
0x76 0x18 0x01 [TEMP] [CHECKSUM]
```
- Command Type: 0x18
- Temperature range: 8-36°C
- Example: Set 22°C: `0x76 0x18 0x01 0x16 0xA5`

### Set Fan Speed

**Set Fan Speed Command**
```
0x76 0x19 0x01 [SPEED] [CHECKSUM]
```
- Command Type: 0x19
- Speed range: 1-5
- Example: Set speed 3: `0x76 0x19 0x01 0x03 0x93`

## Response Structure

Responses follow a similar format:

```
[Header] [Response Type] [Length] [Data...] [Checksum]
```

### Status Response Format

| Byte | Description | Value |
|------|-------------|-------|
| 0 | Header | 0x76 |
| 1 | Response Type | Variable |
| 2 | Data Length | Number of data bytes |
| 3 | Power State | 0x00 (OFF) / 0x01 (ON) |
| 4 | Target Temperature | 8-36 (°C) |
| 5 | Current Temperature | 8-36 (°C) |
| 6 | Fan Speed | 1-5 |
| 7 | Error Code | 0x00 (no error) |
| N | Checksum | Sum of all bytes & 0xFF |

### Example Status Response

```
0x76 0x17 0x05 0x01 0x16 0x14 0x03 0x00 0xB9
```

Parsed:
- Header: 0x76
- Response Type: 0x17 (status)
- Length: 0x05 (5 bytes of data)
- Power: 0x01 (ON)
- Target Temp: 0x16 (22°C)
- Current Temp: 0x14 (20°C)
- Fan Speed: 0x03 (level 3)
- Error Code: 0x00 (no error)
- Checksum: 0xB9

## Error Codes

| Code | Description |
|------|-------------|
| 0x00 | No error |
| 0x01 | Flame out |
| 0x02 | Temperature sensor error |
| 0x03 | Overheat |
| 0x04 | Motor error |
| 0x05 | Low voltage |
| 0x06 | High voltage |
| 0xFF | Unknown error |

## Connection Sequence

1. Scan for BLE devices with service UUID `0000fff0-...`
2. Connect to the device
3. Subscribe to notifications on characteristic `0000fff2-...`
4. Send commands via characteristic `0000fff1-...`
5. Receive responses via notifications

## Notes

- Only one BLE connection at a time (phone app or Home Assistant)
- Connection may timeout after 5 minutes of inactivity
- Some commands may take 1-2 seconds to execute
- Always verify checksum on received data

## Reverse Engineering Tips

If your heater uses a different protocol:

1. Use nRF Connect (Android) or LightBlue (iOS) to scan for services
2. Enable BLE sniffer in Android Developer Options
3. Capture traffic while using the AirHeaterBLE app
4. Analyze command patterns
5. Test commands with nRF Connect before implementing

## Testing Commands

Use nRF Connect app to test commands:

1. Connect to your heater
2. Find the write characteristic (fff1)
3. Send hex commands manually
4. Observe responses on notify characteristic (fff2)
5. Verify heater responds as expected

## Implementation Notes

- Use `bleak` library for cross-platform BLE support
- Implement retry logic for failed commands
- Add timeout handling (5 seconds recommended)
- Queue commands to avoid race conditions
- Cache last known state during disconnections

## Manufacturer Variations

Different manufacturers may use:
- Different service UUIDs
- Different command structures
- Additional features (timer, altitude compensation, etc.)
- Different error codes

Always verify with your specific heater model!
