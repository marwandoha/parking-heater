# Parking Heater BLE - Frequently Asked Questions

## General Questions

### Q: What parking heaters are compatible with this integration?
A: Any parking heater that works with the AirHeaterBLE Android app should be compatible. These are typically Chinese-made parking heaters (diesel or gasoline) with Bluetooth control. Common brands include various OEM manufacturers selling under different names.

### Q: Do I need an external Bluetooth adapter?
A: It depends on your Home Assistant setup:
- **Raspberry Pi 3/4/5**: Built-in Bluetooth works fine
- **Other hardware**: May need a USB Bluetooth dongle (recommended: with Bluetooth 4.0+ / BLE support)

### Q: Can I control multiple heaters?
A: Yes! You can add multiple heaters (e.g., front and rear). Each will appear as a separate device in Home Assistant. 

**How to add multiple:**
1. Go to Settings → Devices & Services
2. Click "+ Add Integration" for EACH heater
3. Search "Parking Heater BLE" each time
4. Give each a unique name (e.g., "Front Heater", "Rear Heater")
5. Each gets its own climate entity: `climate.front_heater`, `climate.rear_heater`

**Control them together:**
```yaml
service: climate.turn_on
target:
  entity_id:
    - climate.front_heater
    - climate.rear_heater
```

### Q: Will this work with my phone app at the same time?
A: No. Bluetooth only allows one connection at a time. You must choose either Home Assistant OR the phone app. Disconnect from one before connecting to the other.

## Installation Questions

### Q: Where do I install the files?
A: Copy the `custom_components/parking_heater` folder to your Home Assistant configuration directory:
```
/config/custom_components/parking_heater/
```

### Q: Do I need to install anything else?
A: The integration automatically installs required Python packages (`bleak` and `bleak-retry-connector`). Just make sure your Home Assistant has Bluetooth enabled.

### Q: How do I find my heater's MAC address?
A: Several methods:
1. Look in the AirHeaterBLE app when connected
2. Use "nRF Connect" app (Android) or "LightBlue" app (iOS)
3. Check your phone's Bluetooth settings while connected
4. Let Home Assistant auto-discover it (if in range)

### Q: The integration doesn't appear after installation?
A: Make sure to:
1. Restart Home Assistant after copying files
2. Clear your browser cache (Ctrl+F5)
3. Check that all files are in the correct location
4. Check Home Assistant logs for errors

## Connection Issues

### Q: "Cannot connect to device" error?
A: Try these steps:
1. Make sure the heater is powered on
2. Ensure you're within Bluetooth range (typically 10 meters)
3. Disconnect the AirHeaterBLE app if running
4. Power cycle the heater (turn off and on)
5. Restart the Bluetooth service on your Raspberry Pi
6. Check Home Assistant logs for detailed errors

### Q: Connection keeps dropping?
A: Common causes:
- **Distance**: Heater may be too far from Home Assistant
- **Interference**: Other Bluetooth devices or WiFi can interfere
- **Power**: Weak heater battery/power supply
- **Signal**: Metal car body can block signal

Try:
- Move Bluetooth adapter closer to heater
- Use a USB extension cable to position adapter better
- Reduce polling interval in the code

### Q: Device not found during setup?
A: Checklist:
- [ ] Heater is powered on
- [ ] Heater is within 10 meters
- [ ] No other device connected to heater
- [ ] Bluetooth is enabled on Home Assistant
- [ ] Try entering MAC address manually

## Usage Questions

### Q: How do I turn the heater on from an automation?
A: Use the climate.set_hvac_mode service:
```yaml
service: climate.set_hvac_mode
target:
  entity_id: climate.parking_heater
data:
  hvac_mode: heat
```

### Q: Can I set temperature and fan speed at the same time?
A: Yes, but do it in sequence in your automation:
```yaml
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
- service: climate.set_fan_mode
  target:
    entity_id: climate.parking_heater
  data:
    fan_mode: "3"
```

### Q: How often does the integration update?
A: By default, every 30 seconds. You can modify this in `const.py` by changing `UPDATE_INTERVAL`.

