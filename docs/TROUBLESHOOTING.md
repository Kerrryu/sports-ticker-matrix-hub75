# Sports Ticker - Troubleshooting Guide

## Critical Safety Warning ⚠️

### VOLTAGE IS CRITICAL - ALWAYS USE 5V

**The #1 mistake that destroys this project: Using wrong voltage**

```
✅ CORRECT: 5V power supply (4.75V - 5.25V acceptable)
❌ WRONG:   12V power supply (instant component destruction)
❌ WRONG:   9V power supply (still too high)
❌ WRONG:   Any voltage other than 5V
```

### What Happens If You Use 12V

**Real incident from this project:**
- Connected 12V/5A to components designed for 5V
- Components released smoke within seconds
- Brown/burned solder joints around power input
- Likely damage: voltage regulators, input capacitors, possibly LED drivers
- Cost: $25-30 for replacement matrix

**Symptoms of 12V damage:**
- Immediate heat (components get very hot very fast)
- Smoke (white/gray smoke from overloaded components)
- Burning smell (distinct acrid electronics smell)
- Brown/discolored solder joints
- Component failure

**If this happens to you:**
1. **UNPLUG IMMEDIATELY** - Don't wait to "see what happens"
2. Let everything cool down (15+ minutes)
3. Inspect for visible damage (brown solder, burned components)
4. Do NOT attempt to power on again with wrong voltage
5. Get correct 5V supply before testing
6. Order replacement if damaged (LED matrix ~$25, Pico ~$8)

### How to Verify Your Power Supply

**ALWAYS check the label before connecting:**

**SAFE (Example of correct label):**
```
INPUT:  100-240V AC 50/60Hz
OUTPUT: DC 5V ⎓ 4A
        or
OUTPUT: 5.0V 4000mA
```

**DANGEROUS (Wrong voltage):**
```
OUTPUT: DC 12V ⎓ 5A     ← Will destroy components
OUTPUT: 9V 1000mA       ← Still too high
OUTPUT: 3.3V 2A         ← Too low, won't work
```

**Key things to check:**
1. Output voltage MUST say "5V" (or 5.0V)
2. Current (amps) should be 4A or higher (5A ideal)
3. When in doubt, measure with multimeter BEFORE connecting

### Voltage vs Current - Understanding The Difference

**Voltage (Volts):**
- Like water pressure in a pipe
- **MUST match exactly** - 5V for this project
- Too high = destroys components (like too much water pressure bursts pipe)
- Too low = won't work (like not enough pressure to reach top floor)

**Current (Amps):**
- Like pipe diameter / water flow rate
- Device draws only what it needs
- **Higher is fine** - having more available doesn't hurt
- Too low = dim display or brownouts, but won't damage components

**Examples:**
```
5V/4A   ✅ Perfect
5V/5A   ✅ Ideal (extra headroom)
5V/10A  ✅ Overkill but totally safe
12V/4A  ❌ DESTROYS EVERYTHING (wrong voltage)
12V/1A  ❌ Still destroys (voltage still wrong)
5V/2A   ⚠️ Works but dim (not enough current)
```

## Common Problems and Solutions

### Display Issues

#### No Display At All

**Symptoms:**
- Matrix completely dark
- No LEDs light up
- No signs of life

**Possible Causes:**
1. **Power supply not connected or wrong voltage**
   - Check: Is power supply plugged in?
   - Check: Is voltage 5V (not 12V)?
   - Check: Are power connections tight?
   - Test: Measure voltage at matrix input with multimeter

2. **HUB75 cable not connected**
   - Check: Is ribbon cable fully inserted?
   - Check: Is cable in correct orientation?
   - Test: Remove and reconnect cable firmly

3. **Pico not programmed**
   - Check: Is code uploaded to Pico?
   - Check: Does Pico have MicroPython firmware?
   - Test: Connect Pico to USB and verify it's recognized

4. **Component damage (12V incident)**
   - Check: Any brown solder or burn marks?
   - Check: Any burning smell?
   - Test: Replace matrix if visibly damaged

