# Sports Ticker Simulator

Test the Sports Ticker locally without hardware.

## Quick Start

```bash
cd simulator
python run_simulator.py
```

## Requirements

```bash
pip install requests
```

## Features

- **Terminal Display**: ANSI-colored simulation of LED matrix
- **Live Scores**: Real ESPN API data
- **Web Interface**: Local server on port 8080
- **Team Colors**: Authentic team color schemes
- **Keyboard Controls**: Interactive management

## Keyboard Controls

| Key | Action |
|-----|--------|
| `q` | Quit simulator |
| `r` | Refresh scores now |
| `d` | Toggle demo mode |
| `s` | Cycle sports (NFL/NBA/MLB/NHL) |
| `+` | Increase brightness |
| `-` | Decrease brightness |

## Web Interface

Open http://localhost:8080 in your browser to:
- Add/remove teams
- View current configuration
- Adjust settings
- See system status

## Display Modes

### Live Mode
Fetches real scores from ESPN API every 2 minutes.

### Demo Mode
Shows sample game data without API calls - useful for:
- Testing display layouts
- Development without internet
- Demonstrating functionality

## Configuration

Settings are stored in `../config.json`:

```json
{
    "teams": [
        {"sport": "nfl", "team_id": "DET", "team_name": "Detroit Lions"}
    ],
    "update_interval": 120,
    "brightness": 200
}
```

## Terminal Display

The simulator renders a scaled representation:

```
╔════════════════════════════════════════════════════════════════╗
║                      DET vs CHI                                 ║
║                                                                 ║
║               LIONS                    BEARS                    ║
║                 24        -              17                     ║
║                                                                 ║
║                    Q3  8:42                                     ║
╚════════════════════════════════════════════════════════════════╝
```

Colors are displayed using ANSI escape codes (works in most terminals).

## Troubleshooting

### "No module named requests"
```bash
pip install requests
```

### Colors not showing
Your terminal may not support ANSI colors. Try:
- macOS: Use Terminal.app or iTerm2
- Linux: Most terminals work
- Windows: Use Windows Terminal or enable ANSI in CMD

### API errors
- Check internet connection
- ESPN API may be rate-limited (wait a few minutes)
- Try demo mode with 'd' key

## Development

The simulator shares code structure with hardware deployment:
- Same configuration format
- Same API parsing logic
- Same web interface routes

Changes tested in simulator should work on Pico 2W hardware.
