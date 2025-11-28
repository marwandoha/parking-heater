# Installation Instructions

## Prerequisites

Before installing this integration, ensure you have:

1. **Home Assistant** installed and running (minimum version 2023.1.0 recommended)
2. **HACS** (Home Assistant Community Store) installed - [Installation Guide](https://hacs.xyz/docs/setup/download)
3. **Bluetooth adapter** - Either built-in Bluetooth on Raspberry Pi or external USB dongle
4. **Parking heater** compatible with AirHeaterBLE app, powered on

## Step 1: Install the Integration

### Option A: Via HACS (Recommended)

1. Open Home Assistant
2. Navigate to **HACS** → **Integrations**
3. Click the **⋮** (three dots) in the top right
4. Select **Custom repositories**
5. Add repository URL: `https://github.com/yourusername/parking_heater`
6. Select category: **Integration**
7. Click **Add**
8. Search for "Parking Heater BLE" in HACS
9. Click **Download**
10. Select the latest version
11. Click **Download** again

### Option B: Manual Installation

1. Download the latest release from GitHub
2. Extract the ZIP file
3. Copy the `custom_components/parking_heater` folder to your Home Assistant config directory:
   ```
   <config_directory>/custom_components/parking_heater/
   ```
4. Your directory structure should look like:
   ```
   config/
   ├── custom_components/
   │   └── parking_heater/
   │       ├── __init__.py
   │       ├── manifest.json
   │       ├── climate.py
   │       ├── config_flow.py
   │       ├── const.py
   │       ├── coordinator.py
   │       ├── heater_client.py
   │       └── strings.json
   ```

## Step 2: Restart Home Assistant

After installing the integration:

1. Go to **Settings** → **System**
2. Click **Restart** (top right corner)
3. Wait for Home Assistant to fully restart

## Step 3: Enable Bluetooth (If Not Already Enabled)

### On Raspberry Pi

1. Check if Bluetooth is enabled:
   ```bash
   hciconfig
   ```

2. If Bluetooth is not enabled, you may need to enable it:
   ```bash
   sudo systemctl enable bluetooth
   sudo systemctl start bluetooth
   ```

### With External USB Dongle

1. Plug in your Bluetooth USB dongle
2. Home Assistant should automatically detect it
3. Verify in **Settings** → **System** → **Hardware** that Bluetooth is available

## Step 4: Add the Integration

1. Navigate to **Settings** → **Devices & Services**
2. Click **+ Add Integration** (bottom right)
3. Search for "Parking Heater"
4. Click on **Parking Heater BLE**

## Step 5: Configure Your Heater

### If Auto-Discovery Works:

1. The integration will scan for nearby parking heaters
2. Select your heater from the dropdown list
3. Give it a friendly name (e.g., "Car Heater", "Parking Heater")
4. Click **Submit**
5. Your heater should now appear in Home Assistant!

### If Manual Entry is Needed:

If your heater isn't automatically discovered:

1. Find your heater's MAC address:
   - Open the AirHeaterBLE app on your phone
   - Connect to your heater
   - Note the MAC address (format: `XX:XX:XX:XX:XX:XX`)
   
   **OR use a Bluetooth scanner:**
   - On Android: Use "nRF Connect" app
   - On iOS: Use "LightBlue" app
   - Look for devices named "Air" or similar

2. Enter the MAC address in the integration setup
3. Give your heater a name
4. Click **Submit**

## Step 6: Verify Installation

1. Go to **Settings** → **Devices & Services**
2. You should see "Parking Heater BLE" listed
3. Click on it to see your configured heater(s)
4. Click on the device to view the climate entity

## Step 7: Test Your Heater

1. Go to **Settings** → **Devices & Services** → **Parking Heater BLE**
2. Click on your heater device
3. Click on the climate entity (e.g., `climate.parking_heater`)
4. Try these tests:
   - Turn it on (set HVAC mode to "Heat")
   - Adjust the temperature
   - Change the fan speed
   - Turn it off

## Step 7a: Add Additional Heaters (Optional)

If you have multiple heaters installed:

1. Repeat **Step 4** (Add Integration) for each additional heater
2. Use unique, descriptive names:
   - "Front Parking Heater"
   - "Rear Parking Heater"
   - "Left Side Heater"
   - "Right Side Heater"
3. Each heater will have its own:
   - Device entry
   - Climate entity
   - MAC address
4. Test each heater individually
5. Create automations to control multiple heaters together

## Step 8: Add to Dashboard (Optional)

1. Go to your Home Assistant dashboard
2. Click **Edit Dashboard** (three dots, top right)
3. Click **Add Card**
4. Select **Thermostat Card**
5. Select your parking heater entity
6. Customize the card as desired
7. Click **Save**

## Troubleshooting Installation

### Integration Not Found

- Ensure you restarted Home Assistant after copying files
- Check that files are in the correct location: `config/custom_components/parking_heater/`
- Verify all files from the repository are present

### Bluetooth Not Working

- Ensure Bluetooth is enabled on your system
- Check Home Assistant logs: **Settings** → **System** → **Logs**
- Try restarting the Bluetooth service:
  ```bash
  sudo systemctl restart bluetooth
  ```

### Cannot Connect to Heater

- Make sure heater is powered on
- Ensure you're within range (typically 10 meters)
- Verify no other device (phone) is connected to the heater
- Try power cycling the heater

### Dependencies Not Installing

The integration requires these Python packages:
- `bleak>=0.21.0`
- `bleak-retry-connector>=3.1.0`

They should install automatically, but if not:

1. SSH into your Home Assistant
2. Activate the virtual environment:
   ```bash
   source /srv/homeassistant/bin/activate
   ```
3. Manually install:
   ```bash
   pip install bleak bleak-retry-connector
   ```

## Next Steps

- Set up automations (see README.md for examples)
- Add to your dashboard
- Configure alerts for errors
- Create scenes with your heater

## Getting Help

If you still have issues:

1. Enable debug logging:
   ```yaml
   # configuration.yaml
   logger:
     default: info
     logs:
       custom_components.parking_heater: debug
   ```

2. Restart Home Assistant
3. Try the integration again
4. Check logs for detailed error messages
5. Open an issue on GitHub with the logs

## Updating the Integration

### Via HACS:

1. Go to **HACS** → **Integrations**
2. Find "Parking Heater BLE"
3. Click **Update** if available
4. **Restart Home Assistant**
5. No need to remove/re-add devices

### Manual Update:

1. Download the latest release from GitHub
2. **Replace** the `custom_components/parking_heater` folder completely
3. **Restart Home Assistant** (Settings → System → Restart)
4. Integration will automatically reload with new code
5. **No need to uninstall** - just restart HA

**Note**: Your device configuration, automations, and history are preserved during updates.

**Detailed upgrade guide**: See [UPGRADE.md](UPGRADE.md) for more information.

---

**Congratulations!** Your parking heater is now integrated with Home Assistant. Enjoy remote control and automation of your heater! 🚗🔥
