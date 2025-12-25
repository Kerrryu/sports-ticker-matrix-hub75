# Pico 2W Deployment Guide

Complete guide for deploying the Sports Ticker to Raspberry Pi Pico 2W hardware.

## Table of Contents

1. [Hardware Preparation](#hardware-preparation)
2. [Initial Setup](#initial-setup)
3. [First Deployment](#first-deployment)
4. [Testing & Validation](#testing--validation)
5. [OTA Updates](#ota-updates)
6. [Troubleshooting](#troubleshooting)

---

## Hardware Preparation

### What You Need

```
Hardware:
□ Raspberry Pi Pico 2W (RP2350 chip, built-in WiFi)
□ 64x64 RGB LED Matrix (HUB75, 1/32 scan rate)
□ 5V 4A+ Power Supply (DO NOT USE 12V!)
□ 15+ Dupont jumper wires (female-to-female)
□ USB-C cable for programming

Tools:
□ Computer with USB port
□ Multimeter (recommended for power verification)
```

### Pico 2W vs Pico W Differences

The Pico 2W uses the **RP2350** chip (vs RP2040 in original Pico):
- Dual ARM Cortex-M33 cores at 150MHz
- 520KB SRAM (vs 264KB)
- Better floating-point performance
- Same WiFi chip (CYW43439)
- **Same MicroPython deployment process**

---

## Initial Setup

### Step 1: Download MicroPython Firmware

1. Go to: https://micropython.org/download/RPI_PICO2_W/
2. Download the latest `.uf2` file
3. Note the version (e.g., `v1.22.0`)

> **Important**: Use the `RPI_PICO2_W` firmware, NOT `RPI_PICO_W` (that's for original Pico W)

### Step 2: Flash MicroPython

```bash
# 1. Hold BOOTSEL button on Pico 2W
# 2. While holding, connect USB cable to computer
# 3. Release BOOTSEL after connecting
# 4. A drive named "RPI-RP2" should appear

# On macOS:
cp ~/Downloads/RPI_PICO2_W-*.uf2 /Volumes/RPI-RP2/

# On Linux:
cp ~/Downloads/RPI_PICO2_W-*.uf2 /media/$USER/RPI-RP2/

# On Windows:
# Drag and drop the .uf2 file to the RPI-RP2 drive
```

5. Wait 10-15 seconds for the Pico to flash and restart
6. The RPI-RP2 drive will disappear - this is normal

### Step 3: Install Development Tools

```bash
# Install mpremote (official MicroPython tool)
pip install mpremote

# Verify installation
mpremote --version

# Test connection to Pico
mpremote connect list
# Should show something like: /dev/tty.usbmodem1234 (or COM3 on Windows)
```

### Step 4: Verify MicroPython is Working

```bash
# Connect to REPL
mpremote repl

# You should see:
# MicroPython v1.22.0 on 2024-01-01; Raspberry Pi Pico 2 W with RP2350
# Type "help()" for more information.
# >>>

# Test WiFi chip is recognized
>>> import network
>>> wlan = network.WLAN(network.STA_IF)
>>> wlan.active(True)
True

# Exit REPL with Ctrl+X
```

---

## First Deployment

### Step 1: Prepare Project Files

Ensure your project structure looks like:

```
sports_ticker_matrix/
├── src/
│   ├── display/
│   │   ├── __init__.py
│   │   ├── hub75.py
│   │   ├── renderer.py
│   │   ├── fonts.py
│   │   └── simulator.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── espn.py
│   │   ├── parser.py
│   │   └── cache.py
│   ├── web/
│   │   ├── __init__.py
│   │   ├── server.py
│   │   ├── routes.py
│   │   └── templates.py
│   ├── ota/
│   │   ├── __init__.py
│   │   ├── updater.py
│   │   └── routes.py
│   └── utils/
│       ├── __init__.py
│       ├── config.py
│       ├── network.py
│       ├── logger.py
│       └── time_utils.py
├── boot.py
├── main.py
├── config.json
├── version.json
└── secrets.py  (you'll create this)
```

### Step 2: Create WiFi Credentials

Create `secrets.py` in the project root:

```python
# secrets.py - DO NOT COMMIT TO GIT
WIFI_SSID = "YourWiFiNetworkName"
WIFI_PASSWORD = "YourWiFiPassword"
```

> **Note**: Pico 2W only supports 2.4GHz WiFi, not 5GHz

### Step 3: Deploy Files to Pico

```bash
# Navigate to project directory
cd /path/to/sports_ticker_matrix

# Create directory structure on Pico
mpremote mkdir :src
mpremote mkdir :src/display
mpremote mkdir :src/api
mpremote mkdir :src/web
mpremote mkdir :src/ota
mpremote mkdir :src/utils

# Upload source modules
mpremote cp -r src/display/* :src/display/
mpremote cp -r src/api/* :src/api/
mpremote cp -r src/web/* :src/web/
mpremote cp -r src/ota/* :src/ota/
mpremote cp -r src/utils/* :src/utils/

# Upload main files
mpremote cp boot.py :
mpremote cp main.py :
mpremote cp config.json :
mpremote cp version.json :
mpremote cp secrets.py :

# Verify files are uploaded
mpremote ls :
mpremote ls :src/display/
```

### Step 4: First Boot (Software Only)

**Before connecting LED matrix**, test WiFi connectivity:

```bash
# Reset Pico to run the code
mpremote reset

# Connect to REPL to see output
mpremote repl

# You should see:
# Starting sports ticker...
# Connecting to WiFi...
# Connected! IP: 192.168.1.XXX
# Web server started on port 80
```

Record the IP address - you'll need it to access the web interface.

### Step 5: Wire the LED Matrix

**CRITICAL SAFETY STEPS**:

```
⚠️  VERIFY POWER SUPPLY IS 5V BEFORE CONNECTING
⚠️  USE MULTIMETER TO CONFIRM VOLTAGE
⚠️  12V WILL DESTROY COMPONENTS INSTANTLY
```

**Wiring Diagram**:

```
Power Supply (5V 4A)
    ├── +5V ────┬──► LED Matrix Power Input (+)
    │           └──► Pico VSYS (Pin 39)
    │
    └── GND ────┬──► LED Matrix Power Input (-)
                └──► Pico GND (Pin 38)


Pico GPIO ──► HUB75 Connector
    GP0  ──► R1  (Red Upper)
    GP1  ──► G1  (Green Upper)
    GP2  ──► B1  (Blue Upper)
    GP3  ──► R2  (Red Lower)
    GP4  ──► G2  (Green Lower)
    GP5  ──► B2  (Blue Lower)
    GP6  ──► CLK (Clock)
    GP7  ──► LAT (Latch)
    GP8  ──► OE  (Output Enable)
    GP9  ──► A   (Row Select)
    GP10 ──► B   (Row Select)
    GP11 ──► C   (Row Select)
    GP12 ──► D   (Row Select)
    GP13 ──► E   (Row Select)
    GND  ──► GND (Signal Ground)
```

### Step 6: First Power-On with Display

```bash
# 1. Double-check all connections
# 2. Have finger ready to unplug power
# 3. Apply power

# Monitor for first 30 seconds:
# - No smoke or burning smell
# - No excessive heat
# - Display should illuminate

# Connect to REPL to see any errors
mpremote repl
```

---

## Testing & Validation

### Test 1: Display Test

```bash
# Run display test script
mpremote run tests/test_display_hardware.py
```

Or via REPL:

```python
>>> from src.display import HUB75Display
>>> display = HUB75Display(64, 64)
>>>
>>> # Fill screen with red
>>> for y in range(64):
...     for x in range(64):
...         display.set_pixel(x, y, 255, 0, 0)
>>> display.show()
>>>
>>> # Clear screen
>>> display.clear()
>>> display.show()
```

### Test 2: WiFi Connectivity

```python
>>> from src.utils import NetworkManager
>>> nm = NetworkManager()
>>> nm.connect()
>>> print(f"IP: {nm.get_ip()}")
>>> print(f"RSSI: {nm.get_rssi()} dBm")
```

### Test 3: Web Interface

1. Open browser to `http://PICO_IP_ADDRESS`
2. You should see the Sports Ticker configuration page
3. Add a test team
4. Verify it saves (check config.json on Pico)

### Test 4: ESPN API

```python
>>> from src.api import ESPNClient
>>> client = ESPNClient()
>>> scores = client.get_scores('nfl')
>>> print(f"Found {len(scores)} games")
>>> for game in scores[:2]:
...     print(f"  {game['away_team']} @ {game['home_team']}")
```

### Test 5: Full Integration

Let the system run for 10+ minutes:
- Verify scores update
- Check display transitions work
- Monitor for memory issues
- Verify web interface stays responsive

```python
>>> import gc
>>> print(f"Free memory: {gc.mem_free()} bytes")
# Should be > 50000 bytes
```

---

## OTA Updates

### How OTA Works

The OTA system allows remote updates without USB connection:

1. Place new version files on a web server
2. Access the update page on the Pico
3. Pico downloads, verifies, and installs
4. Automatic rollback if update fails

### Setting Up Update Server

**Option A: GitHub Releases** (Recommended)

1. Create a GitHub repository
2. Create a release with version tag (e.g., `v1.0.1`)
3. Upload version.json and src.zip to release assets

**Option B: Local Web Server**

```bash
# Start simple HTTP server in project directory
cd sports_ticker_matrix
python -m http.server 8000

# Update URL becomes: http://YOUR_COMPUTER_IP:8000/
```

### Preparing an Update

1. **Update version.json**:

```json
{
    "version": "1.0.1",
    "release_date": "2024-12-25",
    "changelog": "Fixed display refresh, improved WiFi stability",
    "min_micropython": "1.22.0",
    "files": {
        "main.py": "abc123...",
        "src/display/hub75.py": "def456..."
    }
}
```

2. **Create update package** (if using zip method):

```bash
zip -r update-1.0.1.zip src/ main.py boot.py config.json version.json
```

### Deploying an Update

**Via Web Interface**:

1. Navigate to `http://PICO_IP/update`
2. Click "Check for Updates"
3. Review changelog
4. Click "Install Update"
5. Wait for completion (do NOT power off!)

**Via API**:

```bash
# Check for updates
curl http://PICO_IP/api/update/check

# Install update
curl -X POST http://PICO_IP/api/update/install

# Check status
curl http://PICO_IP/api/update/status
```

### Rollback Procedure

If an update fails:

**Automatic Rollback**: The system detects boot failures and auto-rollbacks after 3 failed attempts.

**Manual Rollback**:

```bash
# Via web interface
# Go to http://PICO_IP/update and click "Rollback to Previous"

# Via API
curl -X POST http://PICO_IP/api/update/rollback

# Via REPL (if web is down)
mpremote repl
>>> from src.ota import OTAUpdater
>>> updater = OTAUpdater("http://example.com")
>>> updater.rollback()
```

### Emergency Recovery

If the Pico won't boot at all:

1. Hold BOOTSEL and connect USB
2. It will appear as RPI-RP2 drive again
3. Re-flash MicroPython
4. Re-deploy all files from scratch

---

## Deployment Checklist

### Initial Deployment

```
Pre-Deployment:
□ MicroPython firmware downloaded (RPI_PICO2_W)
□ mpremote installed and working
□ secrets.py created with WiFi credentials
□ All source files ready

Flashing:
□ BOOTSEL held while connecting
□ Firmware .uf2 copied to RPI-RP2
□ Pico restarted successfully
□ MicroPython REPL accessible

File Upload:
□ Directory structure created
□ All src/ modules uploaded
□ boot.py, main.py uploaded
□ config.json, version.json uploaded
□ secrets.py uploaded (not in git!)

Software Test:
□ WiFi connects
□ IP address displayed
□ Web interface accessible
□ ESPN API working

Hardware Test:
□ Power supply verified 5V
□ All wires connected per diagram
□ Display lights up
□ No smoke/heat
□ Colors correct

Integration Test:
□ Scores display correctly
□ Web interface controls work
□ System stable for 10+ minutes
□ Memory usage acceptable
```

### OTA Update Deployment

```
Preparation:
□ Version number incremented in version.json
□ Changelog updated
□ All changes tested locally
□ Update package created

Deployment:
□ Update files hosted on server
□ Check for Updates shows new version
□ Changelog displays correctly
□ Install Update initiated
□ Update completed successfully
□ Version number updated on Pico

Validation:
□ All features still working
□ No errors in console
□ Web interface responsive
□ Previous config preserved
```

---

## Troubleshooting

### "No module named 'src.display'"

Files weren't uploaded correctly:
```bash
mpremote ls :src/display/
# Should show __init__.py, hub75.py, etc.

# Re-upload if missing
mpremote cp -r src/display/* :src/display/
```

### "WiFi connection failed"

```python
# Check WiFi credentials
>>> import secrets
>>> print(secrets.WIFI_SSID)
>>> print(len(secrets.WIFI_PASSWORD))

# Try manual connection
>>> import network
>>> wlan = network.WLAN(network.STA_IF)
>>> wlan.active(True)
>>> wlan.connect("SSID", "PASSWORD")
>>> wlan.isconnected()  # Wait and retry
```

### Display shows garbage/wrong colors

1. Check GPIO pin assignments in hub75.py
2. Verify all data wires connected
3. Try swapping R1/G1/B1 connections
4. Check for loose connections

### Out of memory errors

```python
>>> import gc
>>> gc.collect()
>>> print(gc.mem_free())

# If too low, check for:
# - Large log files
# - Cached data not being cleared
# - Memory leaks in loops
```

### OTA update fails

```python
# Check network connectivity
>>> import urequests
>>> r = urequests.get("http://update-server/version.json")
>>> print(r.status_code)

# Check available space
>>> import os
>>> os.statvfs('/')
```

---

## Quick Reference Commands

```bash
# Connect to Pico
mpremote connect list          # List devices
mpremote repl                  # Interactive Python
mpremote reset                 # Restart Pico

# File operations
mpremote ls :                  # List root
mpremote ls :src/display/      # List directory
mpremote cp file.py :          # Upload file
mpremote cp :file.py ./        # Download file
mpremote rm :file.py           # Delete file
mpremote mkdir :dirname        # Create directory

# Running code
mpremote run script.py         # Run local script on Pico
mpremote exec "print('hi')"    # Run Python statement

# Bulk operations
mpremote cp -r src/* :src/     # Upload directory recursively
```

---

## Version History

| Version | Date | Notes |
|---------|------|-------|
| 1.0.0 | 2024-12-25 | Initial release |

---

## Support

If you encounter issues not covered here:

1. Check `docs/TROUBLESHOOTING.md` for common problems
2. Review serial console output for error messages
3. Verify hardware connections match wiring diagram
4. Test individual components in isolation

For OTA-specific issues, check the update history at `http://PICO_IP/api/update/history`
