# Getting Started - Sports Ticker

Quick start guide to get your LED sports ticker up and running.

## Prerequisites

### Hardware Checklist
```
□ Raspberry Pi Pico 2W
□ 64x64 RGB LED Matrix (HUB75, 1/32 scan)
□ 5V/4A (or higher) power supply
□ 15+ jumper wires (male-to-female)
□ USB cable for Pico programming
```

### Software Checklist
```
□ MicroPython firmware for Pico 2W
□ Python 3.8+ on development computer
□ mpremote or Thonny IDE
□ Text editor (VS Code recommended)
```

## Quick Start (30 Minutes)

### Step 1: Flash MicroPython (5 min)

1. Download latest MicroPython for Pico 2W from [micropython.org](https://micropython.org/download/RPI_PICO2_W/)
2. Hold BOOTSEL button on Pico while plugging in USB
3. Drag .uf2 file to RPI-RP2 drive
4. Wait for Pico to restart

### Step 2: Wire Connections (10 min)

**Power connections:**
```
Power Supply → LED Matrix Input (+5V and GND)
Power Supply → Pico VSYS (Pin 39) and GND (Pin 38)
```

**Data connections (HUB75):**
```
Pico GP0  → R1     Pico GP6  → A      Pico GP11 → CLK
Pico GP1  → G1     Pico GP7  → B      Pico GP12 → LAT
Pico GP2  → B1     Pico GP8  → C      Pico GP13 → OE
Pico GP3  → R2     Pico GP9  → D      Pico GND  → GND
Pico GP4  → G2     Pico GP10 → E
Pico GP5  → B2
```

See [WIRING_GUIDE.md](WIRING_GUIDE.md) for detailed diagrams.

### Step 3: Upload Project Files (10 min)

**Install mpremote:**
```bash
pip install mpremote
```

**Upload files:**
```bash
# Navigate to project directory
cd sports-ticker/

# Upload all source files
mpremote fs cp -r src/ :

# Upload main files
mpremote fs cp main.py :
mpremote fs cp boot.py :
mpremote fs cp config.json :
```

**Create WiFi credentials:**
```bash
# Create secrets.py on your computer
echo 'WIFI_SSID = "YourNetworkName"' > secrets.py
echo 'WIFI_PASSWORD = "YourPassword"' >> secrets.py

# Upload to Pico
mpremote fs cp secrets.py :
```

### Step 4: Test (5 min)

**Power on and check:**
```bash
# Connect to serial console
mpremote repl

# You should see:
# - "Starting sports ticker..."
# - WiFi connection messages
# - IP address displayed
# - "Web server started on port 80"
```

**Open web interface:**
```
1. Note IP address from display or serial output
2. Open browser: http://PICO_IP_ADDRESS
3. Add your favorite teams
4. Save configuration
```

**Watch display:**
- Display should show startup message
- Then transition to idle mode or live scores
- Updates every 2 minutes

### Step 5: Configure Teams

**Via web interface:**
```
1. Go to http://PICO_IP_ADDRESS
2. Click "Add Team"
3. Select sport (NFL, NBA, MLB, NHL)
4. Search for team name
5. Click "Add"
6. Repeat for all favorite teams
7. Click "Save Changes"
```

Display updates within 2 minutes!

## Project Structure

```
sports-ticker/
├── README.md              ← Project overview
├── main.py               ← Main entry point
├── boot.py              ← Boot configuration
├── config.json          ← User settings
├── secrets.py           ← WiFi credentials (not in git)
│
├── src/                 ← Source code
│   ├── display/        ← LED matrix drivers
│   ├── api/           ← Sports API clients
│   ├── web/           ← Web server
│   └── utils/         ← Helper functions
│
├── tests/              ← Unit tests
│
└── docs/               ← Documentation
    ├── ARCHITECTURE.md  ← System design
    ├── CONTEXT.md       ← Development context
    ├── DESIGN.md        ← Visual design specs
    ├── TESTING.md       ← Test strategy
    ├── TROUBLESHOOTING.md ← Common issues
    └── WIRING_GUIDE.md    ← Hardware setup
```

## Documentation Guide

**Start here:**
1. **README.md** - Project overview and basic setup
2. **GETTING_STARTED.md** - This file (quick start)
3. **WIRING_GUIDE.md** - Detailed hardware connections

**For development:**
4. **CONTEXT.md** - Complete technical context for AI/developers
5. **ARCHITECTURE.md** - System design and module specs
6. **DESIGN.md** - UI/UX and visual design
7. **TESTING.md** - Testing strategy

**When things go wrong:**
8. **TROUBLESHOOTING.md** - Common problems and solutions

## Common First-Time Issues

### Display doesn't light up
```
□ Check power supply is 5V (not 12V!)
□ Verify power connections are tight
□ Check HUB75 cable is fully inserted
□ Verify Pico is programmed with code
```

### WiFi won't connect
```
□ Ensure WiFi is 2.4GHz (not 5GHz)
□ Check SSID and password in secrets.py
□ Verify Pico is in range of router
□ Try mobile hotspot to test
```

### No scores showing
```
□ Verify internet connection works
□ Check teams are configured
□ Confirm games are scheduled today
□ Look at serial console for errors
```

### Web interface not accessible
```
□ Note IP address from display at startup
□ Use http:// not https://
□ Ensure computer on same WiFi network
□ Try pinging the IP address
```

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed solutions.

## Development Workflow

### Making Code Changes

**Edit on computer:**
```bash
# 1. Edit files in your editor
nano src/display/renderer.py

# 2. Upload changed file
mpremote fs cp src/display/renderer.py :src/display/

# 3. Restart Pico (soft reset)
mpremote reset

# 4. Monitor output
mpremote repl
```

### Testing Changes

**Run tests on PC:**
```bash
pytest tests/ -v
```

**Test on hardware:**
```bash
mpremote run tests/test_display.py
```

### Debugging

**View logs:**
```bash
# Real-time console
mpremote repl

# File logging (if enabled)
mpremote fs cat :logs/debug.log
```

**Common debug commands:**
```python
import gc
print(f"Free memory: {gc.mem_free()}")

import network
wlan = network.WLAN(network.STA_IF)
print(f"Connected: {wlan.isconnected()}")
print(f"IP: {wlan.ifconfig()[0]}")
```

## Next Steps

Once basic setup works:

**Customize:**
- Adjust brightness in web interface
- Change update interval
- Configure quiet hours
- Add more teams

**Improve:**
- Add weather display (future feature)
- Custom team logos
- Sound alerts for scores
- Mobile app (future)

**Maintain:**
- Check for code updates
- Update team configurations
- Monitor for API changes
- Clean display periodically

## Getting Help

**If you're stuck:**

1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Review serial console output for errors
3. Verify hardware connections
4. Test with example code
5. Check documentation for your specific issue

**Information to gather when asking for help:**
```
□ Exact error message
□ What you were doing when it happened
□ Serial console output
□ Hardware configuration
□ What you've already tried
```

## Timeline Estimate

**Complete beginner:** 2-3 hours total
- Hardware assembly: 30 min
- Software setup: 45 min
- Configuration: 15 min
- Troubleshooting: 30-60 min

**Experienced maker:** 30-60 minutes total
- Hardware assembly: 15 min
- Software setup: 15 min
- Configuration: 5 min
- Testing: 10 min

## Success Criteria

You've successfully completed setup when:

```
✓ Display shows startup message
✓ WiFi connects automatically
✓ Web interface is accessible
✓ Teams are configured
✓ Scores display and update
✓ System runs stable for 1+ hour
```

## What's Next?

**Gift giving:**
- Let it run for 24 hours as burn-in test
- Prepare instructions for recipient
- Include WiFi setup details
- Provide web interface URL

**Future enhancements:**
- See ARCHITECTURE.md for planned features
- Join community forums for ideas
- Contribute improvements back to project

## Quick Reference

**Essential Commands:**
```bash
# Upload file
mpremote fs cp file.py :

# Upload directory
mpremote fs cp -r src/ :

# View file
mpremote fs cat :main.py

# Delete file
mpremote fs rm :old_file.py

# Serial console
mpremote repl

# Soft reset
mpremote reset

# Run script
mpremote run test.py
```

**Important Pins:**
```
VSYS (39) ← 5V power input
GND (38)  ← Ground
GP0-13    ← HUB75 data lines
```

**Critical Safety:**
```
⚠️ Always use 5V power (never 12V)
⚠️ Connect common ground
⚠️ Check connections before powering on
⚠️ Monitor for heat/smoke on first power-up
```

## Resources

**Official Documentation:**
- MicroPython: https://docs.micropython.org
- Pico 2W: https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf
- ESPN API: https://gist.github.com/nntrn/ee26cb2a0716de0947a0a4e9a157bc1c

**Tools:**
- mpremote: https://docs.micropython.org/en/latest/reference/mpremote.html
- Thonny IDE: https://thonny.org

**Community:**
- MicroPython Forum: https://forum.micropython.org
- Raspberry Pi Forums: https://forums.raspberrypi.com

## Final Checklist

Before considering project complete:

```
Hardware:
□ All connections secure
□ Power supply is 5V/4A or higher
□ No loose wires
□ Display mounted safely
□ Ventilation adequate

Software:
□ Code uploaded successfully
□ WiFi credentials configured
□ Teams added
□ Settings optimized
□ Tested for 24+ hours

Documentation:
□ Recipient instructions prepared
□ WiFi setup details documented
□ Troubleshooting guide accessible
□ Contact info for support

Gift Presentation:
□ Device cleaned
□ Cables organized
□ Instructions included
□ Power supply included
□ Ready to plug in and use
```

Congratulations! Your sports ticker is ready! 🎉
