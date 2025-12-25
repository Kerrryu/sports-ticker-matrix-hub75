# Sports Ticker - System Architecture

## Table of Contents

1. [System Overview](#system-overview)
2. [Hardware Architecture](#hardware-architecture)
3. [Software Architecture](#software-architecture)
4. [Module Design](#module-design)
5. [Data Flow](#data-flow)
6. [State Management](#state-management)
7. [Error Handling Strategy](#error-handling-strategy)
8. [Performance Considerations](#performance-considerations)

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Power Supply                         │
│                         (5V/4A)                             │
└────────────────┬───────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                    LED Matrix Panel                         │
│                      (64x64 RGB)                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              HUB75 Interface                        │   │
│  │  (R1,G1,B1,R2,G2,B2,A,B,C,D,E,CLK,LAT,OE)          │   │
│  └──────────────────┬──────────────────────────────────┘   │
└─────────────────────┼──────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Raspberry Pi Pico 2W                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │   WiFi   │  │  GPIO    │  │  Flash   │                 │
│  │ CYW43439 │  │  Pins    │  │ Storage  │                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
│  ┌────────────────────────────────────────┐               │
│  │        MicroPython Runtime             │               │
│  │  ┌──────────┐ ┌──────────┐ ┌────────┐ │               │
│  │  │ Display  │ │   API    │ │  Web   │ │               │
│  │  │  Driver  │ │  Client  │ │ Server │ │               │
│  │  └──────────┘ └──────────┘ └────────┘ │               │
│  └────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  External Services                          │
│  ┌──────────────┐        ┌──────────────┐                 │
│  │  ESPN API    │        │  User's      │                 │
│  │ (REST/JSON)  │        │  Browser     │                 │
│  └──────────────┘        └──────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

### Design Patterns

1. **Singleton Pattern**: Display driver, config manager
2. **Factory Pattern**: Creating game data objects from API responses
3. **Observer Pattern**: Config changes trigger display updates
4. **Strategy Pattern**: Different display modes (live, idle, error)
5. **Command Pattern**: Web API endpoints as commands

## Hardware Architecture

### Microcontroller Specifications

**Raspberry Pi Pico 2W (RP2350)**:
- **CPU**: Dual ARM Cortex-M33 @ 150MHz (default, overclockable to 250MHz)
- **RAM**: 520KB SRAM (264KB per core)
- **Flash**: 4MB (2MB usable after MicroPython)
- **WiFi**: Infineon CYW43439 (2.4GHz 802.11n)
- **GPIO**: 26 multi-function GPIO pins
- **ADC**: 3 analog inputs (12-bit)
- **Timers**: 8 hardware timers
- **DMA**: 12 channels

### LED Matrix Specifications

**64x64 RGB Panel (HUB75)**:
- **Resolution**: 64 pixels (width) × 64 pixels (height)
- **Total Pixels**: 4,096
- **Color Depth**: 24-bit RGB (16.7M colors)
- **Scan Type**: 1/32 scan (2 rows active at a time)
- **Refresh Rate**: Target 60Hz minimum
- **Power Draw**: 
  - Maximum (all white): ~4A @ 5V = 20W
  - Typical (mixed content): ~1.5-2A = 7.5-10W
- **Interface**: HUB75 parallel (14 signal pins + power)

### Pin Mapping Rationale

GPIO pins selected for optimal performance:

```
GP0-GP5   → RGB data (consecutive for efficient bit manipulation)
GP6-GP10  → Address lines (consecutive, hardware-optimized)
GP11-GP13 → Control signals (CLK, LAT, OE)
```

**Why this mapping?**
- Consecutive pins allow bit-shifting operations for faster updates
- Control pins grouped together for atomic operations
- GPIO11-13 have hardware timer support for precise clock generation

### Power Architecture

```
┌──────────────┐
│ Wall Outlet  │
│   (120V AC)  │
└──────┬───────┘
       │
       ▼
┌──────────────┐      5V/4A      ┌──────────────┐
│  5V Power    │─────────────────▶│ LED Matrix   │
│   Supply     │                  │  Power Input │
└──────┬───────┘                  └──────────────┘
       │
       │ 5V via USB (500mA)
       ▼
┌──────────────┐
│  Pico 2W     │
│  (USB Port)  │
└──────────────┘
```

**Critical**: LED matrix must have dedicated power supply. Do NOT attempt to power from Pico.

**Power Budget**:
- Pico 2W: ~100-150mA (WiFi active)
- LED Matrix: 1.5-4A depending on content
- Total system: ~2-4A @ 5V

## Software Architecture

### Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                    │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐       │
│  │  Main Loop │  │  Display   │  │   Web UI   │       │
│  │   Logic    │  │  Manager   │  │  Handlers  │       │
│  └────────────┘  └────────────┘  └────────────┘       │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────┴─────────────────────────────────┐
│                   Business Logic Layer                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐       │
│  │  API       │  │  Config    │  │  Renderer  │       │
│  │  Client    │  │  Manager   │  │  Engine    │       │
│  └────────────┘  └────────────┘  └────────────┘       │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────┴─────────────────────────────────┐
│                    Hardware Layer                       │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐       │
│  │   HUB75    │  │   WiFi     │  │  Storage   │       │
│  │   Driver   │  │   Driver   │  │   I/O      │       │
│  └────────────┘  └────────────┘  └────────────┘       │
└─────────────────────────────────────────────────────────┘
```

### Module Dependency Graph

```
main.py
  ├─ display/
  │   ├─ hub75.py (no dependencies)
  │   ├─ renderer.py → hub75.py, fonts.py
  │   └─ fonts.py (no dependencies)
  │
  ├─ api/
  │   ├─ espn.py → network.py, cache.py
  │   ├─ parser.py (no dependencies)
  │   └─ cache.py → time_utils.py
  │
  ├─ web/
  │   ├─ server.py → network.py, config.py
  │   ├─ routes.py → config.py, display/
  │   └─ templates.py (no dependencies)
  │
  └─ utils/
      ├─ config.py (no dependencies)
      ├─ network.py (no dependencies)
      ├─ time_utils.py (no dependencies)
      ├─ logger.py (no dependencies)
      └─ watchdog.py → network.py, display/
```

**Design Rule**: Lower layers never import from higher layers (prevents circular dependencies)

## Module Design

### 1. Display Module

#### HUB75 Driver (`display/hub75.py`)

```python
class HUB75:
    """Low-level HUB75 protocol driver."""
    
    def __init__(self, width: int, height: int, pins: dict):
        """
        Initialize HUB75 driver.
        
        Args:
            width: Panel width in pixels
            height: Panel height in pixels
            pins: Dictionary mapping pin names to GPIO numbers
        """
        self.width = width
        self.height = height
        self.pins = pins
        self.framebuffer = bytearray(width * height * 3)
        self._init_gpio()
        self._start_refresh_timer()
    
    def set_pixel(self, x: int, y: int, r: int, g: int, b: int):
        """Set single pixel color (no bounds checking for performance)."""
        offset = (y * self.width + x) * 3
        self.framebuffer[offset] = r
        self.framebuffer[offset + 1] = g
        self.framebuffer[offset + 2] = b
    
    def show(self):
        """Push framebuffer to display (non-blocking)."""
        self._refresh_display()
    
    def clear(self, r=0, g=0, b=0):
        """Clear display to color."""
        for i in range(0, len(self.framebuffer), 3):
            self.framebuffer[i] = r
            self.framebuffer[i+1] = g
            self.framebuffer[i+2] = b
```

**Performance Optimization**:
- Use `bytearray` instead of list for framebuffer (50% memory savings)
- Direct memory access, no bounds checking in hot path
- Hardware timer for consistent refresh rate
- DMA for data transfer (future optimization)

#### Renderer (`display/renderer.py`)

```python
class Renderer:
    """High-level drawing functions."""
    
    def __init__(self, display: HUB75):
        self.display = display
        self.font_5x7 = Font5x7()
        self.font_3x5 = Font3x5()
    
    def draw_text(self, x: int, y: int, text: str, 
                  color: tuple, font: Font):
        """Draw text at position with font."""
        cursor_x = x
        for char in text:
            bitmap = font.get_char(char)
            self._draw_bitmap(cursor_x, y, bitmap, color)
            cursor_x += font.char_width + 1
    
    def draw_game_layout(self, game_data: GameData):
        """Draw complete game display layout."""
        # Header: Team names
        self.draw_text(2, 2, game_data.away_team, 
                      COLOR_WHITE, self.font_5x7)
        self.draw_text(34, 2, game_data.home_team, 
                      COLOR_WHITE, self.font_5x7)
        
        # Center: Scores (large font)
        self.draw_large_number(8, 20, game_data.away_score)
        self.draw_large_number(40, 20, game_data.home_score)
        
        # Footer: Game status
        self.draw_text(8, 55, game_data.status, 
                      COLOR_YELLOW, self.font_3x5)
```

**Display Modes**:

1. **Live Game Mode**:
   ```
   ┌──────────────────────────────┐
   │ DET    @    GB              │
   │                             │
   │  14    -    10              │
   │                             │
   │     Q2  5:42                │
   └──────────────────────────────┘
   ```

2. **Idle Mode** (no active games):
   ```
   ┌──────────────────────────────┐
   │      [DET LOGO]             │
   │   Detroit Lions             │
   │   Next Game: Sun 1:00PM     │
   └──────────────────────────────┘
   ```

3. **Error Mode**:
   ```
   ┌──────────────────────────────┐
   │         [!]                 │
   │   Connection Error          │
   │   Retrying...               │
   └──────────────────────────────┘
   ```

### 2. API Module

#### ESPN Client (`api/espn.py`)

```python
class ESPNClient:
    """ESPN API client with caching."""
    
    BASE_URLS = {
        'nfl': 'https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard',
        'nba': 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard',
        'mlb': 'https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard',
        'nhl': 'https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard'
    }
    
    def __init__(self, cache: Cache):
        self.cache = cache
        self.timeout = 10  # seconds
    
    async def get_games_for_teams(self, teams: list) -> list[GameData]:
        """
        Get current games for specified teams.
        
        Args:
            teams: List of team configs from config.json
            
        Returns:
            List of GameData objects for active/upcoming games
        """
        all_games = []
        
        for team in teams:
            if not team.get('enabled', True):
                continue
                
            # Check cache first
            cache_key = f"{team['sport']}:{team['team_id']}"
            cached = self.cache.get(cache_key)
            if cached:
                all_games.append(cached)
                continue
            
            # Fetch from API
            try:
                game_data = await self._fetch_team_game(
                    team['sport'], 
                    team['team_id']
                )
                if game_data:
                    self.cache.set(cache_key, game_data, ttl=120)
                    all_games.append(game_data)
            except Exception as e:
                logger.log_error(f"API error for {team['team_name']}", e)
        
        return all_games
```

**API Request Flow**:

```
┌────────────┐
│ API Client │
└─────┬──────┘
      │
      ├─ Check Cache ────▶ Cache Hit? ─Yes─▶ Return Data
      │                        │
      │                       No
      │                        ▼
      ├─ Make HTTP Request ───┬────▶ Success ──▶ Parse ──▶ Cache ──▶ Return
      │                        │
      │                        └────▶ Error ────▶ Log ────▶ Return Stale/None
      │
      └─ Implement Backoff ───▶ Retry with increasing delay
```

#### Data Parser (`api/parser.py`)

```python
class GameData:
    """Standardized game data structure."""
    
    def __init__(self):
        self.game_id: str = ""
        self.home_team: str = ""
        self.away_team: str = ""
        self.home_score: int = 0
        self.away_score: int = 0
        self.status: str = ""  # "pregame", "live", "final"
        self.period: str = ""  # "Q1", "3rd", etc.
        self.time_remaining: str = ""
        self.start_time: str = ""  # ISO 8601
        
    @classmethod
    def from_espn(cls, event_data: dict) -> 'GameData':
        """Create GameData from ESPN API response."""
        game = cls()
        
        # Safe navigation with defaults
        competitions = event_data.get('competitions', [{}])[0]
        competitors = competitions.get('competitors', [])
        
        for comp in competitors:
            team_abbr = comp['team']['abbreviation']
            score = int(comp.get('score', 0))
            
            if comp['homeAway'] == 'home':
                game.home_team = team_abbr
                game.home_score = score
            else:
                game.away_team = team_abbr
                game.away_score = score
        
        # Status parsing
        status = event_data.get('status', {})
        game.status = status.get('type', {}).get('state', 'unknown')
        game.period = f"Q{status.get('period', 0)}"
        game.time_remaining = status.get('displayClock', '')
        
        return game
```

### 3. Web Server Module

#### Async Server (`web/server.py`)

```python
class WebServer:
    """Lightweight async HTTP server."""
    
    def __init__(self, config_manager, display_manager):
        self.config = config_manager
        self.display = display_manager
        self.routes = Routes(config_manager, display_manager)
        
    async def start(self, port=80):
        """Start server on specified port."""
        addr = socket.getaddrinfo('0.0.0.0', port)[0][-1]
        server = socket.socket()
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(addr)
        server.listen(1)
        server.setblocking(False)
        
        logger.log_info(f"Web server started on port {port}")
        
        while True:
            try:
                yield  # Allow other tasks to run
                client, addr = server.accept()
                asyncio.create_task(self.handle_client(client))
            except OSError:
                await asyncio.sleep(0.1)
    
    async def handle_client(self, client):
        """Handle single HTTP request."""
        try:
            request = await self.read_request(client)
            response = await self.routes.dispatch(request)
            await self.send_response(client, response)
        finally:
            client.close()
```

**Request Routing**:

```python
class Routes:
    """URL routing and handlers."""
    
    def __init__(self, config_manager, display_manager):
        self.config = config_manager
        self.display = display_manager
        
        self.routes = {
            'GET /': self.serve_index,
            'GET /api/config': self.get_config,
            'POST /api/config': self.update_config,
            'GET /api/status': self.get_status,
            'GET /api/teams': self.get_teams_list,
            'POST /api/restart': self.restart_system,
        }
    
    async def dispatch(self, request):
        """Route request to appropriate handler."""
        method_path = f"{request.method} {request.path}"
        handler = self.routes.get(method_path, self.not_found)
        return await handler(request)
```

### 4. Configuration Module

#### Config Manager (`utils/config.py`)

```python
class ConfigManager:
    """Manage persistent configuration."""
    
    CONFIG_FILE = 'config.json'
    BACKUP_FILE = 'config.json.bak'
    
    def __init__(self):
        self.config = self.load()
        self.observers = []  # Observer pattern for changes
    
    def load(self) -> dict:
        """Load config from file or create default."""
        try:
            with open(self.CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return self.validate(config)
        except (OSError, ValueError):
            logger.log_info("Config not found, creating default")
            return self.get_default()
    
    def save(self):
        """Save config with atomic write."""
        # Write to temp file first
        temp_file = f"{self.CONFIG_FILE}.tmp"
        with open(temp_file, 'w') as f:
            json.dump(self.config, f)
        
        # Backup old config
        try:
            os.rename(self.CONFIG_FILE, self.BACKUP_FILE)
        except OSError:
            pass
        
        # Rename temp to config
        os.rename(temp_file, self.CONFIG_FILE)
        
        # Notify observers
        self.notify_observers()
    
    def add_team(self, sport: str, team_id: str, team_name: str):
        """Add team to favorites."""
        team = {
            'sport': sport,
            'team_id': team_id,
            'team_name': team_name,
            'enabled': True
        }
        self.config['teams'].append(team)
        self.save()
```

## Data Flow

### Startup Sequence

```
1. Power On
    ↓
2. Load MicroPython
    ↓
3. Execute main.py
    ↓
4. Initialize Logging
    ↓
5. Load Configuration ────▶ Create Default if Missing
    ↓
6. Initialize Display ────▶ Show Startup Message
    ↓
7. Connect WiFi ──────────▶ Show IP Address
    │   ↓
    │  Retry on Failure (max 3 attempts)
    ↓
8. Start Web Server ──────▶ Background Task
    ↓
9. Enter Main Loop
```

### Main Loop Flow

```
┌─────────────────────────────────────┐
│         Main Loop (async)           │
└──────────────┬──────────────────────┘
               │
               ├─▶ Check Time ────────┬─▶ Update Interval Passed?
               │                       │       │
               │                       │      Yes
               │                       │       ▼
               │                       └─▶ Poll API ────▶ Parse Data
               │                                │
               │                                ▼
               ├─▶ Update Display ◀────────── Game Data Available?
               │        │                       │
               │        ├─ Live Game ──────────┤
               │        ├─ Idle Mode ──────────┤
               │        └─ Error State ────────┘
               │
               ├─▶ Handle Web Requests (async, non-blocking)
               │
               ├─▶ Feed Watchdog
               │
               ├─▶ Check System Health ──▶ Log Memory/WiFi Status
               │
               └─▶ Sleep (100ms) ────────────▶ Yield to other tasks
                   │
                   └─────────────────────────▶ Loop
```

### Web Request Flow

```
Browser Request
     │
     ▼
┌──────────────┐
│ Web Server   │
│ (Port 80)    │
└──────┬───────┘
       │
       ▼
┌──────────────┐       ┌──────────────┐
│   Router     │──────▶│   Handler    │
│ (dispatch)   │       │  (execute)   │
└──────────────┘       └──────┬───────┘
                              │
                              ├─▶ Read Config
                              ├─▶ Validate Input
                              ├─▶ Modify State
                              ├─▶ Save Config
                              └─▶ Return JSON
                                   │
                                   ▼
                              Browser Response
```

## State Management

### System States

```python
class SystemState(Enum):
    INITIALIZING = "init"
    CONNECTING = "connecting"
    READY = "ready"
    ERROR = "error"
    SLEEPING = "sleeping"
```

### Display States

```python
class DisplayState(Enum):
    IDLE = "idle"           # No active games
    LIVE_GAME = "live"      # Showing live score
    PREGAME = "pregame"     # Upcoming game
    POSTGAME = "postgame"   # Final score
    ERROR = "error"         # Connection/API error
    CONFIG = "config"       # Web config active
```

### State Transitions

```
        ┌─────────────┐
        │    IDLE     │◀────────────┐
        └──────┬──────┘             │
               │                    │
     Game Found│                    │ Game Ends
               ▼                    │
        ┌─────────────┐             │
        │  PREGAME    │             │
        └──────┬──────┘             │
               │                    │
    Game Starts│                    │
               ▼                    │
        ┌─────────────┐             │
        │  LIVE_GAME  │─────────────┘
        └──────┬──────┘
               │
        ┌──────┴──────┐
        │             │
   Game Ends    API Error
        │             │
        ▼             ▼
   ┌─────────┐  ┌─────────┐
   │POSTGAME │  │  ERROR  │
   └────┬────┘  └────┬────┘
        │            │
        └─────┬──────┘
              │
              ▼
         Back to IDLE
```

## Error Handling Strategy

### Error Categories

1. **Hardware Errors**:
   - Display connection failure
   - Power supply issues
   - GPIO malfunction

2. **Network Errors**:
   - WiFi connection lost
   - DNS resolution failure
   - Internet connectivity issues

3. **API Errors**:
   - HTTP timeout
   - Invalid response format
   - Rate limiting
   - Service unavailable

4. **System Errors**:
   - Out of memory
   - File system corruption
   - Configuration errors

### Error Handling Hierarchy

```
┌──────────────────────────────────────┐
│    Critical Error                    │
│  (Display MUST show something)       │
│  → Show error state on display       │
│  → Log to serial                     │
│  → Attempt recovery                  │
└──────────────┬───────────────────────┘
               │
┌──────────────┴───────────────────────┐
│    Recoverable Error                 │
│  (Retry with backoff)                │
│  → Use cached data if available      │
│  → Show warning on display           │
│  → Schedule retry                    │
└──────────────┬───────────────────────┘
               │
┌──────────────┴───────────────────────┐
│    Warning                           │
│  (Log and continue)                  │
│  → Log to serial/file                │
│  → Update status indicator           │
│  → Continue operation                │
└──────────────────────────────────────┘
```

### Retry Strategy

```python
class RetryStrategy:
    """Exponential backoff with jitter."""
    
    def __init__(self, max_retries=5, base_delay=1):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.attempts = 0
    
    def next_delay(self) -> float:
        """Calculate next retry delay."""
        if self.attempts >= self.max_retries:
            return None  # Give up
        
        # Exponential: 1s, 2s, 4s, 8s, 16s
        delay = self.base_delay * (2 ** self.attempts)
        
        # Add jitter (±20%)
        jitter = delay * 0.2 * (random.random() - 0.5)
        
        self.attempts += 1
        return delay + jitter
```

## Performance Considerations

### Memory Optimization

**Framebuffer Management**:
- Single 12KB buffer (64×64×3 bytes)
- No double buffering (insufficient RAM)
- Clear unused buffers after API calls

**String Handling**:
```python
# Bad: Creates multiple string objects
text = "Score: " + str(score) + " - " + str(other_score)

# Good: Single allocation
text = f"Score: {score} - {other_score}"

# Best: Reuse buffer
buffer = bytearray(32)
# Write directly to buffer
```

### CPU Optimization

**Display Refresh**:
- Target: 60Hz refresh (16.67ms per frame)
- Use hardware timer interrupt
- Minimize work in refresh ISR
- Pre-calculate lookup tables

**API Polling**:
- Async/await to prevent blocking
- Batch requests where possible
- Parse incrementally (don't load entire JSON)

### Network Optimization

**Connection Management**:
- Keep-alive for HTTP connections
- DNS caching (save IP addresses)
- Compress responses if supported

**Data Transfer**:
- Request only needed fields
- Use conditional requests (If-Modified-Since)
- Implement client-side filtering

## Conclusion

This architecture provides:

✅ **Modularity**: Independent, testable components
✅ **Reliability**: Error handling and recovery at every level
✅ **Performance**: Optimized for Pico's constraints
✅ **Maintainability**: Clear structure and documentation
✅ **Extensibility**: Easy to add new features

The system is designed to run 24/7 with minimal intervention, providing a reliable sports ticker display for years to come.
