# Sports Ticker - Design Specification

## Table of Contents

1. [Design Philosophy](#design-philosophy)
2. [Display Layouts](#display-layouts)
3. [Color Schemes](#color-schemes)
4. [Typography](#typography)
5. [Animations](#animations)
6. [Web Interface Design](#web-interface-design)
7. [User Experience](#user-experience)
8. [Accessibility](#accessibility)

## Design Philosophy

### Core Principles

1. **Clarity Above All**: Information must be readable from across a room
2. **Simplicity**: No clutter, focus on essential information
3. **Sports Authenticity**: Use recognizable sports presentation conventions
4. **Visual Hierarchy**: Most important info (scores) should dominate
5. **Error Tolerance**: System should always show something useful

### Design Constraints

**Hardware Limitations**:
- **Resolution**: 64×64 pixels (very small!)
- **Viewing Distance**: 3-10 feet typical
- **Pixel Pitch**: 3mm (relatively coarse)
- **Color Depth**: 24-bit RGB (good!)

**Readability Requirements**:
- Minimum font size: 3 pixels tall (absolute minimum)
- Recommended minimum: 5 pixels tall
- Score numbers: 7-9 pixels tall minimum
- High contrast required (no subtle colors)

## Display Layouts

### 1. Live Game Display

**Primary Layout** (Most Common State):

```
┌────────────────────────────────────────────────────┐
│  Row 0-7:   Team Names & Logos                    │
│  DET ██  @  GB ██                                 │
│                                                    │
│  Row 15-35: Large Scores (Center Focus)           │
│      24        17                                 │
│                                                    │
│  Row 40-48: Quarter/Period & Time                 │
│     Q2  3:47  2nd & 6                             │
│                                                    │
│  Row 55-63: Status Bar (Score Trend)              │
│  [▲DET] Last Score: 2:15 ago                      │
└────────────────────────────────────────────────────┘
```

**Detailed Specifications**:

```
Layout Zones (pixel rows):
┌─────────────────────┐
│ 0-10:  Header       │ Team abbreviations + small logos
├─────────────────────┤
│ 12-38: Scores       │ Large numbers (primary focus)
├─────────────────────┤
│ 40-50: Game Info    │ Quarter, time, down & distance
├─────────────────────┤
│ 52-63: Footer       │ Last score, trends, animations
└─────────────────────┘
```

**Element Sizing**:
- Team abbreviations: 5×7 font (3 chars = 17px wide)
- Small logos: 8×8 pixels
- Score numbers: Use custom 9×13 font
- Game status: 3×5 font
- Footer info: 3×5 font

**Color Coding**:
- Away team (top/left): White text, team primary color accent
- Home team (bottom/right): White text, team primary color accent
- Current possession: Yellow highlight
- Winning score: Brighter intensity
- Losing score: Dimmer (70% brightness)

### 2. Pre-Game Display

```
┌────────────────────────────────────────────────────┐
│                                                    │
│         UPCOMING GAME                              │
│                                                    │
│      DET  @  GB                                    │
│                                                    │
│     SUN 1:00 PM                                    │
│                                                    │
│  [Detroit Lions Logo]                              │
│                                                    │
└────────────────────────────────────────────────────┘
```

**Specifications**:
- Centered layout
- Game time prominently displayed
- Alternating logo display (4 sec each team)
- Countdown if game < 1 hour away

### 3. Post-Game Display

```
┌────────────────────────────────────────────────────┐
│                                                    │
│        FINAL SCORE                                 │
│                                                    │
│    DET 28  -  GB 24                                │
│                                                    │
│    ★ DET WINS ★                                    │
│                                                    │
│  Next Game: Thu 8:15 PM                            │
│                                                    │
└────────────────────────────────────────────────────┘
```

**Display Duration**: 
- Show for 5 minutes after game ends
- Then transition to idle or next game

### 4. Idle Mode (No Active Games)

**Option A: Team Logo Rotation**

```
┌────────────────────────────────────────────────────┐
│                                                    │
│                                                    │
│         ████████████                               │
│         ██      ██                                 │
│         ██ DET ██  [Large centered logo]           │
│         ██      ██                                 │
│         ████████████                               │
│                                                    │
│      Detroit Lions                                 │
│   Next: Sun 1:00 PM                                │
│                                                    │
└────────────────────────────────────────────────────┘
```

**Rotation Pattern**:
- 8 seconds per team
- Smooth fade transition (1 sec)
- Show next game time if available

**Option B: Clock + Team Banner**

```
┌────────────────────────────────────────────────────┐
│                                                    │
│         12:34 PM                                   │
│         SAT DEC 21                                 │
│                                                    │
│    ───────────────────                             │
│                                                    │
│    GO LIONS!   [Animated]                          │
│                                                    │
│    Next Game: Tomorrow                             │
│         1:00 PM vs GB                              │
│                                                    │
└────────────────────────────────────────────────────┘
```

### 5. Multi-Game Display

When multiple favorite teams are playing simultaneously:

```
┌────────────────────────────────────────────────────┐
│  DET 14  GB 10  │  MIA 7  BUF 21                  │
│     Q2  5:42    │    Q3  8:15                     │
│ ────────────────┼─────────────────                │
│  (Rotates every 8 seconds)                         │
│                                                    │
│  Or split screen if only 2 games                   │
└────────────────────────────────────────────────────┘
```

**Multi-Game Strategy**:
- Maximum 2 games visible at once
- Split screen (32px each half) if 2 games
- Rotation if 3+ games
- Prioritize closest/most exciting games

### 6. Error Display

```
┌────────────────────────────────────────────────────┐
│                                                    │
│            ⚠️                                       │
│                                                    │
│      CONNECTION                                    │
│         ERROR                                      │
│                                                    │
│      Retrying...                                   │
│                                                    │
│  [Animated spinner or dots]                        │
│                                                    │
└────────────────────────────────────────────────────┘
```

**Error Types**:
- WiFi disconnected: "No Network"
- API timeout: "Connection Error"
- Invalid data: "Data Error"
- System error: "System Error"

All errors show retry countdown and status

## Color Schemes

### Primary Palette

```
Color Name      RGB Value       Hex       Usage
─────────────────────────────────────────────────────
White           (255,255,255)   #FFFFFF   Primary text
Light Gray      (200,200,200)   #C8C8C8   Secondary text
Medium Gray     (128,128,128)   #808080   Dividers
Dark Gray       (64,64,64)      #404040   Backgrounds

Bright Red      (255,0,0)       #FF0000   Errors, important
Bright Green    (0,255,0)       #00FF00   Success, winning
Bright Blue     (0,0,255)       #0000FF   Info, links
Bright Yellow   (255,255,0)     #FFFF00   Warnings, highlights

Orange          (255,165,0)     #FFA500   Live indicators
Purple          (128,0,128)     #800080   Special events
Cyan            (0,255,255)     #00FFFF   Accents
```

### Sport-Specific Colors

**NFL**: 
- Field Green: (0, 180, 0)
- End Zone: Team colors
- Scoreboard: White on black

**NBA**:
- Court Tan: (255, 220, 177)
- Lines: White
- Scoreboard: Orange accents

**MLB**:
- Grass Green: (0, 155, 0)
- Dirt Brown: (139, 90, 43)
- Scoreboard: Traditional white/yellow

**NHL**:
- Ice White: (240, 248, 255)
- Blue Lines: (0, 100, 200)
- Scoreboard: Red for goals

### Team Color Database

```python
TEAM_COLORS = {
    'DET': {'primary': (0, 118, 182), 'secondary': (176, 183, 188)},
    'GB':  {'primary': (24, 48, 40), 'secondary': (255, 184, 28)},
    'CHI': {'primary': (11, 22, 42), 'secondary': (200, 56, 3)},
    # ... Complete database for all teams
}
```

**Usage**:
- Use team primary color for logos/accents
- Use secondary for highlights
- Always ensure 4.5:1 contrast ratio minimum

### Brightness Levels

```
Level       Value   Use Case
─────────────────────────────────────────
Maximum     255     Bright room, daytime
High        192     Normal indoor
Medium      128     Default, evening
Low         64      Night mode
Minimum     32      Sleep mode
```

**Adaptive Brightness** (Future):
- Consider time-of-day adjustment
- Ambient light sensor integration
- Gradual transitions (no flashing)

## Typography

### Font Specifications

**Font 5×7** (Primary Text):
```
Character size: 5px wide × 7px tall
Use cases: Team names, status text
Sample: "DET" = 17px (3 chars + 2 spaces)

█████  ███  █████
█   █  █    █
█   █  ███  █
█   █  █    █
█████  ███  █
```

**Font 3×5** (Small Text):
```
Character size: 3px wide × 5px tall
Use cases: Time, small labels
Sample: "Q2" = 7px

███  ████
█  █    █
█  █   █
█  █  █
███   ████
```

**Font 9×13** (Large Numbers):
```
Character size: 9px wide × 13px tall
Use cases: Scores only
Sample: "24" = 19px

████████    █    █
      █    ███  ███
      █   █   █   █
      █       █   █
████████  █████████
█            █
█            █
█            █
████████     █
```

### Text Rendering Rules

1. **Spacing**:
   - Letter spacing: 1 pixel between characters
   - Word spacing: 3 pixels between words
   - Line height: font height + 2 pixels

2. **Alignment**:
   - Scores: Center aligned
   - Team names: Left/right aligned from edges
   - Status: Center aligned
   - Time: Right aligned

3. **Anti-aliasing**:
   - None (pixels too large for sub-pixel rendering)
   - Use bold rendering for better visibility

### Readability Testing

**Minimum Requirements**:
- 5×7 font readable from 6 feet
- 9×13 font readable from 12 feet
- High contrast (white on dark) required
- No serif fonts (sans-serif only)

## Animations

### Scroll Animations

**Horizontal Scroll** (for long text):
```
Frame 1: "Detroit Lions vs..."
Frame 2: "etroit Lions vs ..."
Frame 3: "troit Lions vs ..."
...
Speed: 2 pixels per 100ms
Pause: 2 seconds at start/end
```

**Vertical Scroll** (for multiple items):
```
Row transitions up
Smooth 1px per frame
Speed: 50ms per pixel
```

### Fade Transitions

**Cross-fade** (between game displays):
```python
for alpha in range(0, 256, 16):  # 16 steps
    # Blend old_frame and new_frame
    display = (old_frame * (255-alpha) + new_frame * alpha) / 255
    show(display)
    sleep(30)  # 30ms per step = ~500ms total
```

### Pulsing Effects

**Score Change Indicator**:
```
When score changes:
- Flash bright (3 flashes)
- Pulse yellow highlight (2 seconds)
- Return to normal
```

**Live Indicator**:
```
"LIVE" badge pulses:
Brightness: 255 → 128 → 255
Period: 2 seconds
Continuous during live games
```

### Loading Animations

**Spinner** (API fetching):
```
Frame 1: ◜
Frame 2: ◝
Frame 3: ◞
Frame 4: ◟
8 frames total, 100ms each
```

**Progress Bar** (startup):
```
[=========>        ] 50%
Width: 40 pixels
Height: 3 pixels
Updates every 100ms
```

## Web Interface Design

### Desktop Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Sports Ticker Configuration                       v1.0.0   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  System Status                                               │
│  ├─ Online      IP: 192.168.1.42                            │
│  ├─ Uptime: 2d 5h 23m                                       │
│  └─ Memory: 145KB free                                       │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Favorite Teams                         [+ Add Team]    │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │ 🏈 NFL  │ Detroit Lions    │ [✓ Enabled] │ [Remove]   │ │
│  │ 🏀 NBA  │ Detroit Pistons  │ [✓ Enabled] │ [Remove]   │ │
│  │ ⚾ MLB  │ Detroit Tigers   │ [✓ Enabled] │ [Remove]   │ │
│  │ 🏒 NHL  │ Detroit Red Wings│ [✓ Enabled] │ [Remove]   │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  Display Settings                                            │
│  ├─ Brightness:  [═══════░░░] 70%                           │
│  ├─ Update Interval: [120] seconds                          │
│  └─ Quiet Hours: 2:00 AM - 8:00 AM [✓]                     │
│                                                              │
│  [Save Changes]  [Restart Device]  [Reset to Default]       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Mobile Layout

```
┌──────────────────────┐
│ Sports Ticker ☰      │
├──────────────────────┤
│                      │
│ Status: Online ●     │
│ IP: 192.168.1.42     │
│                      │
│ ─── TEAMS ───        │
│                      │
│ [NFL] Detroit Lions  │
│ ✓ [Remove]           │
│                      │
│ [NBA] Det. Pistons   │
│ ✓ [Remove]           │
│                      │
│ [+ Add Team]         │
│                      │
│ ─── SETTINGS ───     │
│                      │
│ Brightness           │
│ [════════░] 70%      │
│                      │
│ Update: 120 sec      │
│                      │
│ [Save]  [Restart]    │
│                      │
└──────────────────────┘
```

### Team Selection Modal

```
┌────────────────────────────────────────┐
│  Add Favorite Team              [✕]   │
├────────────────────────────────────────┤
│                                        │
│  Sport: [NFL ▼]                        │
│                                        │
│  Search teams:                         │
│  [detroit_______________] 🔍           │
│                                        │
│  Results:                              │
│  ┌──────────────────────────────────┐ │
│  │ ● Detroit Lions                  │ │
│  │   NFC North                      │ │
│  └──────────────────────────────────┘ │
│                                        │
│         [Cancel]  [Add Team]           │
│                                        │
└────────────────────────────────────────┘
```

## User Experience

### First-Time Setup

**Setup Wizard Flow**:

1. **Welcome Screen** (on display):
   ```
   Welcome!
   Connect to WiFi:
   SportsTicker-Setup
   Password: setup123
   ```

2. **WiFi Configuration** (web):
   - List available networks
   - Password entry
   - Connection test

3. **Team Selection** (web):
   - "Add your first team!"
   - Sport selection
   - Team search
   - Confirmation

4. **Completion** (display):
   ```
   Setup Complete!
   Checking for games...
   ```

### Normal Operation Flow

**User Journey**:

```
1. Power On
   └─> Display shows startup animation
   
2. Connect to WiFi
   └─> Shows IP address (5 seconds)
   
3. Check for games
   ├─> Games found: Show live scores
   └─> No games: Show idle screen
   
4. Configuration Changes (optional)
   ├─> Open web interface
   ├─> Modify settings
   ├─> Save
   └─> Display updates automatically
   
5. Continuous Operation
   └─> Auto-update every 2 minutes
```

### Error Recovery UX

**WiFi Disconnection**:
```
Display: "WiFi Lost - Reconnecting..."
Action: Auto-retry every 10 seconds
Recovery: Resume normal operation
Notification: None (silent recovery)
```

**API Failure**:
```
Display: "Connection Error - Retrying..."
Action: Show cached data if available
Recovery: Exponential backoff retry
Notification: Status on web interface
```

**Power Loss**:
```
Restart: Automatic on power restore
Resume: Last configuration preserved
Display: Startup sequence
Time: ~30 seconds to full operation
```

## Accessibility

### Visual Accessibility

**High Contrast Mode**:
- Black backgrounds
- Bright white text
- 7:1 contrast ratio
- No subtle colors

**Color Blind Considerations**:
- Don't rely solely on color
- Use icons + color
- Patterns for differentiation
- Red/green alternatives available

**Low Vision Support**:
- Minimum 5px font height
- Bold text rendering
- Clear visual hierarchy
- High brightness option

### Configuration Accessibility

**Web Interface**:
- Keyboard navigation
- Screen reader compatible
- Large touch targets (44×44px min)
- Clear labels and descriptions
- Error messages in plain language

**Physical Access**:
- No required physical interaction with display
- All config via web interface
- Alternative: mobile app (future)

## Design Validation

### Testing Checklist

**Readability Tests**:
```
□ Readable from 3 feet
□ Readable from 6 feet  
□ Readable from 10 feet
□ Readable in bright room
□ Readable in dim room
□ No glare/reflection issues
```

**Usability Tests**:
```
□ First-time setup < 5 minutes
□ Team addition < 30 seconds
□ Settings change < 1 minute
□ Web interface intuitive
□ Mobile-friendly
□ No confusion about status
```

**Visual Quality**:
```
□ No flickering
□ Smooth animations
□ Colors accurate
□ Text crisp
□ Logos recognizable
□ Layout balanced
```

## Future Design Enhancements

### Phase 2

- **Weather Integration**: Small weather icon in corner
- **Social Media**: Live tweet/hashtag scroll
- **Custom Alerts**: User-defined score thresholds
- **Multiple Displays**: Synchronized multi-panel setup

### Phase 3

- **Voice Control**: "Show Lions score"
- **Gesture Control**: Wave to change display
- **Ambient Mode**: Background glow based on game intensity
- **AR Companion**: Phone app with 3D visualizations

## Conclusion

This design specification ensures:

✅ **Legibility**: Clear, readable from intended viewing distance
✅ **Consistency**: Unified visual language throughout
✅ **Simplicity**: Easy to understand at a glance
✅ **Flexibility**: Adaptable to different sports and scenarios
✅ **Polish**: Professional appearance worthy of a gift

The design prioritizes function over form, with every visual element serving a clear purpose in delivering sports information quickly and effectively.