### Q: Can I monitor fuel consumption?
A: Not currently. The integration only reports what the heater provides via Bluetooth. Most heaters don't report fuel data over BLE.

## Technical Questions

### Q: What if my heater uses different commands?
A: You may need to reverse engineer the protocol:
1. Use nRF Connect to sniff Bluetooth traffic
2. Capture commands from the AirHeaterBLE app
3. Modify `const.py` and `heater_client.py` with correct commands
4. See `PROTOCOL.md` for details

### Q: The commands don't work with my heater?
A: Different manufacturers may use different protocols. Check:
1. Service UUIDs (in nRF Connect)
2. Characteristic UUIDs
3. Command structures (capture with BLE sniffer)
4. Update the constants in the code accordingly

### Q: How do I enable debug logging?
A: Add to `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.parking_heater: debug
    bleak: debug
```
Then restart Home Assistant and check logs.

### Q: Can I contribute to the project?
A: Absolutely! Contributions are welcome:
- Report bugs with logs
- Submit protocol info for different heater models
- Improve documentation
- Add features via pull requests

## Safety Questions

### Q: Is it safe to leave the heater running unattended?
A: **Always follow manufacturer safety guidelines!** Recommendations:
- Never run heater in enclosed spaces
- Ensure proper ventilation
- Use automations to auto-shut-off after set time
- Monitor for error codes
- Check fuel levels regularly

### Q: What do error codes mean?
A: Common error codes (may vary by model):
- 0x00: No error
- 0x01: Flame out (ignition failure)
- 0x02: Temperature sensor error
- 0x03: Overheat protection
- 0x04: Motor error
- 0x05: Low voltage
- 0x06: High voltage

If you get persistent errors, check the heater physically!

### Q: Can the heater drain my car battery?
A: Yes! Parking heaters draw significant power. Recommendations:
- Don't run too long on battery alone
- Consider a battery monitor integration
- Set auto-shutoff timers
- Ensure good battery condition

## Performance Questions

### Q: Does this use a lot of resources?
A: No, very lightweight:
- Polls every 30 seconds
- Minimal memory usage
- BLE is low power
- No cloud dependencies

### Q: Will it work with Home Assistant Cloud?
A: For local control, no cloud needed. But you CAN use Home Assistant Cloud/Nabu Casa to:
- Access from anywhere via internet
- Use voice assistants remotely
- Integration still works locally

### Q: Can I use this with Google Home / Alexa?
A: Yes! Once added to Home Assistant, expose it:
- **Google Home**: Via Home Assistant Cloud or manually configure
- **Alexa**: Via Home Assistant Cloud or Alexa skill
- Use climate entity voice commands

## Troubleshooting

### Q: "Module not found" error?
A: Dependencies didn't install. Manually install:
```bash
# SSH into Home Assistant
source /srv/homeassistant/bin/activate
pip install bleak bleak-retry-connector
```

### Q: Temperature shows in Fahrenheit?
A: Change Home Assistant unit system:
Settings → System → General → Unit System → Metric

### Q: Heater works in app but not Home Assistant?
A: Remember: only ONE connection at a time. Fully close the AirHeaterBLE app, then:
1. Restart Home Assistant integration
2. Or power cycle the heater

### Q: How do I uninstall?
A: 
1. Remove integration: Settings → Devices & Services → Parking Heater → Delete
2. Delete folder: `custom_components/parking_heater`
3. Restart Home Assistant

## Getting Help

### Q: Where can I get more help?
A: Several options:
1. Check Home Assistant logs (Settings → System → Logs)
2. Enable debug logging (see above)
3. Open GitHub issue with logs and heater model
4. Home Assistant Community Forum
5. Home Assistant Discord

### Q: What information should I provide when reporting issues?
A: Please include:
- Home Assistant version
- Integration version
- Heater brand/model
- MAC address format (XX:XX:XX:XX:XX:XX)
- Relevant logs with debug enabled
- Whether AirHeaterBLE app works
- Steps to reproduce the issue

---

**Still have questions?** Open an issue on GitHub or check the documentation!
