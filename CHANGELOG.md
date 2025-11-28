# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2025-11-28

### Added
- Initial release of Parking Heater BLE integration
- Full climate entity support with temperature control (8-36°C)
- Fan speed control (5 levels)
- Power on/off control
- Automatic Bluetooth device discovery
- Manual MAC address entry option
- Real-time status updates every 30 seconds
- Error code monitoring
- Config flow for easy setup through UI
- Support for multiple heaters
- Connection retry logic
- Proper Home Assistant device registry integration

### Features
- Climate entity with HVAC modes (off, heat)
- Target temperature setting
- Current temperature monitoring
- Fan mode control (1-5 speed levels)
- Automatic reconnection on connection loss
- BLE notifications for real-time updates

### Documentation
- Complete README with usage examples
- Installation guide
- Protocol documentation for developers
- Lovelace card examples
- Automation examples
- Troubleshooting guide

### Technical
- Built with Home Assistant 2023.1+ architecture
- Uses bleak library for cross-platform BLE support
- Implements DataUpdateCoordinator for efficient updates
- Proper error handling and logging
- Async/await throughout
- Type hints for better code quality

## [Unreleased]

### Planned Features
- Timer/scheduler support
- Altitude compensation settings
- Advanced diagnostics sensor
- Battery voltage monitoring
- Fuel level estimation
- Multiple heater profiles
- Integration with Home Assistant energy dashboard
