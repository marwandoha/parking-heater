# Testing Guide

## Quick Test Script Usage

Use this to debug BLE connection without Home Assistant.

**Note**: Run this on your Raspberry Pi (or the machine with Bluetooth where Home Assistant runs).

### 1. Copy Script to Raspberry Pi

**Option A: Git Clone** (if you have git)
```bash
cd ~
git clone https://github.com/marwandoha/parking-heater.git
cd parking-heater
```

**Option B: Direct Download**
```bash
cd ~
wget https://raw.githubusercontent.com/marwandoha/parking-heater/main/test_heater_connection.py
```

**Option C: Manual Copy**
```bash
# From your Windows machine, use SCP:
scp test_heater_connection.py pi@your-pi-ip:~/
```

### 2. Install Requirements on Raspberry Pi

```bash
# SSH into your Raspberry Pi
ssh pi@your-pi-ip

# Install bleak
pip3 install bleak

# Or if you need sudo:
sudo pip3 install bleak
```

### 3. Edit Configuration (if needed)

```bash
nano test_heater_connection.py
```

Update these lines:
```python
HEATER_MAC = "E0:4E:7A:AD:EA:5D"  # Your heater MAC
BLUETOOTH_ADAPTER = "hci1"          # Your USB dongle (hci1)
PASSWORD = "1234"                    # Your heater password
```

Save and exit (Ctrl+X, Y, Enter)

### 4. Run Test Script

```bash
python3 test_heater_connection.py
```

### 3. What It Does

The script will:
1. ✅ Scan for your heater
2. ✅ Connect to it
3. ✅ Discover all services and characteristics
4. ✅ Test password authentication with multiple formats
5. ✅ Try sending commands
6. ✅ Show all responses

### 4. Configuration

Edit these variables in `test_heater_connection.py`:

```python
HEATER_MAC = "E0:4E:7A:AD:EA:5D"  # Your heater MAC
BLUETOOTH_ADAPTER = "hci1"          # Your USB dongle
PASSWORD = "1234"                    # Your heater password
```

### 5. Read Output

Look for:
- ✅ "Connected!" - Connection works
- 📋 List of services/characteristics - Note the UUIDs
- 🔑 Password authentication attempts
- 📨 Command responses

### 6. Debug Process

1. **If connection fails:**
   - Check MAC address
   - Check adapter (try "hci0" or "hci1")
   - Ensure heater is powered on
   - Check Bluetooth range

2. **If characteristics not found:**
   - Script will show all available UUIDs
   - Update `const.py` with correct UUIDs

3. **If password fails:**
   - Script tries multiple password formats
   - Note which format gets a response
   - Update code with working format

4. **If commands fail:**
   - Check response data
   - Decode the command structure
   - Update command format

### 7. Once Working

Copy the working:
- Service UUIDs
- Characteristic UUIDs  
- Password authentication method
- Command formats

Then update the Home Assistant integration files.

## Quick Commands

```bash
# Run test
python test_heater_connection.py

# With more debug
python test_heater_connection.py 2>&1 | tee test_output.log

# Check Bluetooth
hciconfig

# List adapters
hciconfig -a
```
