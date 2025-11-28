#!/bin/bash

# Disconnect heater if connected
echo "Disconnecting heater if connected..."
bluetoothctl disconnect E0:4E:7A:AD:E8:EE 2>/dev/null
sleep 2

# Run the test
echo "Running connection test..."
python3 test_heater_connection.py