**Solutions:**
```
1. Verify 5V power supply connected and ON
2. Check all connections are secure
3. Upload fresh code to Pico
4. Try with just power (no data) - some LEDs should light randomly
5. If nothing works after checking above, likely hardware failure
```

#### Partial Display / Dead Sections

**Symptoms:**
- Some rows or columns don't light up
- Checkerboard pattern of dead pixels
- One color missing (no red, green, or blue)

**Possible Causes:**
1. **Loose HUB75 connection**
   - Check: Cable seated properly?
   - Test: Wiggle cable gently while powered

2. **Wrong pin mapping**
   - Check: Verify GPIO pins match code
   - Test: Try example HUB75 code first

3. **Damaged matrix sections**
   - Check: Physical damage visible?
   - Test: If same sections always dead = hardware issue

**Solutions:**
```
1. Reconnect HUB75 cable firmly
2. Verify pin definitions in code match physical wiring
3. Test with known-good example code
4. If problem persists, likely component damage
```

#### Flickering Display

**Symptoms:**
- Display flickers or strobes
- Brightness varies
- Colors flash randomly

**Possible Causes:**
1. **Insufficient power supply**
   - Check: Is supply rated for 4A minimum?
   - Test: Reduce brightness, does flickering stop?
   - Measure: Voltage under load (should stay >4.75V)

2. **Refresh rate too slow**
   - Check: Is Pico overloaded with tasks?
   - Test: Disable API polling temporarily
   - Solution: Optimize display refresh code

3. **Poor power connections**
   - Check: Loose wires to power input?
   - Test: Wiggle power wires, does flicker change?
   - Solution: Secure all power connections

**Solutions:**
```
1. Upgrade to 5V/5A or higher power supply
2. Add bulk capacitor (1000µF) near matrix power input
3. Lower display brightness in code
4. Optimize refresh rate in display driver
5. Check for loose ground connections
```

#### Wrong Colors

**Symptoms:**
- Colors appear wrong (blue appears red, etc.)
- Inverted colors
- Washed out appearance

**Possible Causes:**
1. **Swapped RGB data lines**
   - Check: Are R1/G1/B1 connected to correct GPIO?
   - Test: Display solid red - is it actually red?

2. **BGR vs RGB order**
   - Check: Does your matrix use BGR instead of RGB?
   - Test: Swap R and B in code

**Solutions:**
```
1. Verify pin connections match code:
   GP0 → R1, GP1 → G1, GP2 → B1
   GP3 → R2, GP4 → G2, GP5 → B2
2. Try swapping color order in code
3. Test with simple color patterns (solid red, green, blue)
```

### WiFi Issues

#### Won't Connect to WiFi

**Symptoms:**
- Display shows "WiFi Lost" or "Connecting..."
- Never gets IP address
- Can't access web interface

