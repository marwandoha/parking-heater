# Troubleshooting Connection Issues

## Error: TimeoutError during connection

This means the heater was found but connection timed out.

### Common Causes:

1. **Heater is connected to another device**
   - Close the AirHeaterBLE phone app completely
   - Check if Home Assistant is connected
   - Restart the heater to clear connections

2. **Wrong Bluetooth adapter**
   - Try without specifying adapter (uses default)
   - Try `hci0` instead of `hci1`

3. **Heater is too far away**
   - Move closer (< 5 meters)
   - Check signal strength (RSSI)

4. **Bluetooth permissions**
   - Run with sudo: `sudo python3 test_heater_connection.py`

---

## Quick Diagnostic Steps

### Step 1: Run the scanner

```bash
python3 scan_heater.py
```

This will:
- ✅ Check if your heater is visible
- ✅ Show signal strength (RSSI)
- ✅ List all nearby BLE devices
- ✅ Verify Bluetooth adapter works

### Step 2: Check Bluetooth status

```bash
# Check adapters
hciconfig -a

# Check if hci1 is up
hciconfig hci1

# If down, bring it up
sudo hciconfig hci1 up

# Scan with system tools
sudo hcitool -i hci1 lescan

# Check device info
bluetoothctl
> scan on
> devices
> exit
```

### Step 3: Check for existing connections

```bash
# List connected devices
bluetoothctl
> info E0:4E:7A:AD:EA:5D
> disconnect E0:4E:7A:AD:EA:5D
> exit
```

### Step 4: Try different approaches

**Option A: Use default adapter**

Edit `test_heater_connection.py`, change:
```python
BLUETOOTH_ADAPTER = None  # Use default instead of "hci1"
```

**Option B: Try hci0**
```python
BLUETOOTH_ADAPTER = "hci0"  # Try built-in Bluetooth
```

**Option C: Run with sudo**
```bash
sudo python3 test_heater_connection.py
```

---

## If Scanner Shows Heater

If `scan_heater.py` shows your heater but connection fails:

### The heater is likely paired to another device

1. **Power cycle the heater** (turn off and on)
2. **Close all phone apps** that might connect to it
3. **Disconnect from Home Assistant** if connected
4. **Try immediately** after power cycle

### Check signal strength

```
RSSI > -70 dBm  = Excellent (very close)
RSSI -70 to -80 = Good (should work)
RSSI -80 to -90 = Weak (might timeout)
RSSI < -90 dBm  = Too weak (won't connect)
```

If RSSI is low:
- Move Raspberry Pi closer to heater
- Move heater closer to Raspberry Pi
- Use a USB extension cable to position Bluetooth dongle better

---

## If Scanner DOESN'T Show Heater

1. **Verify heater is on**
   - Check display/lights
   - Try connecting with phone app

2. **Double-check MAC address**
   - On phone app: Look for device address
   - Format should be: `E0:4E:7A:AD:EA:5D`

3. **Try without adapter specification**
   ```python
   BLUETOOTH_ADAPTER = None
   ```

4. **Check Bluetooth is working**
   ```bash
   sudo systemctl status bluetooth
   sudo systemctl restart bluetooth
   ```

---

## Next Steps Based on Results

### If heater found + RSSI good:
→ Issue is connection/pairing. Try power cycling.

### If heater found + RSSI weak:
→ Move devices closer together.

### If heater NOT found:
→ Check MAC address, ensure heater is on, try phone app.

### If adapter errors:
→ Try default adapter or check Bluetooth service.

---

Run `python3 scan_heater.py` and share the output!
