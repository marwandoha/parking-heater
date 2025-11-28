#!/bin/bash

# Quick setup script for testing on Raspberry Pi
# Run this on your Raspberry Pi to set everything up

echo "=================================================="
echo "Parking Heater BLE Test Setup"
echo "=================================================="
echo ""

# Check if Python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Installing..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip
else
    echo "✅ Python3 found: $(python3 --version)"
fi

# Install bleak
echo ""
echo "📦 Installing bleak library..."
pip3 install --user bleak

# Check Bluetooth
echo ""
echo "🔍 Checking Bluetooth adapters..."
hciconfig

echo ""
echo "=================================================="
echo "✅ Setup complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Edit test_heater_connection.py with your heater's MAC address"
echo "2. Run: python3 test_heater_connection.py"
echo ""
