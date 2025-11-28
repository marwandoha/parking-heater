# Pre-Deployment Checklist

Use this checklist before deploying the integration to your Home Assistant instance.

## ✅ Installation Verification

### Files Present
- [ ] `custom_components/parking_heater/__init__.py`
- [ ] `custom_components/parking_heater/manifest.json`
- [ ] `custom_components/parking_heater/config_flow.py`
- [ ] `custom_components/parking_heater/const.py`
- [ ] `custom_components/parking_heater/coordinator.py`
- [ ] `custom_components/parking_heater/heater_client.py`
- [ ] `custom_components/parking_heater/climate.py`
- [ ] `custom_components/parking_heater/strings.json`
- [ ] `custom_components/parking_heater/translations/en.json`

### Documentation Present
- [ ] `README.md`
- [ ] `INSTALLATION.md`
- [ ] `QUICKSTART.md`
- [ ] `PROTOCOL.md`
- [ ] `FAQ.md`
- [ ] `CHANGELOG.md`
- [ ] `LICENSE`

## 🔧 Pre-Installation Steps

### Home Assistant Environment
- [ ] Home Assistant version 2023.1 or newer
- [ ] Bluetooth integration enabled in HA
- [ ] Bluetooth adapter working (`hciconfig` or Settings → System → Hardware)
- [ ] Home Assistant restarted after copying files

### Heater Preparation
- [ ] Parking heater powered on
- [ ] Heater in Bluetooth range (< 10 meters)
- [ ] AirHeaterBLE phone app closed/disconnected
- [ ] MAC address noted (if manual entry needed)

## 📝 First-Time Setup

### Integration Addition
- [ ] Navigate to Settings → Devices & Services
- [ ] Click "+ Add Integration"
- [ ] Search for "Parking Heater"
- [ ] Integration appears in list
- [ ] Can proceed to config flow

### Configuration Flow
- [ ] Heater discovered automatically OR
- [ ] Manual MAC address entry works
- [ ] Device name can be set
- [ ] Setup completes without errors
- [ ] Entity created: `climate.parking_heater`

## 🧪 Functionality Testing

### Basic Controls
- [ ] Can view climate entity in HA
- [ ] Current temperature displays (or N/A initially)
- [ ] Can turn heater ON (set to "Heat" mode)
- [ ] Heater actually turns on physically
- [ ] Can set target temperature
- [ ] Temperature change reflected in heater
- [ ] Can change fan speed
- [ ] Fan speed changes on heater
- [ ] Can turn heater OFF
- [ ] Heater actually turns off physically

### Status Updates
- [ ] Status updates appear (check every 30 seconds)
- [ ] Current temperature updates when heater running
- [ ] Fan speed shows correctly
- [ ] Power state shows correctly (On/Off)
- [ ] Error codes appear if applicable

### Connection Handling
- [ ] Reconnects after heater power cycle
- [ ] Handles connection loss gracefully
- [ ] Shows "Unavailable" when out of range
- [ ] Reconnects when back in range

## 🎨 Dashboard Integration

### Climate Card
- [ ] Add thermostat card to dashboard
- [ ] Card displays correctly
- [ ] Temperature slider works
- [ ] Fan mode selector works
- [ ] HVAC mode toggle works
- [ ] Status updates on card

## 🤖 Automation Testing

### Basic Automation
- [ ] Create test automation (turn on at specific time)
- [ ] Automation triggers correctly
- [ ] Heater responds to automation
- [ ] Can call services from Developer Tools
- [ ] `climate.set_hvac_mode` works
- [ ] `climate.set_temperature` works
- [ ] `climate.set_fan_mode` works

## 📊 Logging & Debugging

### Log Verification
- [ ] Check logs: Settings → System → Logs
- [ ] No critical errors on startup
- [ ] Integration loads successfully
- [ ] Device connects without errors
- [ ] Commands execute without errors

### Debug Logging (if needed)
- [ ] Add debug logging to configuration.yaml
- [ ] Restart HA
- [ ] Debug messages appear in logs
- [ ] Can see BLE communication
- [ ] Can see command/response data

## ⚠️ Known Issues Check

### Protocol Compatibility
- [ ] Commands actually control your heater model
- [ ] Temperature readings accurate
- [ ] Fan speeds match actual levels
- [ ] Error codes make sense (if any)

### Protocol Adjustment (if needed)
- [ ] Captured BLE traffic with nRF Connect
- [ ] Identified service UUIDs
- [ ] Decoded command structure
- [ ] Updated `const.py` with correct values
- [ ] Updated `heater_client.py` if needed
- [ ] Retested after changes

## 📱 Multi-Device Testing

### Phone App Compatibility
- [ ] Can't connect both HA and phone app simultaneously (expected)
- [ ] Closing phone app allows HA to connect
- [ ] Closing HA allows phone app to connect
- [ ] No conflicts between apps

## 🔒 Security & Safety

### Safety Features
- [ ] Auto-shutoff automation configured
- [ ] Heater won't run indefinitely
- [ ] Battery drain prevention in place
- [ ] Notification setup for long runs (optional)

### Security
- [ ] MAC address not exposed publicly
- [ ] Integration only accessible on local network
- [ ] No cloud dependencies (good for privacy)

## 📈 Performance

### Resource Usage
- [ ] CPU usage acceptable
- [ ] Memory usage acceptable
- [ ] Bluetooth connection stable
- [ ] No excessive polling
- [ ] Updates occur at expected intervals

## 📝 Documentation Review

### For Users
- [ ] README accurate for your setup
- [ ] Installation instructions clear
- [ ] Examples work as documented
- [ ] Troubleshooting section helpful
- [ ] FAQ answers common questions

## 🚀 Production Readiness

### Before Daily Use
- [ ] Tested multiple on/off cycles
- [ ] Tested temperature range (8-36°C)
- [ ] Tested all fan speeds
- [ ] Tested over 24 hour period
- [ ] Tested connection recovery
- [ ] Tested automation reliability
- [ ] Created backup of config

### Backup Plan
- [ ] Know how to remove integration if needed
- [ ] Keep phone app as backup control method
- [ ] Document your heater's MAC address
- [ ] Save working configuration

## ✅ Final Checks

- [ ] All core functions working
- [ ] No critical errors in logs
- [ ] Acceptable for daily use
- [ ] Automation setup complete
- [ ] Safety measures in place
- [ ] User trained on features
- [ ] Backup control method available

## 🎉 Deployment Success Criteria

The integration is ready for production use when:

1. ✅ Heater reliably connects
2. ✅ All controls work as expected
3. ✅ Status updates regularly
4. ✅ Automations execute correctly
5. ✅ No critical errors in logs
6. ✅ Safety measures configured
7. ✅ User comfortable with operation

---

## 🐛 If Something Fails

### Debugging Steps
1. Check Home Assistant logs
2. Enable debug logging
3. Test with nRF Connect app
4. Verify BLE protocol with phone app sniffer
5. Check FAQ.md for known issues
6. Open GitHub issue with logs

### Rollback Plan
1. Remove integration from HA
2. Delete custom_component folder
3. Restart Home Assistant
4. Use phone app temporarily
5. Troubleshoot and retry

---

## 📞 Getting Help

If you complete this checklist and have issues:

1. ✅ Ensure all checklist items completed
2. 📋 Gather debug logs
3. 📝 Note exact error messages
4. 🔍 Check FAQ.md first
5. 🐛 Open detailed GitHub issue
6. 💬 Ask in HA Community Forum

---

**Good luck with your deployment!** 🚗🔥

Once everything checks out, enjoy your automated parking heater control! ✅
