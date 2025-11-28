#!/bin/bash

# Disconnect heater if connected
echo "Disconnecting heater if connected..."
bluetoothctl disconnect E0:4E:7A:AD:EA:5D 2>/dev/null
sleep 2

# Run the test and save output
echo "Running connection test..."
python3 test_heater_connection.py 2>&1 | tee test_output.log
