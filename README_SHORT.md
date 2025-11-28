# 🔥 Parking Heater BLE Integration for Home Assistant

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2023.1%2B-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

Control your Bluetooth parking heater (compatible with AirHeaterBLE app) directly from Home Assistant!

---

## ⚡ Quick Start

```bash
# 1. Copy integration to Home Assistant
# 2. Restart Home Assistant  
# 3. Go to Settings → Devices & Services → Add Integration
# 4. Search "Parking Heater BLE"
# 5. Follow setup wizard
```

**Full guide**: See [QUICKSTART.md](QUICKSTART.md)

---

## ✨ Features

| Feature | Status |
|---------|--------|
| 🌡️ Temperature Control (8-36°C) | ✅ |
| 🌀 Fan Speed Control (1-5) | ✅ |
| ⚡ Power On/Off | ✅ |
| 📊 Real-time Status | ✅ |
| 🔍 Auto-Discovery | ✅ |
| 🔄 Auto-Reconnect | ✅ |
| 🎯 Multiple Heaters | ✅ |
| ❌ Error Detection | ✅ |
| 🤖 Full Automation Support | ✅ |

---

## 📸 Screenshots

*Add your screenshots here after testing*

### Dashboard View
![Dashboard](docs/images/dashboard.png)

### Climate Control
![Climate Control](docs/images/climate.png)

### Automation Example
![Automation](docs/images/automation.png)

---

## 🎯 Use Cases

- ⏰ **Morning Routine**: Warm car automatically before work
- 🌡️ **Temperature-Based**: Auto-start when it's freezing outside  
- ⏱️ **Timed Warmup**: Schedule heating 30 minutes before departure
- 🔋 **Safety**: Auto-shutoff to prevent battery drain
- 📱 **Remote Control**: Start heater from anywhere with HA Cloud
- 🏠 **Scenes**: "Morning Departure" scene includes car heating

---

## 📦 Installation

### Requirements
- Home Assistant 2023.1 or newer
- Bluetooth adapter (built-in or USB dongle)
- Parking heater compatible with AirHeaterBLE app

### Option 1: HACS (Recommended)
1. Open HACS → Integrations
2. Add custom repository (when published)
3. Search "Parking Heater BLE"
4. Install and restart HA

### Option 2: Manual
1. Copy `custom_components/parking_heater` to your config folder
2. Restart Home Assistant
3. Add integration via UI

**Detailed instructions**: [INSTALLATION.md](INSTALLATION.md)

---

## 🎮 Basic Usage

### Dashboard Card
```yaml
type: thermostat
entity: climate.parking_heater
```

### Turn On Automation
```yaml
service: climate.set_hvac_mode
target:
  entity_id: climate.parking_heater
data:
  hvac_mode: heat
```

### Set Temperature
```yaml
service: climate.set_temperature
target:
  entity_id: climate.parking_heater
data:
  temperature: 22
```

**More examples**: [examples/](examples/)

---

## 🤖 Automation Examples

### Morning Warmup
```yaml
alias: "Warm car before work"
trigger:
  - platform: time
    at: "07:00:00"
condition:
  - condition: time
    weekday: [mon, tue, wed, thu, fri]
action:
  - service: climate.turn_on
    target:
      entity_id: climate.parking_heater
  - service: climate.set_temperature
    target:
      entity_id: climate.parking_heater
    data:
      temperature: 22
```

### Auto Shutoff
```yaml
alias: "Auto turn off after 30 min"
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

**More automations**: [examples/configuration.yaml](examples/configuration.yaml)

---

## 🔧 Configuration

The integration is configured entirely through the UI. No YAML required!

### Find Your Heater's MAC Address

**Method 1: Auto-Discovery**
- Integration will scan and find your heater automatically

**Method 2: AirHeaterBLE App**
- Open app → Connect to heater → Note MAC address

**Method 3: Bluetooth Scanner**
- Android: nRF Connect app
- iOS: LightBlue app

---

## 📚 Documentation

- 📖 [README.md](README.md) - Complete documentation
- 🚀 [QUICKSTART.md](QUICKSTART.md) - 5-minute setup guide
- 💾 [INSTALLATION.md](INSTALLATION.md) - Detailed installation
- 🔌 [PROTOCOL.md](PROTOCOL.md) - Bluetooth protocol details
- ❓ [FAQ.md](FAQ.md) - Common questions & troubleshooting
- 📝 [CHANGELOG.md](CHANGELOG.md) - Version history

---

## 🐛 Troubleshooting

### Device Not Found
- Ensure heater is powered on
- Check Bluetooth range (< 10m)
- Disconnect phone app if running

### Cannot Connect
- Only one device can connect at a time
- Power cycle the heater
- Restart HA Bluetooth integration

### Commands Don't Work
- Your heater may use different protocol
- See [PROTOCOL.md](PROTOCOL.md) for reverse engineering
- Check logs with debug enabled

**More help**: [FAQ.md](FAQ.md)

---

## 🔍 Debug Logging

Add to `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.parking_heater: debug
    bleak: debug
```

---

## ⚠️ Important Notes

### Protocol Compatibility
The BLE protocol is based on common Chinese parking heaters. **Your specific model may need adjustments**:

1. Test with your heater first
2. If commands don't work, see [PROTOCOL.md](PROTOCOL.md)
3. May need to reverse engineer using nRF Connect
4. Update `const.py` with correct commands

### Safety First
- ⚠️ Never run heater in enclosed spaces
- ⏱️ Always set auto-shutoff timers
- 🔋 Monitor battery levels
- 📖 Follow manufacturer safety guidelines

### Bluetooth Limitations
- Only ONE connection at a time (HA or phone app, not both)
- Range typically 10 meters
- Metal car body may reduce range

---

## 🗺️ Roadmap

Future features under consideration:
- [ ] Built-in timer/scheduler
- [ ] Battery voltage monitoring
- [ ] Fuel level estimation
- [ ] Energy dashboard integration
- [ ] Altitude compensation
- [ ] Runtime statistics
- [ ] More heater models

---

## 🤝 Contributing

Contributions welcome! Ways to help:
- 🧪 Test with different heater models
- 📝 Document protocol variations
- 🐛 Report bugs (with logs)
- 💡 Suggest features
- 🌍 Translate to other languages
- 📖 Improve documentation

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details

---

## 🙏 Credits

- Inspired by the AirHeaterBLE Android app
- Built with [bleak](https://github.com/hbldh/bleak) for BLE support
- Uses Home Assistant's modern integration architecture

---

## 📞 Support

- 📚 Check [FAQ.md](FAQ.md) first
- 🐛 [Open an issue](https://github.com/yourusername/parking_heater/issues) on GitHub
- 💬 Home Assistant Community Forum
- 💭 Home Assistant Discord

---

## ⭐ Show Your Support

If this integration helps you, please:
- ⭐ Star this repository
- 🐛 Report issues
- 📝 Improve documentation
- 💝 Share with others

---

**Made with ❤️ for the Home Assistant community**

*Control your parking heater, automate your life!* 🚗🔥🏠
