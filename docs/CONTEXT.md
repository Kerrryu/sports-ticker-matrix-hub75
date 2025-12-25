# Sports Ticker - Development Context

## Project Overview

This is a MicroPython-based sports score display system designed for Raspberry Pi Pico 2W and a 64x64 RGB LED matrix (HUB75 interface). The system provides real-time sports scores through a web-configurable interface, automatically polling sports APIs and displaying game information for user-selected favorite teams.

## Target Audience

**End User**: Non-technical sports enthusiast who wants a simple plug-and-play sports ticker
**Developer**: You, building this as a Christmas gift with clean, maintainable code

## Technical Stack

### Hardware
- **MCU**: Raspberry Pi Pico 2W (RP2350 chip, dual ARM Cortex-M33, WiFi via Infineon CYW43439)
- **Display**: 64x64 RGB LED Matrix Panel
  - Interface: HUB75
  - Resolution: 4096 pixels (64x64)
  - Color depth: 24-bit RGB (8-bit per channel)
  - Scan: 1/32 scan rate
  - Power: 5V @ 4A max
- **Power**: External 5V power supply for LED matrix (DO NOT power from Pico)

### Software
- **Language**: MicroPython (latest for Pico 2W)
- **Networking**: Built-in WiFi via CYW43439 driver
- **Web Server**: Custom lightweight HTTP server (asyncio-based)
- **APIs**: ESPN API (public endpoints, no auth required)

## Architecture Philosophy

### Design Principles

1. **Modularity**: Each component (display, API, web, config) is independent and testable
2. **Simplicity**: No over-engineering, straightforward logic flow
3. **Reliability**: Graceful degradation, error handling, watchdog protection
4. **Maintainability**: Clear code structure, comprehensive comments, easy debugging
5. **Resource Conscious**: Memory-efficient for Pico's 264KB RAM constraint

### Why These Choices?

- **MicroPython vs C++**: Faster development, easier debugging, good enough performance for this use case
- **ESPN API**: Free, reliable, no rate limits for reasonable use, good coverage
- **Async Web Server**: Non-blocking allows simultaneous display updates and web serving
- **JSON Config**: Human-readable, easy to edit, standard format
- **Modular Structure**: Each module can be tested independently, easier troubleshooting

## System Architecture

### Component Overview

```
┌─────────────────────────────────────────────┐
│              main.py (Entry Point)          │
│  - Init WiFi, Display, Web Server           │
│  - Main loop coordination                   │
└──────────────┬──────────────────────────────┘
               │
       ┌───────┴───────┐
       ▼               ▼
┌────────────┐   ┌────────────┐
│   Display  │   │  Web Server│
│   Module   │   │   Module   │
└─────┬──────┘   └──────┬─────┘
      │                 │
      │         ┌───────┴────────┐
      │         ▼                ▼
      │    ┌─────────┐    ┌──────────┐
      │    │   API   │    │  Config  │
      │    │ Module  │    │  Module  │
      │    └────┬────┘    └────┬─────┘
      │         │              │
      └─────────┴──────────────┘
                │
         ┌──────┴──────┐
         ▼             ▼
    ┌────────┐   ┌─────────┐
    │ Utils  │   │ Secrets │
    └────────┘   └─────────┘
```

### Data Flow

1. **Startup Sequence**:
   ```
   Power On → Load Config → Connect WiFi → Init Display → Start Web Server → Main Loop
   ```

2. **Main Loop** (runs continuously):
   ```
   Check Time → Poll API (if interval passed) → Parse Data → Update Display → Handle Web Requests → Repeat
   ```

3. **Web Request Flow**:
   ```
   HTTP Request → Route Handler → Read/Write Config → JSON Response → Update Display
   ```

## Module Specifications

### 1. Display Module (`src/display/`)

**Purpose**: Control the HUB75 LED matrix, render graphics and text

**Files**:
- `hub75.py` - Low-level HUB75 protocol driver
- `renderer.py` - High-level drawing functions (text, sprites, animations)
- `fonts.py` - Bitmap font definitions (5x7, 3x5 for scores)

**Key Functions**:
```python
class HUB75Display:
    def __init__(self, width=64, height=64)
    def set_pixel(self, x, y, r, g, b)
    def clear(self)
    def show()  # Push framebuffer to display
    
class Renderer:
    def draw_text(self, x, y, text, color, font)
    def draw_score(self, home_team, away_team, home_score, away_score)
    def draw_logo(self, x, y, team_id)  # Simple sprite rendering
    def draw_game_status(self, quarter, time_remaining)
```

