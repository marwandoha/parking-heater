"""Test configuration for Parking Heater integration."""
import pytest
from homeassistant.core import HomeAssistant


@pytest.fixture
def mock_bluetooth_adapters():
    """Mock Bluetooth adapters."""
    return [
        {
            "address": "00:00:00:00:00:01",
            "name": "hci0",
            "available": True,
        }
    ]


@pytest.fixture
def mock_heater_data():
    """Mock heater data."""
    return {
        "is_on": True,
        "target_temperature": 22,
        "current_temperature": 20,
        "fan_speed": 3,
        "error_code": 0,
    }


@pytest.fixture
def mock_mac_address():
    """Mock MAC address."""
    return "A4:C1:38:12:34:56"