**Possible Causes:**
1. **Wrong credentials**
   - Check: SSID and password in secrets.py correct?
   - Check: Is WiFi 2.4GHz? (Pico doesn't support 5GHz)

2. **Out of range**
   - Check: Signal strength (move closer to router)
   - Test: Use phone to check WiFi strength at display location

3. **WiFi disabled**
   - Check: Is router actually on and working?
   - Test: Can other devices connect?

**Solutions:**
```
1. Verify secrets.py has correct SSID/password
2. Ensure WiFi is 2.4GHz (not 5GHz only)
3. Move display closer to router temporarily for testing
4. Check for special characters in password (escape them)
5. Try mobile hotspot to isolate router issues
```

#### WiFi Keeps Disconnecting

**Symptoms:**
- Connects initially, drops later
- Frequent "WiFi Lost" messages
- Intermittent web interface access

**Possible Causes:**
1. **Weak signal**
   - Check: Is display far from router?
   - Test: -70dBm or worse is problematic

2. **Power supply issues**
   - Check: Voltage drooping under load?
   - Test: Does it disconnect when display is bright?

3. **Router issues**
   - Check: Router stability
   - Test: Check router logs for disconnects

**Solutions:**
```
1. Move display closer to router
2. Add WiFi extender/repeater
3. Verify power supply is 5V/4A or higher
4. Add keepalive/ping in code
5. Implement auto-reconnect logic (should be in code already)
```

### API Issues

#### No Scores Showing

**Symptoms:**
- Display works but shows "No games" or idle
- Scores never update
- API errors in logs

**Possible Causes:**
1. **No internet connection**
   - Check: Is WiFi connected?
   - Test: Can you access web interface?

2. **API endpoint changed**
   - Check: ESPN API still working?
   - Test: Try URL in browser

3. **No games actually scheduled**
   - Check: Is it off-season?
   - Check: Are configured teams playing today?

**Solutions:**
```
1. Verify internet connectivity (ping test)
2. Check API endpoints are accessible
3. Verify teams are configured correctly
4. Check if games are actually scheduled
5. Look at serial console for error messages
```

#### Wrong Scores Displayed

**Symptoms:**
- Scores don't match actual game
- Old scores showing
- Wrong teams displayed

**Possible Causes:**
1. **Cache issues**
   - Check: Is cache timeout too long?
   - Test: Restart display, do scores update?

2. **Timezone problems**
   - Check: Is timezone offset correct?
   - Test: Compare display time to actual time

3. **Parser bugs**
   - Check: Serial logs for parsing errors
   - Test: Different sport/game

**Solutions:**
```
1. Clear cache and force refresh
2. Verify timezone offset in config
3. Update to latest code (bug fixes)
4. Check API response format hasn't changed
```

### Web Interface Issues

#### Can't Access Web Interface

**Symptoms:**
- Browser shows "can't connect"
- IP address doesn't respond
- Timeout errors

**Possible Causes:**
1. **Wrong IP address**
   - Check: IP shown on display at startup
   - Test: Ping the IP address

2. **Web server not started**
   - Check: Serial console for errors
   - Test: Restart Pico

3. **Firewall blocking**
   - Check: Computer firewall settings
   - Test: Try from different device

**Solutions:**
```
1. Note correct IP from display at boot
2. Try http://IP (not https)
3. Connect from device on same WiFi network
4. Check serial console for web server errors
5. Restart Pico and try again
```

#### Configuration Changes Don't Save

**Symptoms:**
- Changes made but don't persist
- Settings reset after reboot
- Error when clicking Save

**Possible Causes:**
1. **File system errors**
   - Check: Is storage full?
   - Test: Can Pico write to flash?

2. **JSON corruption**
   - Check: Syntax errors in config.json
   - Test: Upload fresh config.json

**Solutions:**
```
1. Check available storage space
2. Re-upload config.json from backup
3. Factory reset (upload default config)
4. Reflash MicroPython firmware if persistent
```

### Performance Issues

#### Slow Updates / Laggy Display

**Symptoms:**
- Display updates slowly
- Web interface sluggish
- Delayed response to changes

**Possible Causes:**
1. **Memory issues**
   - Check: `gc.mem_free()` in console
   - Test: Does it improve after restart?

2. **CPU overload**
   - Check: Are too many tasks running?
   - Test: Disable some features

**Solutions:**
```
1. Call gc.collect() more frequently
2. Reduce API polling frequency
3. Lower display brightness/complexity
4. Optimize code (remove debug logging)
5. Increase update interval
```

#### Memory Errors / Crashes

**Symptoms:**
- "MemoryError" in console
- Pico resets randomly
- Freezes during operation

**Possible Causes:**
1. **Memory leak**
   - Check: Memory decreases over time
   - Test: Monitor gc.mem_free()

2. **Large data structures**
   - Check: Are API responses too large?
   - Test: Simplify data parsing

**Solutions:**
```
1. Add gc.collect() after API calls
2. Reduce framebuffer size if possible
3. Stream parse JSON instead of loading all
4. Clear old variables after use
5. Monitor memory in development
```

## Hardware Debugging

### Multimeter Tests

**Essential measurements:**

**Power Supply Output:**
```
1. Set multimeter to DC voltage
2. Measure between + and - on power supply
3. Should read: 4.75V - 5.25V
4. If outside range: Replace power supply
```

**Matrix Power Input:**
```
1. Measure at matrix power terminals
2. Should match power supply output
3. If significantly lower: Check wire connections
4. If 0V: Check power supply is ON
```

**Pico VSYS Pin:**
```
1. Measure Pin 39 to GND
2. Should read: 4.75V - 5.25V (same as supply)
3. If 0V: Check power connection
4. If wrong voltage: Stop immediately, check wiring
```

**Continuity Tests:**
```
1. Power OFF for all continuity tests
2. Check ground connections (should beep)
3. Check data lines (Pico GPIO to HUB75 pin)
4. Check for shorts (pins shouldn't connect to neighbors)
```

### Visual Inspection Checklist

**Before every power-on:**
```
□ All connections secure
□ No exposed wire touching other connections
□ Power supply is 5V (check label)
□ Polarity correct (red=+, black=-)
□ No damaged components visible
□ No burning smell
□ Workspace clear of metal objects
```

**After any issues:**
```
□ Check for brown/burned solder
□ Check for swollen capacitors
□ Check for cracked components
□ Check for melted plastic
□ Smell for burning electronics
```

## Emergency Procedures

### If You See Smoke

1. **UNPLUG IMMEDIATELY** - Don't investigate first
2. Move to well-ventilated area
3. Let cool for 15+ minutes
4. Inspect for damage
5. Do NOT power on again until cause identified

### If Components Get Hot

1. **Unplug within 5 seconds**
2. Identify what got hot
3. Check for:
   - Wrong voltage (most common)
   - Shorted wires
   - Reversed polarity
4. Fix issue before re-powering

### If Display Acts Erratically

1. Power off
2. Check all connections
3. Verify power supply voltage
4. Restart from fresh boot
5. If persists, likely hardware damage

## Getting Help

### Information to Collect

When asking for help, provide:
```
□ Exact error message or symptom
□ What you were doing when it happened
□ Power supply specifications (voltage/current)
□ Photos of setup and connections
□ Serial console output
□ What you've already tried
```

### Serial Console Access

**View debug output:**
```bash
# Using mpremote
mpremote connect /dev/ttyACM0 repl

# Using screen (Mac/Linux)
screen /dev/ttyACM0 115200

# Using PuTTY (Windows)
# Select Serial, enter COM port, 115200 baud
```

**Useful debug info:**
```python
import gc
print(f"Free memory: {gc.mem_free()} bytes")
print(f"WiFi connected: {network.WLAN.isconnected()}")
print(f"IP address: {network.WLAN.ifconfig()[0]}")
```

## Preventive Maintenance

### Regular Checks (Monthly)

```
□ Verify display still works correctly
□ Check web interface accessible
□ Verify scores updating properly
□ Check WiFi connection stability
□ Test brightness adjustment
□ Verify no loose connections
```

### Cleaning

```
□ Power off before cleaning
□ Use compressed air for dust
□ Wipe matrix front with microfiber cloth
□ Check for spider webs in back (if mounted)
□ Verify no moisture/condensation
```

### Long-term Storage

If storing display:
```
1. Power off
2. Disconnect all cables
3. Store in anti-static bag if possible
4. Keep in cool, dry place
5. Before reusing: Visual inspection first
```

## Conclusion

Most issues with this project come from:
1. **Wrong voltage** (use 5V ONLY)
2. **Loose connections** (check everything is secure)
3. **WiFi issues** (ensure 2.4GHz, good signal)
4. **Power supply too weak** (use 4A minimum)

**Remember:** When in doubt, check voltage first, connections second, code third.

If you've checked all the above and still have issues, the component may be damaged and need replacement. LED matrices are ~$25-30, Picos are ~$8 - relatively cheap to replace versus troubleshooting damaged hardware for hours.

**The best troubleshooting tool: A working backup component to swap in and test!**