**Technical Details**:
- Framebuffer: 64x64x3 bytes = 12,288 bytes in RAM
- Refresh rate: Target 60Hz (double buffering if needed)
- Color depth: 24-bit RGB, but may use 18-bit (6-bit per channel) to reduce flicker
- Fonts: Pre-defined bitmap fonts, 5x7 for text, larger for scores
- Logo storage: Small 16x16 or 8x8 sprites in flash memory

**Testing Strategy**:
- Unit tests for pixel calculations
- Visual tests for rendering accuracy
- Timing tests for refresh rate stability

### 2. API Module (`src/api/`)

**Purpose**: Fetch live sports data from external APIs

**Files**:
- `espn.py` - ESPN API client
- `parser.py` - Parse API responses into standard format
- `cache.py` - Simple caching to reduce API calls

**Key Functions**:
```python
class ESPNClient:
    def get_games_today(self, sport)  # Returns list of games
    def get_team_schedule(self, sport, team_id)  # Team-specific games
    def get_live_score(self, game_id)  # Detailed game data
    
class GameData:
    # Standardized data structure
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    status: str  # "live", "pregame", "final"
    period: str  # "Q1", "3rd", "7th Inning"
    time_remaining: str
```

**API Endpoints**:
- NFL: `https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard`
- NBA: `https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard`
- MLB: `https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard`
- NHL: `https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard`

**Caching Strategy**:
- Cache game data for 2 minutes (configurable)
- Don't poll during off-hours (2am-8am) to save power/bandwidth
- Exponential backoff on API errors

**Error Handling**:
- Network timeout: 10 seconds max
- API error: Show cached data or "No data" message
- Invalid response: Log error, continue with stale data

### 3. Web Server Module (`src/web/`)

**Purpose**: Provide configuration interface via web browser

**Files**:
- `server.py` - Async HTTP server
- `routes.py` - URL routing and handlers
- `html_templates.py` - Embedded HTML/CSS/JS strings

**Key Endpoints**:
```python
GET  /              # Main config page (HTML)
GET  /api/config    # Get current config (JSON)
POST /api/config    # Update config (JSON)
GET  /api/status    # System status (uptime, IP, memory)
GET  /api/teams     # Available teams list
POST /api/restart   # Soft restart
```

**Web Interface Features**:
- Team selection by sport and team name
- Brightness slider (0-255)
- Update interval selector (1-10 minutes)
- Live preview of current display
- System info (IP, uptime, memory, WiFi signal)

**Security**:
- No authentication (local network only)
- Input validation on all POST requests
- Rate limiting on config changes (max 1 per 5 seconds)

**Technical Details**:
- Single-threaded async server using `asyncio`
- Minimal memory footprint (<5KB for server state)
- Static assets embedded in Python strings
- JSON for all API communication

### 4. Config Module (`src/utils/config.py`)

**Purpose**: Manage persistent configuration storage

**Configuration Schema**:
```json
{
  "version": "1.0.0",
  "teams": [
    {
      "sport": "nfl",
      "team_id": "DET",
      "team_name": "Detroit Lions",
      "enabled": true
    }
  ],
  "display": {
    "brightness": 128,
    "scroll_speed": 50,
    "idle_animation": "logos"
  },
  "polling": {
    "interval_seconds": 120,
    "quiet_hours_enabled": true,
    "quiet_start": "02:00",
    "quiet_end": "08:00"
  },
  "network": {
    "hostname": "sports-ticker",
    "timezone_offset": -5
  }
}
```

**Key Functions**:
```python
def load_config()  # Read from config.json
def save_config(config_dict)  # Write to config.json
def get_default_config()  # Factory defaults
def validate_config(config_dict)  # Schema validation
def migrate_config(old_version, new_version)  # Version upgrades
```

**File Operations**:
- Atomic writes (write to temp file, then rename)
- Backup before overwrite (`config.json.bak`)
- Validation before save
- Auto-create if missing

### 5. Utils Module (`src/utils/`)

**Purpose**: Shared utility functions

**Files**:
- `network.py` - WiFi connection management
- `time_utils.py` - Time zone handling, formatting
- `logger.py` - Simple logging to console/file
- `watchdog.py` - System health monitoring

**Key Functions**:
```python
# Network
def connect_wifi(ssid, password, timeout=30)
def get_ip_address()
def check_internet()  # Ping test

# Time
def get_local_time(offset_hours)
def format_game_time(timestamp)
def is_quiet_hours(current_time, start, end)

# Logging
def log_info(message)
def log_error(message, exception=None)
def log_debug(message)

# Watchdog
def feed_watchdog()  # Reset watchdog timer
def check_system_health()  # Memory, WiFi, display status
```

## Memory Management

### Pico 2W Memory Constraints

- **Total RAM**: 264KB SRAM
- **MicroPython overhead**: ~50-60KB
- **Available for app**: ~200KB

