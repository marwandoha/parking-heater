# Quick Start Guide

Get your parking heater integrated with Home Assistant in 5 minutes!

## Prerequisites Check ✅

Before starting, make sure you have:
- [ ] Home Assistant installed and running
- [ ] HACS installed (optional but recommended)
- [ ] Bluetooth enabled on your system
- [ ] Parking heater powered on
- [ ] Heater MAC address (or rely on auto-discovery)

## Installation (Choose One Method)

### Method 1: HACS (Easiest)

1. Open HACS → Integrations
2. Click ⋮ → Custom repositories
3. Add repository URL (when published)
4. Search "Parking Heater BLE"
5. Click Download
6. **Restart Home Assistant**

### Method 2: Manual

1. Download this repository
2. Copy `custom_components/parking_heater` to your `config/custom_components/` folder
3. **Restart Home Assistant**

## Setup (2 Minutes)

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search "Parking Heater"
4. Select your heater from the list (or enter MAC address)
5. Give it a name
6. Click **Submit**

✅ Done! Your heater is now integrated.

## First Test

1. Find your heater: **Settings** → **Devices & Services** → **Parking Heater BLE**
2. Click the climate entity
3. Try:
   - Turn it on (set to "Heat")
   - Adjust temperature
   - Change fan speed
   - Turn it off

## Add to Dashboard

1. Go to your dashboard
2. Click **Edit** (⋮ → Edit Dashboard)
3. Click **+ Add Card**
4. Choose **Thermostat Card**
5. Select `climate.parking_heater`
6. Click **Save**

## Create Your First Automation

Here's a simple automation to warm up your car before work:

1. Go to **Settings** → **Automations & Scenes**
2. Click **+ Create Automation**
3. Click **Start with an empty automation**
4. Add trigger: Time 07:00
5. Add action: Call service `climate.set_hvac_mode`
   - Entity: `climate.parking_heater`
   - HVAC mode: `heat`
6. Add another action: Call service `climate.set_temperature`
   - Entity: `climate.parking_heater`
   - Temperature: 22
7. Give it a name: "Warm up car"
8. Click **Save**

## Quick Automation Examples

### Auto Turn Off After 30 Minutes

```yaml
alias: "Auto turn off heater"
trigger:
  - platform: state
    entity_id: climate.parking_heater
    to: "heat"
    for:
      minutes: 30
action:
  - service: climate.turn_off
    target:
      entity_id: climate.parking_heater
```

### Warm Car When Cold Outside

```yaml
alias: "Warm car when cold"
trigger:
  - platform: numeric_state
    entity_id: weather.home
    attribute: temperature
    below: 5
  - platform: time
    at: "07:00:00"
condition:
  - condition: time
    weekday:
      - mon
      - tue
      - wed
      - thu
      - fri
action:
  - service: climate.turn_on
    target:
      entity_id: climate.parking_heater
  - service: climate.set_temperature
    target:
      entity_id: climate.parking_heater
    data:
      temperature: 20
```

## Troubleshooting Common Issues

### "Cannot find device"
→ Make sure heater is on and within 10 meters

### "Cannot connect"
→ Disconnect your phone app first (only one connection allowed)

### "Integration not showing"
→ Restart Home Assistant and clear browser cache (Ctrl+F5)

## Next Steps

- 📖 Read the full [README.md](README.md) for detailed features
- 🔄 See [UPGRADE.md](UPGRADE.md) for update instructions
- 🔧 Check [PROTOCOL.md](PROTOCOL.md) if commands don't work
- ❓ See [FAQ.md](FAQ.md) for common questions
- 🎨 Try more [Lovelace examples](examples/lovelace.yaml)
- 🤖 Explore [automation examples](examples/configuration.yaml)

## Pro Tips

1. **Use automation to auto-shutoff** - Don't forget and drain your battery!
2. **Set up notifications** - Get alerted when heater turns on/off
3. **Create scenes** - Quick "Morning Warmup" or "Eco Mode" buttons
4. **Monitor error codes** - Check `climate.parking_heater` attributes
5. **Use timers** - Schedule heating before you need the car

## Safety Reminder ⚠️

- Never run heater in enclosed spaces
- Always ensure proper ventilation
- Set auto-shutoff timers
- Monitor fuel levels
- Follow manufacturer safety guidelines

---

**Enjoy your smart parking heater!** 🚗🔥

Need help? Check the [FAQ](FAQ.md) or open an issue on GitHub.
