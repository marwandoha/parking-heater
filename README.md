# Parking Heater BLE Integration for Home Assistant

This custom component allows you to control your Bluetooth parking heaters (compatible with the AirHeaterBLE app) directly from Home Assistant.

## Features

- 🔥 **Full Climate Control**: Turn heater on/off, set target temperature (8-36°C)
- 🌀 **Fan Speed Control**: Adjust fan speed from level 1 to 5
- 📊 **Real-time Monitoring**: Current temperature and heater status
- 🔍 **Automatic Discovery**: Automatically finds parking heaters via Bluetooth
- 🏠 **Native Integration**: Full Home Assistant climate entity with all standard features

## Requirements

- Home Assistant with Bluetooth support (built-in or USB dongle)
- Python packages: `bleak>=0.21.0`, `bleak-retry-connector>=3.1.0` (auto-installed)
- Parking heater compatible with AirHeaterBLE app

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL with category "Integration"
6. Click "Install"
7. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/parking_heater` folder to your `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

### Via UI (Recommended)

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Parking Heater BLE"
4. Select your heater from the list or enter the MAC address manually
5. Give your heater a friendly name (e.g., "Front Heater", "Rear Heater")
6. Click **Submit**

**For multiple heaters:** Repeat steps 2-6 for each heater. Each will be added as a separate device with its own climate entity.

### Finding Your Heater's MAC Address

If auto-discovery doesn't find your heater:

1. Use the AirHeaterBLE app on your phone
2. Connect to your heater
3. The MAC address should be visible in the app or in your phone's Bluetooth settings
4. Format: `XX:XX:XX:XX:XX:XX` (e.g., `A4:C1:38:12:34:56`)

## Usage

Once configured, your parking heater will appear as a Climate entity in Home Assistant.

### Basic Controls

- **Turn On/Off**: Use HVAC mode selector (Heat/Off)
- **Set Temperature**: Adjust target temperature slider (8°C - 36°C)
- **Fan Speed**: Select fan speed from 1 to 5

### Automations Example

```yaml
# Turn on heater 30 minutes before departure
automation:
  - alias: "Warm up car before work"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: climate.set_hvac_mode
        target:
          entity_id: climate.parking_heater
        data:
          hvac_mode: heat
      - service: climate.set_temperature
        target:
          entity_id: climate.parking_heater
        data:
          temperature: 22

# Turn off after 30 minutes
  - alias: "Turn off heater after 30 min"
    trigger:
      - platform: state
        entity_id: climate.parking_heater
        to: "heat"
        for:
          minutes: 30
    action:
      - service: climate.set_hvac_mode
        target:
          entity_id: climate.parking_heater
        data:
          hvac_mode: "off"
```

### Lovelace Card Example

```yaml
type: thermostat
entity: climate.parking_heater
features:
  - type: climate-hvac-modes
    hvac_modes:
      - "off"
      - heat
  - type: climate-fan-modes
```

## Troubleshooting

### Device Not Found

1. Ensure the heater is powered on
2. Make sure you're within Bluetooth range (typically 10 meters)
3. Check that your Home Assistant has Bluetooth enabled
4. Try restarting the heater
5. Manually enter the MAC address if auto-discovery fails

### Connection Issues

1. Check Home Assistant logs: **Settings** → **System** → **Logs**
2. Ensure no other device (like your phone) is connected to the heater
3. Restart the integration: **Settings** → **Devices & Services** → **Parking Heater** → **⋮** → **Reload**
4. Restart Home Assistant if problems persist

### Commands Not Working

The Bluetooth protocol may vary slightly between heater models. If commands don't work:

1. Check the logs for error messages
2. The protocol constants in `const.py` may need adjustment
3. Consider using a Bluetooth sniffer (like Wireshark) to capture the actual commands from the AirHeaterBLE app

## Protocol Reverse Engineering

If your specific heater model uses different commands, you may need to reverse engineer the protocol:

1. Install a Bluetooth sniffer on Android (e.g., nRF Connect)
2. Connect your heater with the AirHeaterBLE app
3. Capture the Bluetooth traffic
4. Identify the service UUIDs and characteristic UUIDs
5. Decode the command structure
6. Update the constants in `const.py` and command structures in `heater_client.py`

### Common BLE Characteristics

- **Service UUID**: Usually `0000fff0-0000-1000-8000-00805f9b34fb`
- **Write Characteristic**: `0000fff1-0000-1000-8000-00805f9b34fb`
- **Notify Characteristic**: `0000fff2-0000-1000-8000-00805f9b34fb`

## Technical Details

### Protocol Structure

Commands typically follow this format:
```
[Header: 0x76] [Command Type] [Length] [Data...] [Checksum]
```

### Supported Commands

- Power On/Off
- Set Temperature (8-36°C)
- Set Fan Speed (1-5)
- Get Status

## Known Limitations

- Bluetooth range limited to ~10 meters
- Only one connection at a time (can't use phone app simultaneously)
- Some advanced features from the app may not be supported
- Protocol may vary between heater manufacturers

## Support

If you encounter issues:

1. Check Home Assistant logs
2. Enable debug logging:
   ```yaml
   logger:
     default: info
     logs:
       custom_components.parking_heater: debug
   ```
3. Open an issue on GitHub with logs and heater model info

## Contributing

Contributions are welcome! If you have a different heater model and have reverse-engineered the protocol, please submit a PR.

## License

MIT License

## Disclaimer

This integration is not officially affiliated with any parking heater manufacturer. Use at your own risk. Always follow safety guidelines when operating parking heaters.

## Credits

- Inspired by the AirHeaterBLE Android app
- Built with Home Assistant's modern integration architecture
- Uses the `bleak` library for cross-platform Bluetooth LE support