**Memory Budget**:
- Display framebuffer: 12KB (64x64x3)
- Config data: <2KB
- API response buffers: 10KB max
- Web server state: 5KB
- Code and constants: ~40KB
- Remaining for stack/heap: ~130KB

**Memory Optimization Strategies**:
- Use `const()` for constants (stored in flash, not RAM)
- Limit string concatenation (use `bytearray` for building data)
- Stream large JSON responses instead of loading entirely
- Garbage collect after API calls: `gc.collect()`
- Use integer color values (not tuples) where possible

## Testing Strategy

### Unit Tests (Run on PC with CPython)

**Display Tests** (`tests/test_display.py`):
- Pixel addressing correctness
- Color value ranges
- Text rendering alignment
- Font rendering

**API Tests** (`tests/test_api.py`):
- Mock API responses
- Parser edge cases (null values, missing fields)
- Cache expiration logic
- Error handling

**Config Tests** (`tests/test_config.py`):
- JSON validation
- Default value handling
- File I/O errors
- Schema migration

### Integration Tests (Run on actual Pico)

**Hardware Tests**:
- Display output (visual inspection)
- WiFi connectivity
- Web server responsiveness
- Full data flow (API → Parse → Display)

**Stress Tests**:
- Long-running stability (24+ hours)
- Memory leaks (watch `gc.mem_free()`)
- API failures and recovery
- Network reconnection

### Manual Testing Checklist

```
□ Display shows startup message
□ WiFi connects successfully
□ Web interface accessible
□ Team selection works
□ Config saves and persists
□ API polling works
□ Scores display correctly
□ Display updates automatically
□ Error states handled gracefully
□ Brightness control works
□ System runs 24 hours without crash
```

## Development Workflow

### Local Development Setup

1. **Hardware Setup**:
   - Connect Pico 2W via USB
   - Connect LED matrix to power supply
   - Verify pin connections

2. **Software Setup**:
   ```bash
   # Install development tools
   pip install mpremote pytest pytest-mock requests
   
   # Flash MicroPython firmware
   # (Manual: Hold BOOTSEL, copy .uf2 file)
   
   # Upload code
   ./scripts/upload.sh
   ```

3. **Testing Cycle**:
   - Write code on PC
   - Run unit tests: `pytest tests/`
   - Upload to Pico: `mpremote fs cp -r src/ :`
   - Monitor serial: `mpremote repl`
   - Test functionality
   - Iterate

### Debugging Tools

**Serial Console**:
```python
# In code, add print statements
print(f"Score: {home_score}-{away_score}")

# Monitor from PC
mpremote repl
```

**Web-based Debugging**:
- Add `/api/debug` endpoint that returns system state
- Memory usage: `gc.mem_free()`, `gc.mem_alloc()`
- Variable dumps

**LED-based Status Codes**:
- Red flash: Error state
- Green pulse: Normal operation
- Blue flash: Network activity
- Yellow: Initializing

## Common Issues and Solutions

### Issue: Display Flickering

**Cause**: Refresh rate too slow, interrupts during display update
**Solution**: 
- Increase refresh rate in `hub75.py`
- Disable interrupts during critical sections
- Use hardware timers for consistent timing

### Issue: Memory Errors

**Cause**: Fragmentation, memory leaks, large allocations
**Solution**:
- Call `gc.collect()` after API calls
- Pre-allocate buffers
- Check `gc.mem_free()` in main loop
- Reduce framebuffer color depth if needed (18-bit instead of 24-bit)

### Issue: WiFi Disconnects

**Cause**: Weak signal, power supply issues, driver bugs
**Solution**:
- Add auto-reconnect logic
- Increase watchdog timeout
- Add WiFi keepalive (ping every 60 seconds)
- Check power supply is adequate (2A for Pico)

### Issue: API Rate Limiting

**Cause**: Too many requests in short time
**Solution**:
- Increase polling interval
- Implement exponential backoff
- Cache responses more aggressively
- Only poll during active games

### Issue: Incorrect Scores

**Cause**: API format change, parsing errors, timezone issues
**Solution**:
- Add API response logging
- Validate parsed data before display
- Test with multiple sports/games
- Handle timezone conversions carefully

## Code Style Guidelines

### Python Conventions

- Follow PEP 8 where practical
- Use type hints in function signatures (for documentation, not enforced)
- Max line length: 100 characters
- Use descriptive variable names
- Avoid magic numbers (use named constants)

