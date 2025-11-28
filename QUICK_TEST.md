# Quick Start - Testing on Raspberry Pi

## Method 1: Quick Copy & Run

On your **Windows machine**, copy the test script:

```powershell
# Copy to clipboard
Get-Content test_heater_connection.py | Set-Clipboard
```

Then on your **Raspberry Pi** (via SSH):

```bash
# Create file
nano test_heater.py

# Paste the content (Ctrl+Shift+V or right-click)
# Save and exit (Ctrl+X, Y, Enter)

# Install bleak (choose ONE)
sudo apt install -y python3-bleak
# OR: pip3 install bleak --break-system-packages

# Run test
python3 test_heater.py
```

---

## Method 2: Git Clone (Recommended)

On your **Raspberry Pi**:

```bash
# Clone repo
cd ~
git clone https://github.com/marwandoha/parking-heater.git
cd parking-heater

# Install requirements (choose ONE)
sudo apt install -y python3-bleak
# OR: pip3 install bleak --break-system-packages

# Run test
python3 test_heater_connection.py
```

---

## Method 3: Direct Download

On your **Raspberry Pi**:

```bash
# Download script
wget https://raw.githubusercontent.com/marwandoha/parking-heater/main/test_heater_connection.py

# Install bleak (choose ONE)
sudo apt install -y python3-bleak
# OR: pip3 install bleak --break-system-packages

# Run test
python3 test_heater_connection.py
```

---

## What to Look For

The script will show:

```
✅ Connected!
📋 Available Services:
   🔧 Service: 0000fff0-...
      📝 Char: 0000fff1-... - Properties: ['write']
      📝 Char: 0000fff2-... - Properties: ['notify']
```

**Important**: Note down:
- ✅ Service UUIDs that exist
- ✅ Characteristic UUIDs that exist
- ✅ Which password format works
- ✅ Command responses

---

## Configuration Already Set

The script is pre-configured with:
- **MAC**: `E0:4E:7A:AD:EA:5D`
- **Adapter**: `hci1` (your USB dongle)
- **Password**: `1234`

If these are wrong, edit the file:
```bash
nano test_heater_connection.py
```

---

## Troubleshooting

**Script not found?**
```bash
# Make sure you're in the right directory
ls -la test_heater_connection.py
```

**Bluetooth issues?**
```bash
# Check adapters
hciconfig -a

# Check if hci1 exists
hciconfig hci1
```

**Permission denied?**
```bash
# Run with sudo if needed
sudo python3 test_heater_connection.py
```

---

Once the script shows what UUIDs and commands work, we'll update the Home Assistant integration!
