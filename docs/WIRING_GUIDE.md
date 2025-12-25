# Sports Ticker - Power and Wiring Guide

## Power Supply Configuration

### Single 5V/4A Supply (Recommended)

Your 5V/4A power supply can safely power both the LED matrix and Pico 2W.

```
┌────────────────────────────────────────────────────┐
│           5V/4A Power Supply                       │
│         (Barrel jack or screw terminals)           │
└─────────────────┬──────────────────────────────────┘
                  │
          ┌───────┴────────┐
          │                │
          ▼                ▼
    ┌──────────┐     ┌──────────┐
    │   LED    │     │  Power   │
    │  Matrix  │     │  Split   │
    │  (4096   │     │  to Pico │
    │   LEDs)  │     │   2W     │
    └──────────┘     └──────────┘
```

## Detailed Wiring Diagram

### Power Distribution

```
Power Supply Output:
   +5V ──┬─(Red Wire)───> LED Matrix V+ terminal
         │
         └─(Red Wire)───> Pico 2W VSYS (Pin 39)
         
   GND ──┬─(Black Wire)─> LED Matrix GND terminal
         │
         ├─(Black Wire)─> Pico 2W GND (Pin 38)
         │
         └─────────────> HUB75 GND pin (common ground)
```

### Complete Pin Connections

#### Pico 2W Pinout

```
                    Pico 2W
         ╔════════════════════════╗
    GP0  ║ 1                40 ║  VBUS (Don't use)
    GP1  ║ 2                39 ║  VSYS ← 5V IN
    GND  ║ 3                38 ║  GND  ← Ground
    GP2  ║ 4                37 ║  3V3_EN
    GP3  ║ 5                36 ║  3V3(OUT)
    GP4  ║ 6                35 ║  
    GP5  ║ 7                34 ║  GP28
    GND  ║ 8                33 ║  GND
    GP6  ║ 9                32 ║  GP27
    GP7  ║10                31 ║  GP26
    GP8  ║11                30 ║  RUN
    GP9  ║12                29 ║  GP22
    GND  ║13                28 ║  GND
    GP10 ║14                27 ║  GP21
    GP11 ║15                26 ║  GP20
    GP12 ║16                25 ║  GP19
    GP13 ║17                24 ║  GP18
    GND  ║18                23 ║  GND
    GP14 ║19                22 ║  GP17
    GP15 ║20                21 ║  GP16
         ╚════════════════════════╝
```

#### HUB75 Connector Pinout

```
HUB75 Female Connector (on LED Matrix):
┌─────────────────────────────────┐
│ R1  G1  B1  GND  R2  G2  B2  E  │  Top Row
│ A   B   C   D   CLK LAT OE  GND │  Bottom Row
└─────────────────────────────────┘
```

#### Complete Connection Table

| HUB75 Pin | Pico GPIO | Wire Color (Suggested) | Function |
|-----------|-----------|------------------------|----------|
| R1 | GP0 | Red | Red Upper Half |
| G1 | GP1 | Green | Green Upper Half |
| B1 | GP2 | Blue | Blue Upper Half |
| R2 | GP3 | Orange | Red Lower Half |
| G2 | GP4 | Light Green | Green Lower Half |
| B2 | GP5 | Light Blue | Blue Lower Half |
| A | GP6 | Yellow | Row Select A |
| B | GP7 | Brown | Row Select B |
| C | GP8 | Purple | Row Select C |
| D | GP9 | Gray | Row Select D |
| E | GP10 | Pink | Row Select E |
| CLK | GP11 | White | Clock |
| LAT | GP12 | Black/White | Latch |
| OE | GP13 | White/Black | Output Enable |
| GND | GND (Pin 3) | Black | Common Ground |

**Note**: GND from HUB75 should connect to Pico GND (shared with power supply ground)

### Physical Wiring Steps

#### Step 1: Prepare Power Distribution

**Option A - Screw Terminal Block** (Easiest, most reliable):

```
Materials:
- 2-way screw terminal block (5.08mm pitch)
- 18-22 AWG wire (red for +5V, black for GND)

Connections:
┌──────────────────┐
│ Terminal Block   │
│  + │ + │ - │ -   │
└──┼─┼─┼─┼─────────┘
   │ │ │ │
   │ │ │ └─> Pico GND
   │ │ └───> LED Matrix GND
   │ └─────> Pico VSYS
   └───────> LED Matrix V+
```

**Option B - Soldered Y-Cable** (More permanent):

```
Power Supply
     │
     ├─> Solder split to LED Matrix
     └─> Solder split to Pico VSYS
     
Same for ground
```

#### Step 2: Connect Power

1. **LED Matrix Power Terminals**:
   - Locate power screw terminals on the back of LED matrix
   - Red wire to V+ or +5V terminal
   - Black wire to GND or - terminal
   - Tighten securely

2. **Pico 2W Power**:
   - Red wire to VSYS (Pin 39)
   - Black wire to GND (Pin 38 or Pin 3)
   - Can use header pins or solder directly

#### Step 3: Connect Data Lines

You'll need 15 jumper wires (14 data + 1 ground):