### Example:
```python
# Good
MAX_BRIGHTNESS = 255
DEFAULT_UPDATE_INTERVAL = 120  # seconds

def set_brightness(value: int) -> None:
    """Set display brightness (0-255)."""
    if not 0 <= value <= MAX_BRIGHTNESS:
        raise ValueError(f"Brightness must be 0-{MAX_BRIGHTNESS}")
    display.brightness = value

# Avoid
def sb(v):
    if v < 0 or v > 255:
        raise ValueError("bad value")
    display.b = v
```

### Comments

- Use docstrings for all functions and classes
- Inline comments for complex logic
- TODO comments for future improvements
- Explain WHY, not WHAT (code shows what)

### Error Handling

- Catch specific exceptions, not bare `except:`
- Log errors with context
- Fail gracefully (show error on display if possible)
- Retry with backoff for transient failures

## API Data Examples

### ESPN API Response (Simplified)

```json
{
  "events": [
    {
      "id": "401547397",
      "name": "Detroit Lions at Green Bay Packers",
      "status": {
        "type": {
          "state": "in",
          "description": "In Progress"
        },
        "period": 2,
        "displayClock": "5:42"
      },
      "competitions": [
        {
          "competitors": [
            {
              "team": {
                "abbreviation": "DET",
                "displayName": "Detroit Lions"
              },
              "score": "14",
              "homeAway": "away"
            },
            {
              "team": {
                "abbreviation": "GB",
                "displayName": "Green Bay Packers"
              },
              "score": "10",
              "homeAway": "home"
            }
          ]
        }
      ]
    }
  ]
}
```

## Deployment Checklist

### Pre-Deployment

```
□ All tests passing
□ Code reviewed and clean
□ Documentation complete
□ secrets.py template provided (without real credentials)
□ Default config.json included
□ Pin diagram verified
□ Power supply warnings added
```

### Deployment Steps

1. Flash MicroPython firmware
2. Upload all project files
3. Create and upload `secrets.py`
4. Power cycle and verify startup
5. Access web interface and configure teams
6. Verify scores display correctly
7. Let run for 24 hours as burn-in test

### Gift Delivery

- Include printed pin diagram
- Include WiFi setup instructions
- Include quick start guide (1 page)
- Include URL to web interface
- Consider pre-configuring his favorite teams

## Future Enhancement Ideas

**Phase 2** (Post-gift):
- Weather display during idle time
- Multiple games rotating display
- Mobile app for remote config
- Push notifications for game start/end
- Historical scores and stats

**Phase 3** (If he loves it):
- Larger display (128x64 or 128x128)
- Sound alerts for big plays (buzzer via GPIO)
- Social media integration (#hashtags for his teams)
- OTA firmware updates
- Cloud sync for settings

## Resources and References

### MicroPython Documentation
- [MicroPython docs](https://docs.micropython.org/en/latest/)
- [Pico 2W specific](https://docs.micropython.org/en/latest/rp2/quickref.html)

### HUB75 Resources
- [HUB75 Protocol Overview](https://learn.adafruit.com/32x16-32x32-rgb-led-matrix/how-the-matrix-works)
- [RGB Matrix Library References](https://github.com/hzeller/rpi-rgb-led-matrix)

### Sports APIs
- [ESPN Hidden APIs](https://gist.github.com/nntrn/ee26cb2a0716de0947a0a4e9a157bc1c)
- [The Sports DB](https://www.thesportsdb.com/api.php) (backup)

### Tools
- [Thonny IDE](https://thonny.org/) - Beginner-friendly MicroPython IDE
- [mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html) - Command-line tool
- [ampy](https://github.com/scientifichackers/ampy) - Alternative file manager

## Project Timeline Estimate

- **Hardware assembly**: 1-2 hours
- **Core display driver**: 4-6 hours
- **API integration**: 3-4 hours
- **Web server**: 3-4 hours
- **Integration and testing**: 4-6 hours
- **Documentation and polish**: 2-3 hours
- **Total**: 17-25 hours

**Recommended approach**: Build and test each module independently before integration.

## Success Metrics

The project is successful when:

1. ✅ Display shows clear, readable scores
2. ✅ Web interface is intuitive and reliable
3. ✅ System runs 24/7 without crashes
4. ✅ Scores update automatically and accurately
5. ✅ Your father-in-law loves it and uses it daily!

## Notes for AI Assistants

When working on this project:

1. **Prioritize simplicity** - Don't over-engineer, this is a gift not enterprise software
2. **Test frequently** - Hardware bugs are expensive, catch them early
3. **Handle errors gracefully** - Display should show something useful even when APIs fail
4. **Comment thoroughly** - Father-in-law might want to tinker, make it approachable
5. **Consider power usage** - This will run 24/7, be energy conscious
6. **Think about the user** - Non-technical sports fan, make it intuitive

This is a heartfelt gift project. Quality and reliability matter more than fancy features. Keep it simple, make it work, and make it last.
