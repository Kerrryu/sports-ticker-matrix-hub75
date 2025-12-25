# LED Sports Ticker

A MicroPython-based sports score display system for Raspberry Pi Pico 2W and 64x64 RGB LED matrix panel.

## Overview

This project displays live sports scores for your favorite teams on a 64x64 RGB LED matrix. It features a web interface for team selection and automatically polls sports APIs to show real-time game information when your teams are playing.

## Hardware Requirements

- **Raspberry Pi Pico 2W** - Microcontroller with WiFi
- **64x64 RGB LED Matrix Panel** - HUB75 interface
  - Resolution: 64x64 pixels
  - Pitch: 3mm
  - Scan rate: 1/32
  - Input voltage: 5V
- **5V Power Supply** - 4A minimum recommended for LED matrix
- **Jumper wires** - For connections

## Pin Connections

| Pico 2W GPIO | HUB75 Pin | Function |
|--------------|-----------|----------|
| GP0 | R1 | Red Data (Upper) |
| GP1 | G1 | Green Data (Upper) |
| GP2 | B1 | Blue Data (Upper) |
| GP3 | R2 | Red Data (Lower) |
| GP4 | G2 | Green Data (Lower) |
| GP5 | B2 | Blue Data (Lower) |
| GP6 | A | Row Select A |
| GP7 | B | Row Select B |
| GP8 | C | Row Select C |
| GP9 | D | Row Select D |
| GP10 | E | Row Select E |
| GP11 | CLK | Clock |
| GP12 | LAT | Latch |
| GP13 | OE | Output Enable |
| GND | GND | Ground |

**Power:** Connect 5V power supply directly to the LED matrix power terminals. Do NOT power the matrix from the Pico.

## Software Requirements

- MicroPython firmware for Pico 2W (latest stable version)
- Python 3.8+ (for development/testing)

## Installation

### 1. Flash MicroPython to Pico 2W

1. Download the latest MicroPython firmware for Pico 2W from [micropython.org](https://micropython.org/download/RPI_PICO2_W/)
2. Hold the BOOTSEL button while connecting Pico to your computer
3. Drag and drop the `.uf2` file to the RPI-RP2 drive
4. Wait for the Pico to restart

### 2. Upload Project Files

Using a tool like Thonny, ampy, or mpremote:

```bash
# Install mpremote if you don't have it
pip install mpremote

# Upload all project files
mpremote connect /dev/ttyACM0 fs cp -r src/ :
mpremote connect /dev/ttyACM0 fs cp config.json :
mpremote connect /dev/ttyACM0 fs cp main.py :
```

### 3. Configure WiFi

Create a `secrets.py` file in the root directory:

```python
WIFI_SSID = "YourWiFiNetwork"
WIFI_PASSWORD = "YourPassword"
```

Upload it to the Pico:

```bash
mpremote connect /dev/ttyACM0 fs cp secrets.py :
```

## Configuration

### Initial Setup

1. Connect to the Pico's web interface at `http://PICO_IP_ADDRESS` (IP shown on display at startup)
2. Select your favorite sports and teams
3. Scores will automatically update every 2 minutes during active games

### Config File Structure

The `config.json` file stores your preferences:

```json
{
  "teams": [
    {
      "sport": "nfl",
      "team_id": "DET",
      "team_name": "Detroit Lions"
    }
  ],
  "update_interval": 120,
  "brightness": 128
}
```

## Usage

### Starting the Ticker

The ticker starts automatically on power-up. It will:

1. Connect to WiFi
2. Display IP address briefly
3. Start polling for game data
4. Show scores when games are active
5. Display idle animation when no games are active

### Web Interface

Access the configuration page at `http://PICO_IP_ADDRESS/` to:

- Add/remove favorite teams
- Adjust display brightness
- Change update interval
- View system status

### Display Modes

- **Live Game**: Shows team logos, current score, quarter/period, and time remaining
- **Pre-Game**: Shows upcoming game time
- **Post-Game**: Shows final score
- **Idle**: Rotating team logos or custom message

## API Information

This project uses free sports APIs. Current support:

- **ESPN API** - NFL, NBA, MLB, NHL
- **The Sports DB** - Backup/fallback
- No API key required for basic functionality

## Troubleshooting

### Display Issues

- **No image on display**: Check power supply to matrix (needs 5V 4A)
- **Flickering**: Verify all HUB75 connections are secure
- **Wrong colors**: Double-check R1/G1/B1/R2/G2/B2 pin assignments

### WiFi Issues

- **Won't connect**: Verify `secrets.py` credentials
- **Connection drops**: Check WiFi signal strength, consider adding power supply capacitor

### API Issues

- **No scores showing**: Verify internet connectivity and API endpoints
- **Wrong team data**: Check team_id in config.json matches API format

## Development

See `docs/CONTEXT.md` for detailed development information.

### Running Tests

```bash
cd tests
python -m pytest test_display.py -v
python -m pytest test_api.py -v
python -m pytest test_config.py -v
```

## Project Structure

```
sports-ticker/
├── main.py                 # Entry point
├── config.json            # User configuration
├── secrets.py             # WiFi credentials (not in git)
├── src/
│   ├── display/           # LED matrix driver
│   ├── api/              # Sports API handlers
│   ├── web/              # Web server
│   └── utils/            # Helper functions
├── tests/                # Unit tests
└── docs/                 # Documentation
```

## Future Enhancements

- Multiple sport support in single view
- Weather display integration
- Custom animations
- Mobile app for configuration
- OTA updates

## License

MIT License - Free for personal use

## Credits

Built with ❤️ for a sports-loving father-in-law

## Support

For issues or questions, check the `docs/` folder or create an issue in the project repository.