1. **Start with Row Select Lines** (easiest to identify):
   - GP6 → A (HUB75)
   - GP7 → B (HUB75)
   - GP8 → C (HUB75)
   - GP9 → D (HUB75)
   - GP10 → E (HUB75)

2. **Connect RGB Data Lines**:
   - GP0 → R1
   - GP1 → G1
   - GP2 → B1
   - GP3 → R2
   - GP4 → G2
   - GP5 → B2

3. **Connect Control Signals**:
   - GP11 → CLK (Clock)
   - GP12 → LAT (Latch)
   - GP13 → OE (Output Enable)

4. **Connect Ground**:
   - Pico GND (Pin 3, 8, 13, 18, 23, 28, 33, or 38) → HUB75 GND

### Wiring Best Practices

#### Wire Management

1. **Keep wires short** - Reduces noise and improves signal integrity
2. **Use ribbon cable** - 16-wire ribbon cable works perfectly for HUB75
3. **Label both ends** - Use tape or heat shrink with labels
4. **Strain relief** - Secure wires so they don't pull on connections

#### Signal Integrity

1. **Twist pairs for long runs**:
   - Twist CLK with GND
   - Twist LAT with GND
   - Helps reduce interference

2. **Common ground is critical**:
   - Pico GND, Matrix GND, and Power Supply GND must all connect
   - Use star grounding (all grounds to one point)

3. **Separate power from data if possible**:
   - Keep high-current power wires away from signal wires
   - Reduces electromagnetic interference

### Testing Procedure

#### Power-On Sequence

1. **Before Connecting Anything**:
   - Verify power supply voltage with multimeter (should be 5.0V ±0.25V)
   - Check polarity (red = +, black = -)

2. **Connect Power to Matrix First**:
   - Connect only LED matrix to power
   - Power on
   - Some LEDs may light up (this is normal)
   - Verify no smoke, strange smells, or excessive heat
   - Power off

3. **Add Pico Power**:
   - Connect Pico to same power supply
   - Power on
   - Pico LED should light up
   - Power off

4. **Connect Data Lines**:
   - With power OFF, connect all 15 HUB75 wires
   - Double-check every connection
   - Verify no shorts with multimeter (continuity test)

5. **First Boot**:
   - Power on everything
   - Pico should boot (LED flashes)
   - LED matrix should initialize within 30 seconds
   - You should see startup message

### Safety Notes

⚠️ **Important Safety Warnings**:

1. **Never connect 5V to 3V3 pins** - This will damage the Pico!
2. **Always use VSYS (Pin 39)** for external 5V power, never 3V3 pins
3. **4A can generate heat** - Ensure good ventilation
4. **Power supply quality matters** - Cheap supplies can damage electronics
5. **Unplug before wiring** - Always disconnect power when changing connections

### Troubleshooting Power Issues

#### No Display

**Check**:
- Power supply voltage (should be 5.0V)
- All ground connections (common ground is essential)
- Pico is powered (LED on board should light)
- Matrix power connections tight

#### Dim or Flickering Display

**Possible Causes**:
- Insufficient current from power supply
- Loose power connections
- Voltage drop in wires (use thicker gauge)
- Bad power supply

**Solutions**:
- Upgrade to 5V/5A supply
- Use shorter, thicker wires
- Add bulk capacitor (1000µF/10V) near matrix power input

#### Pico Keeps Resetting

**Possible Causes**:
- Power supply overload
- Ground loop issues
- Insufficient capacitance

**Solutions**:
- Lower display brightness
- Add 100µF capacitor between VSYS and GND on Pico
- Check all ground connections

#### Strange Colors or Patterns

**Usually NOT a power issue** - Check data line connections

### Recommended Shopping List for Wiring

```
Essential:
□ 5V/4A power supply (you have this)
□ Male-to-Female jumper wires (20-pack)
□ HUB75 cable (16-pin ribbon cable with connector)
  OR
□ Female DuPont connectors + crimp tool
□ Heat shrink tubing (assorted sizes)
□ Wire labels or tape

Highly Recommended:
□ 2-way screw terminal blocks (for power split)
□ 18AWG wire (red and black, 2 feet each)
□ Small breadboard (for testing)
□ Multimeter (for voltage/continuity testing)

Optional but Nice:
□ 1000µF/10V electrolytic capacitor (for matrix)
□ 100µF/10V capacitor (for Pico)
□ Cable ties or velcro straps
□ Small project enclosure
□ Standoffs for mounting Pico
```

### Final Assembly Tips

1. **Test incrementally** - Don't connect everything at once
2. **Take photos** - Document your wiring for future reference
3. **Label everything** - You'll thank yourself later
4. **Secure loose wires** - Use cable ties or hot glue
5. **Plan for access** - Make it easy to reprogram Pico later

## Questions to Answer Before Starting

1. **Do you have jumper wires?** (You'll need ~20 male-to-female)
2. **Does your power supply have bare wires or a connector?**
3. **Do you have a soldering iron?** (Helpful but not required)
4. **Do you have a multimeter?** (Highly recommended for testing)

Let me know and I can provide more specific guidance!
