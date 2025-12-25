# Sports Ticker - Testing Documentation

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Testing Levels](#testing-levels)
3. [Unit Testing](#unit-testing)
4. [Integration Testing](#integration-testing)
5. [System Testing](#system-testing)
6. [Performance Testing](#performance-testing)
7. [User Acceptance Testing](#user-acceptance-testing)
8. [Continuous Testing](#continuous-testing)

## Testing Philosophy

### Core Principles

1. **Test Early, Test Often**: Catch issues during development, not deployment
2. **Automated Where Possible**: Unit tests run on every change
3. **Real Hardware Matters**: Some bugs only appear on actual Pico
4. **User-Centric**: Test what users will actually experience
5. **Document Failures**: Every bug teaches us something

### Testing Goals

- **Reliability**: System runs 24/7 without crashes
- **Accuracy**: Scores displayed correctly
- **Responsiveness**: Updates happen on time
- **Usability**: Configuration is intuitive
- **Recoverability**: Graceful handling of errors

### Test Coverage Targets

```
Module              Target Coverage
────────────────────────────────────
Display Driver      80%+
API Client          75%+
Configuration       90%+
Web Server          70%+
Utilities           85%+
────────────────────────────────────
Overall             80%+
```

## Testing Levels

### Testing Pyramid

```
                    ┌────────────┐
                    │   Manual   │  ← Exploratory, User Acceptance
                    │  Testing   │
                    └────────────┘
                  ┌────────────────┐
                  │   System Tests │  ← End-to-end on hardware
                  │  (Integration) │
                  └────────────────┘
              ┌────────────────────────┐
              │   Integration Tests    │  ← Module interactions
              │  (Mocked hardware)     │
              └────────────────────────┘
          ┌──────────────────────────────┐
          │       Unit Tests             │  ← Individual functions
          │  (Run on development PC)     │
          └──────────────────────────────┘
```

### Test Execution Environment

**Development PC** (Unit & Integration Tests):
- Python 3.8+
- pytest framework
- Mock libraries for hardware

**Raspberry Pi Pico 2W** (System Tests):
- MicroPython runtime
- Actual hardware connections
- Serial console monitoring

## Unit Testing

### Test Structure

```python
# tests/test_display.py

import pytest
from src.display.hub75 import HUB75
from src.display.renderer import Renderer

class TestHUB75:
    """Unit tests for HUB75 display driver."""
    
    @pytest.fixture
    def display(self):
        """Create mock display for testing."""
        # Mock GPIO pins
        pins = {
            'r1': 0, 'g1': 1, 'b1': 2,
            'r2': 3, 'g2': 4, 'b2': 5,
            'a': 6, 'b': 7, 'c': 8, 'd': 9, 'e': 10,
            'clk': 11, 'lat': 12, 'oe': 13
        }
        return HUB75(width=64, height=64, pins=pins)
    
    def test_pixel_addressing(self, display):
        """Test pixel coordinate to buffer index calculation."""
        # Top-left corner
        assert display._pixel_index(0, 0) == 0
        
        # Top-right corner
        assert display._pixel_index(63, 0) == 63 * 3
        
        # Bottom-left corner
        assert display._pixel_index(0, 63) == 63 * 64 * 3
        
        # Center
        assert display._pixel_index(32, 32) == (32 * 64 + 32) * 3
    
    def test_set_pixel_color(self, display):
        """Test setting individual pixel colors."""
        display.set_pixel(10, 10, 255, 128, 64)
        
        idx = (10 * 64 + 10) * 3
        assert display.framebuffer[idx] == 255  # Red
        assert display.framebuffer[idx + 1] == 128  # Green
        assert display.framebuffer[idx + 2] == 64  # Blue
    
    def test_clear_display(self, display):
        """Test clearing display to color."""
        # Set some pixels
        display.set_pixel(0, 0, 255, 255, 255)
        display.set_pixel(32, 32, 255, 255, 255)
        
        # Clear to black
        display.clear(0, 0, 0)
        
        # Verify all zeros
        assert all(b == 0 for b in display.framebuffer)
    
    def test_brightness_control(self, display):
        """Test global brightness adjustment."""
        display.set_brightness(128)  # 50%
        display.set_pixel(0, 0, 255, 255, 255)
        
        # Colors should be scaled
        idx = 0
        assert display.framebuffer[idx] == 127  # 255 * 0.5
        assert display.framebuffer[idx + 1] == 127
        assert display.framebuffer[idx + 2] == 127

class TestRenderer:
    """Unit tests for rendering functions."""
    
    @pytest.fixture
    def renderer(self):
        """Create renderer with mock display."""
        display = HUB75(64, 64, {})
        return Renderer(display)
    
    def test_draw_text_basic(self, renderer):
        """Test basic text rendering."""
        renderer.draw_text(0, 0, "A", (255, 255, 255), 'font_5x7')
        
        # Verify pixels set for letter 'A'
        # (Implementation-specific verification)
    
    def test_text_alignment(self, renderer):
        """Test text alignment calculations."""
        text = "DET"
        width = renderer.get_text_width(text, 'font_5x7')
        
        # 3 chars * 5px + 2 spaces * 1px = 17px
        assert width == 17
        
        # Center alignment
        x_center = (64 - width) // 2
        assert x_center == 23
    
    def test_draw_number_large(self, renderer):
        """Test large number rendering for scores."""
        renderer.draw_large_number(10, 20, 42)
        
        # Verify both digits rendered
        # (Check specific pixels for '4' and '2')
```

### Running Unit Tests

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-mock

# Run all unit tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_display.py -v

# Run specific test
pytest tests/test_display.py::TestHUB75::test_pixel_addressing -v
```

### Test Cases by Module

#### Display Module Tests

```python
# test_display.py
✓ test_pixel_addressing
✓ test_set_pixel_color
✓ test_clear_display
✓ test_brightness_control
✓ test_framebuffer_bounds
✓ test_color_value_clipping

# test_renderer.py
✓ test_draw_text_basic
✓ test_text_alignment
✓ test_draw_number_large
✓ test_draw_game_layout
✓ test_scroll_animation
✓ test_fade_transition
```

#### API Module Tests

```python
# test_espn_client.py
✓ test_parse_scoreboard_response
✓ test_handle_empty_response
✓ test_handle_invalid_json
✓ test_timeout_handling
✓ test_cache_hit
✓ test_cache_expiration
✓ test_multiple_games_parsing

# test_game_parser.py
✓ test_parse_live_game
✓ test_parse_pregame
✓ test_parse_final_game
✓ test_missing_fields_handling
✓ test_score_parsing
✓ test_time_parsing
```

#### Configuration Module Tests

```python
# test_config.py
✓ test_load_default_config
✓ test_load_existing_config
✓ test_save_config_atomic
✓ test_config_validation
✓ test_add_team
✓ test_remove_team
✓ test_update_settings
✓ test_corrupt_config_recovery
✓ test_backup_creation
✓ test_schema_migration
```

#### Web Server Tests

```python
# test_web_server.py
✓ test_route_dispatch
✓ test_get_config_endpoint
✓ test_post_config_endpoint
✓ test_invalid_request_handling
✓ test_cors_headers
✓ test_status_endpoint
✓ test_teams_list_endpoint
```

## Integration Testing

### Module Integration Tests

#### Display + Renderer Integration

```python
# test_display_integration.py

def test_full_game_display():
    """Test complete game display rendering."""
    display = HUB75(64, 64, MOCK_PINS)
    renderer = Renderer(display)
    
    game_data = GameData(
        home_team="DET",
        away_team="GB",
        home_score=24,
        away_score=17,
        status="Q2",
        time_remaining="5:42"
    )
    
    # Render full layout
    renderer.draw_game_layout(game_data)
    display.show()
    
    # Verify key elements present
    assert_text_present(display, "DET")
    assert_text_present(display, "GB")
    assert_number_present(display, 24)
    assert_number_present(display, 17)
    assert_text_present(display, "Q2")
```

#### API + Parser Integration

```python
# test_api_integration.py

@pytest.mark.asyncio
async def test_fetch_and_parse_live_game():
    """Test fetching and parsing real API data."""
    client = ESPNClient()
    
    # Use recorded API response (VCR cassette)
    with vcr.use_cassette('espn_nfl_live_game.yaml'):
        games = await client.get_games_today('nfl')
    
    assert len(games) > 0
    
    game = games[0]
    assert game.home_team is not None
    assert game.away_team is not None
    assert isinstance(game.home_score, int)
    assert isinstance(game.away_score, int)
```

#### Config + Web Server Integration

```python
# test_config_web_integration.py

def test_web_config_update_flow():
    """Test web interface config update."""
    config_mgr = ConfigManager()
    server = WebServer(config_mgr)
    
    # Simulate POST request
    request = {
        'method': 'POST',
        'path': '/api/config',
        'body': {
            'teams': [
                {'sport': 'nfl', 'team_id': 'DET', 'team_name': 'Detroit Lions'}
            ]
        }
    }
    
    response = server.handle_request(request)
    
    assert response.status == 200
    assert len(config_mgr.config['teams']) == 1
    assert config_mgr.config['teams'][0]['team_id'] == 'DET'
```

### Integration Test Checklist

```
□ Display renders API data correctly
□ Web changes update display
□ Config persists across restarts
□ API errors handled gracefully
□ Cache reduces API calls
□ WiFi reconnection works
□ All modules communicate properly
```

## System Testing

### End-to-End Tests (On Hardware)

#### Test 1: Startup Sequence

```python
def test_system_startup():
    """Test complete startup sequence."""
    
    # Step 1: Power on
    reset_pico()
    
    # Step 2: Verify boot message
    assert_display_shows("Starting...")
    
    # Step 3: WiFi connection
    wait_for_wifi_connect(timeout=30)
    assert_display_shows_ip()
    
    # Step 4: Web server ready
    response = http_get("http://pico_ip/api/status")
    assert response.status == 200
    
    # Step 5: Display mode
    wait_for_display_state("idle", timeout=10)
    assert_display_mode() in ["idle", "live_game"]
```

#### Test 2: Live Game Display

```python
def test_live_game_display():
    """Test displaying live game from real API."""
    
    # Configure team
    http_post("http://pico_ip/api/config", {
        'teams': [{'sport': 'nfl', 'team_id': 'DET', 'team_name': 'Detroit Lions'}]
    })
    
    # Wait for API poll
    time.sleep(125)  # Just over 2 min interval
    
    # Verify display updated
    if game_is_live():
        assert_display_shows_scores()
        assert_display_shows_time()
    else:
        assert_display_shows("No games")
```

#### Test 3: Web Configuration

```python
def test_web_configuration():
    """Test web interface configuration."""
    
    # Open web interface
    browser = webdriver.Chrome()
    browser.get("http://pico_ip/")
    
    # Add team
    browser.find_element_by_id("add-team-btn").click()
    browser.find_element_by_id("sport-select").send_keys("NFL")
    browser.find_element_by_id("team-search").send_keys("Lions")
    browser.find_element_by_id("team-result-0").click()
    browser.find_element_by_id("save-btn").click()
    
    # Verify saved
    assert "Detroit Lions" in browser.page_source
    
    # Verify display updates
    time.sleep(2)
    assert_config_applied_to_display()
```

#### Test 4: Error Recovery

```python
def test_wifi_disconnect_recovery():
    """Test WiFi disconnection and recovery."""
    
    # Initial state: connected
    assert system_is_connected()
    
    # Disable WiFi router
    disable_wifi_router()
    
    # Wait for disconnect detection
    time.sleep(10)
    assert_display_shows("WiFi Lost")
    
    # Re-enable WiFi
    enable_wifi_router()
    
    # Verify reconnection
    wait_for_reconnect(timeout=60)
    assert_display_shows_normal()
    assert system_is_connected()
```

### System Test Checklist

```
Hardware Tests:
□ Display shows correct colors
□ All pixels functional
□ No flickering
□ Brightness adjustment works
□ Viewing angle acceptable

Software Tests:
□ Boots successfully every time
□ WiFi connects reliably
□ Web interface accessible
□ Configuration persists
□ API polling works
□ Display updates on schedule

Integration Tests:
□ Config changes reflect on display
□ Multiple games handled correctly
□ Time zones correct
□ All sports work (NFL, NBA, MLB, NHL)
□ Error states display properly

Stress Tests:
□ Runs 24 hours without crash
□ Handles rapid config changes
□ Survives network interruptions
□ Recovers from power loss
□ Memory doesn't leak
```

## Performance Testing

### Memory Testing

```python
def test_memory_usage():
    """Monitor memory usage over time."""
    
    import gc
    
    measurements = []
    
    for i in range(100):
        # Simulate normal operation
        poll_api()
        update_display()
        handle_web_requests()
        
        # Measure
        gc.collect()
        free = gc.mem_free()
        measurements.append(free)
        
        time.sleep(120)  # 2 min interval
    
    # Verify no significant memory leak
    initial = measurements[0]
    final = measurements[-1]
    drift = initial - final
    
    assert drift < 10000, f"Memory leaked {drift} bytes"
```

### Display Refresh Rate Testing

```python
def test_display_refresh_rate():
    """Measure actual refresh rate."""
    
    import time
    
    frame_times = []
    
    for i in range(100):
        start = time.ticks_us()
        display.show()
        end = time.ticks_us()
        
        frame_times.append(end - start)
    
    avg_frame_time = sum(frame_times) / len(frame_times)
    fps = 1_000_000 / avg_frame_time
    
    assert fps >= 60, f"Refresh rate {fps} Hz too low"
```

### API Response Time Testing

```python
def test_api_response_times():
    """Measure API call latency."""
    
    response_times = []
    
    for i in range(20):
        start = time.time()
        data = espn_client.get_games_today('nfl')
        end = time.time()
        
        response_times.append(end - start)
    
    avg_response = sum(response_times) / len(response_times)
    max_response = max(response_times)
    
    assert avg_response < 2.0, f"Average response {avg_response}s too slow"
    assert max_response < 5.0, f"Max response {max_response}s too slow"
```

### Performance Benchmarks

```
Metric                  Target      Acceptable    Failure
─────────────────────────────────────────────────────────
Refresh Rate            60 Hz       50 Hz         <40 Hz
API Response            <2s avg     <3s avg       >5s avg
Web Page Load           <1s         <2s           >3s
Config Save             <500ms      <1s           >2s
Display Update          <100ms      <200ms        >500ms
Memory Free             >100KB      >50KB         <20KB
Boot Time               <30s        <45s          >60s
WiFi Connect            <15s        <30s          >45s
```

## User Acceptance Testing

### UAT Scenarios

#### Scenario 1: First-Time Setup

**Given**: New device, never configured
**When**: User powers on device
**Then**:
1. Display shows welcome message
2. WiFi setup instructions clear
3. Web interface loads successfully
4. Team selection intuitive
5. Configuration saves
6. Device shows live scores

**Success Criteria**:
- Setup completed in <5 minutes
- No confusion about next steps
- No technical errors

#### Scenario 2: Daily Use

**Given**: Device configured with 2 teams
**When**: User checks scores throughout day
**Then**:
1. Live games display clearly
2. Scores update automatically
3. No manual intervention needed
4. Display readable from couch

**Success Criteria**:
- Scores always current
- No crashes during day
- Information easy to read

#### Scenario 3: Configuration Change

**Given**: User wants to add/remove teams
**When**: User accesses web interface
**Then**:
1. Interface loads quickly
2. Changes are intuitive
3. Save happens immediately
4. Display updates within 2 minutes

**Success Criteria**:
- Changes saved successfully
- No data loss
- Display reflects changes

### UAT Checklist

```
Setup Experience:
□ Welcome message clear
□ WiFi instructions easy to follow
□ Web interface intuitive
□ Team selection straightforward
□ Configuration saves properly

Daily Use:
□ Scores display clearly
□ Updates happen automatically
□ No manual interaction needed
□ Readable from intended distance
□ Shows all important info

Configuration:
□ Web interface loads fast
□ Changes are intuitive
□ Saves work reliably
□ Can undo mistakes
□ Help text available

Error Handling:
□ Error messages clear
□ Recovery automatic where possible
□ Status visible
□ No data loss
□ Can contact support if needed

Overall Experience:
□ Meets expectations
□ Would recommend to others
□ Looks professional
□ Functions reliably
□ Delivers value
```

## Continuous Testing

### Pre-Commit Tests

```bash
#!/bin/bash
# Run before each commit

echo "Running pre-commit tests..."

# Unit tests
pytest tests/unit/ -v --tb=short
if [ $? -ne 0 ]; then
    echo "Unit tests failed!"
    exit 1
fi

# Code quality
flake8 src/ --max-line-length=100
if [ $? -ne 0 ]; then
    echo "Code quality check failed!"
    exit 1
fi

echo "All pre-commit tests passed!"
```

### Weekly System Tests

```bash
#!/bin/bash
# Run comprehensive tests weekly

# Unit tests with coverage
pytest tests/ --cov=src --cov-report=html

# Integration tests
pytest tests/integration/ -v

# Upload to test Pico
./scripts/upload.sh

# Run system tests on hardware
./scripts/system_tests.sh

# Performance tests
./scripts/performance_tests.sh

# Generate report
./scripts/generate_test_report.sh
```

### Test Reporting

```
Test Report - 2024-12-21
═════════════════════════════════════════════

Unit Tests:          145 passed, 0 failed
Integration Tests:    23 passed, 0 failed
System Tests:         12 passed, 0 failed
Performance Tests:    PASS (all benchmarks met)

Code Coverage:       83%
Critical Paths:      97%

Issues Found:        0 critical, 2 minor
Known Bugs:          1 (cosmetic display glitch)

System Health:
- Memory Usage:      Normal (152KB free)
- Uptime:            7 days, 3 hours
- API Availability:  99.8%
- Display FPS:       62 Hz

Recommendation:      READY FOR DEPLOYMENT
```

## Testing Before Gift Delivery

### Final Pre-Delivery Checklist

```
□ All unit tests passing
□ All integration tests passing
□ 24-hour stability test completed
□ Web interface tested on multiple devices
□ All sports (NFL/NBA/MLB/NHL) verified
□ Error recovery tested
□ Memory leak check passed
□ Performance benchmarks met
□ Documentation complete
□ Setup instructions tested by non-technical person
□ Device cleaned and inspected
□ Power supply tested
□ Backup config available
□ Father-in-law's favorite teams pre-configured
□ WiFi credentials ready for his network
□ Gift wrapped with instructions included
```

### Burn-In Test

```bash
# Run for 48 hours before gift delivery
python burn_in_test.py --duration 48h --report burn_in_report.txt

# Monitors:
# - Memory usage
# - API call success rate
# - Display errors
# - WiFi disconnections
# - Web server uptime
# - Temperature (if sensor available)
```

## Conclusion

This testing strategy ensures:

✅ **Confidence**: Comprehensive coverage of all functionality
✅ **Quality**: Bugs caught early in development
✅ **Reliability**: System tested under real-world conditions
✅ **User Satisfaction**: UX validated before delivery
✅ **Maintenance**: Easy to add tests as features grow

Remember: **A well-tested gift is a reliable gift!** Your father-in-law will appreciate a device that just works, every time.
