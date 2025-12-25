"""
Renderer - High-level Drawing Functions for LED Matrix

Provides drawing primitives and game display layouts for the sports ticker.
Works with any display that implements set_pixel(), clear(), and show().

Usage:
    from display import HUB75Display, Renderer

    display = HUB75Display(64, 64)
    renderer = Renderer(display)

    renderer.draw_text(10, 10, "HELLO", (255, 255, 0))
    renderer.draw_game(game_data)
    display.show()
"""

from .fonts import FONT_5X7, FONT_6X8, get_char_bitmap, get_text_width, get_font_height

# Team colors (primary color for each team)
# Note: For teams that share abbreviations across sports (like DET),
# we use one common color. For Detroit: Honolulu Blue (Lions)
TEAM_COLORS = {
    # NFL
    'DET': (0, 118, 182),    # Honolulu Blue (Lions/Tigers/Pistons/Red Wings share)
    'GB': (24, 48, 40),      # Green
    'CHI': (11, 22, 42),     # Navy
    'MIN': (79, 38, 131),    # Purple
    'KC': (227, 24, 55),     # Red
    'BUF': (0, 51, 141),     # Blue
    'SF': (170, 0, 0),       # Red
    'PHI': (0, 76, 84),      # Green
    'DAL': (0, 53, 148),     # Blue
    'MIA': (0, 142, 151),    # Aqua
    'BAL': (36, 23, 115),    # Purple
    'CIN': (251, 79, 20),    # Orange
    'CLE': (49, 53, 58),     # Brown
    'PIT': (255, 182, 18),   # Gold
    'NE': (0, 34, 68),       # Navy
    'NYJ': (18, 87, 64),     # Green
    'NYG': (1, 35, 82),      # Blue
    'WAS': (90, 20, 20),     # Burgundy
    'TEN': (75, 146, 219),   # Light Blue
    'IND': (0, 44, 95),      # Blue
    'JAX': (0, 103, 120),    # Teal
    'HOU': (3, 32, 47),      # Navy (Texans)
    'DEN': (251, 79, 20),    # Orange
    'LV': (0, 0, 0),         # Black (Raiders)
    'LAC': (0, 128, 198),    # Powder Blue
    'ARI': (151, 35, 63),    # Cardinal Red
    'ATL': (167, 25, 48),    # Red (Falcons)
    'CAR': (0, 133, 202),    # Blue
    'NO': (211, 188, 141),   # Gold
    'TB': (213, 10, 10),     # Red
    'SEA': (0, 34, 68),      # Navy
    'LAR': (0, 53, 148),     # Blue

    # NBA
    'LAL': (85, 37, 130),    # Purple
    'BOS': (0, 122, 51),     # Green
    'GSW': (29, 66, 138),    # Blue
    'MIL': (0, 71, 27),      # Green
    'PHX': (29, 17, 96),     # Purple
    'DEN': (13, 34, 64),     # Navy (Nuggets)
    'OKC': (0, 125, 195),    # Blue
    'SAC': (91, 43, 130),    # Purple
    'POR': (224, 58, 62),    # Red

    # MLB
    'NYY': (0, 48, 135),     # Navy
    'LAD': (0, 90, 156),     # Blue
    'ATL': (206, 17, 65),    # Red (Braves)
    'HOU': (235, 110, 31),   # Orange (Astros)
    'STL': (196, 30, 58),    # Red (Cardinals)
    'CHC': (14, 51, 134),    # Blue (Cubs)
    'SD': (47, 36, 29),      # Brown
    'TEX': (0, 50, 120),     # Blue (Rangers)

    # NHL
    'TOR': (0, 32, 91),      # Blue
    'EDM': (4, 30, 66),      # Blue
    'VGK': (185, 151, 91),   # Gold
    'COL': (111, 38, 61),    # Burgundy
    'BOS': (252, 181, 20),   # Gold (Bruins)
    'MTL': (175, 30, 45),    # Red (Canadiens)
    'TB': (0, 40, 104),      # Blue (Lightning)
    'FLA': (200, 16, 46),    # Red (Panthers)
    'CAR': (206, 17, 38),    # Red (Hurricanes)
    'NYR': (0, 56, 168),     # Blue (Rangers)
    'PIT': (252, 181, 20),   # Gold (Penguins)
    'WSH': (200, 16, 46),    # Red (Capitals)
}

# Default colors
DEFAULT_TEAM_COLOR = (128, 128, 128)  # Gray
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
DIM_WHITE = (100, 100, 100)


class Renderer:
    """High-level rendering for LED matrix display."""

    def __init__(self, display):
        """
        Initialize renderer.

        Args:
            display: Display object with set_pixel(), clear(), show() methods
        """
        self.display = display
        self.width = display.width
        self.height = display.height

    def draw_pixel(self, x, y, color):
        """
        Draw single pixel.

        Args:
            x, y: Coordinates
            color: (r, g, b) tuple
        """
        self.display.set_pixel(x, y, color[0], color[1], color[2])

    def draw_text(self, x, y, text, color, font=FONT_5X7, spacing=1):
        """
        Draw text string.

        Args:
            x, y: Top-left position
            text: Text to draw
            color: (r, g, b) tuple
            font: Font to use
            spacing: Pixels between characters
        """
        char_width = font.get('width', 5)
        char_height = font.get('height', 7)

        cursor_x = x
        for char in text.upper():  # Uppercase for consistency
            bitmap = get_char_bitmap(char, font)
            if bitmap:
                for row_idx, row_data in enumerate(bitmap):
                    for col_idx in range(char_width):
                        # Check if pixel is set (MSB first)
                        if row_data & (1 << (char_width - 1 - col_idx)):
                            px = cursor_x + col_idx
                            py = y + row_idx
                            if 0 <= px < self.width and 0 <= py < self.height:
                                self.draw_pixel(px, py, color)

            cursor_x += char_width + spacing

    def draw_text_centered(self, y, text, color, font=FONT_5X7):
        """Draw text centered horizontally."""
        text_width = get_text_width(text, font)
        x = (self.width - text_width) // 2
        self.draw_text(x, y, text, color, font)

    def draw_rect(self, x, y, w, h, color, filled=False):
        """
        Draw rectangle.

        Args:
            x, y: Top-left corner
            w, h: Width and height
            color: (r, g, b) tuple
            filled: If True, fill rectangle
        """
        if filled:
            for py in range(y, min(y + h, self.height)):
                for px in range(x, min(x + w, self.width)):
                    self.draw_pixel(px, py, color)
        else:
            # Top and bottom
            for px in range(x, min(x + w, self.width)):
                self.draw_pixel(px, y, color)
                self.draw_pixel(px, y + h - 1, color)
            # Left and right
            for py in range(y, min(y + h, self.height)):
                self.draw_pixel(x, py, color)
                self.draw_pixel(x + w - 1, py, color)

    def draw_line(self, x0, y0, x1, y1, color):
        """Draw line using Bresenham's algorithm."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy

        while True:
            self.draw_pixel(x0, y0, color)

            if x0 == x1 and y0 == y1:
                break

            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def draw_game(self, game):
        """
        Draw game score display.

        Args:
            game: Dict with keys: home_team, away_team, home_score, away_score,
                  status, period/quarter, time_remaining
        """
        self.display.clear()

        # Get team info
        away_team = game.get('away_team', 'AWY')[:3].upper()
        home_team = game.get('home_team', 'HME')[:3].upper()
        away_score = str(game.get('away_score', 0))
        home_score = str(game.get('home_score', 0))
        status = game.get('status', 'pre')
        period = game.get('period', '')
        time_remaining = game.get('time_remaining', '')

        # Get team colors
        away_color = TEAM_COLORS.get(away_team, DEFAULT_TEAM_COLOR)
        home_color = TEAM_COLORS.get(home_team, DEFAULT_TEAM_COLOR)

        # Layout:
        # Row 0-10: Away team name + score
        # Row 11-20: Separator
        # Row 21-31: Home team name + score (with @ symbol)
        # Row 32-45: Status/period
        # Row 46-63: Time remaining

        # Away team (top)
        self.draw_text(4, 4, away_team, away_color, FONT_6X8)
        self.draw_text(40, 4, away_score, WHITE, FONT_6X8)

        # Separator
        self.draw_line(4, 18, 60, 18, DIM_WHITE)

        # @ symbol
        self.draw_text(28, 20, "@", DIM_WHITE, FONT_5X7)

        # Home team (bottom)
        self.draw_text(4, 26, home_team, home_color, FONT_6X8)
        self.draw_text(40, 26, home_score, WHITE, FONT_6X8)

        # Status area
        if status == 'live' or status == 'in':
            # Show period and time
            period_text = period if period else 'LIVE'
            self.draw_text_centered(42, period_text, YELLOW, FONT_5X7)

            if time_remaining:
                self.draw_text_centered(52, time_remaining, WHITE, FONT_5X7)
        elif status == 'final' or status == 'post':
            self.draw_text_centered(48, "FINAL", RED, FONT_5X7)
        elif status == 'pre':
            self.draw_text_centered(48, "UPCOMING", DIM_WHITE, FONT_5X7)

    def draw_idle(self):
        """Draw idle screen when no games active."""
        self.display.clear()

        # Simple animation or team logo placeholder
        self.draw_text_centered(20, "SPORTS", YELLOW, FONT_5X7)
        self.draw_text_centered(32, "TICKER", YELLOW, FONT_5X7)

        # Decorative lines
        self.draw_line(10, 45, 54, 45, DIM_WHITE)
        self.draw_line(10, 15, 54, 15, DIM_WHITE)

    def draw_upcoming_games(self, games):
        """
        Draw upcoming games schedule when no active games.

        Args:
            games: List of upcoming game dicts with keys:
                   home_team, away_team, sport, date, time
        """
        self.display.clear()

        if not games:
            self.draw_idle()
            return

        # Show up to 3 upcoming games
        y_pos = 2
        row_height = 20  # 3 games: y=2, y=22, y=42 (all fit in 64px)

        for i, game in enumerate(games[:3]):
            away = game.get('away_team', '???')[:3].upper()
            home = game.get('home_team', '???')[:3].upper()
            sport = game.get('sport', 'nfl').upper()

            # Get team colors
            away_color = TEAM_COLORS.get(away, DEFAULT_TEAM_COLOR)
            home_color = TEAM_COLORS.get(home, DEFAULT_TEAM_COLOR)

            # Sport indicator: colored vertical bar on left edge
            sport_colors = {'NFL': (0, 180, 0), 'NBA': (255, 120, 0), 'NHL': (0, 120, 255), 'MLB': (220, 0, 0)}
            sport_color = sport_colors.get(sport, DIM_WHITE)
            # Draw 2px wide bar
            for dy in range(16):
                self.draw_pixel(0, y_pos + dy, sport_color)
                self.draw_pixel(1, y_pos + dy, sport_color)

            # Row 1: "AWY @ HME" - shifted right to make room for bar
            self.draw_text(4, y_pos, away, away_color, FONT_5X7)
            self.draw_text(23, y_pos, "@", DIM_WHITE, FONT_5X7)
            self.draw_text(30, y_pos, home, home_color, FONT_5X7)

            # Row 2: Date on left, time on right
            game_date = game.get('date', '')
            game_time = game.get('time', '')

            # Format date shorter: "Dec 25" -> "12/25"
            if game_date:
                months = {'Jan': '1', 'Feb': '2', 'Mar': '3', 'Apr': '4', 'May': '5', 'Jun': '6',
                          'Jul': '7', 'Aug': '8', 'Sep': '9', 'Oct': '10', 'Nov': '11', 'Dec': '12'}
                parts = game_date.split()
                if len(parts) == 2 and parts[0] in months:
                    game_date = f"{months[parts[0]]}/{parts[1]}"

            # Format time: "9:30 PM" -> "9:30" (drop AM/PM to save space)
            time_short = ''
            if game_time:
                time_short = game_time.replace(' AM', '').replace(' PM', '').replace('AM', '').replace('PM', '')
                # Remove leading zero from hour if present
                if time_short.startswith('0'):
                    time_short = time_short[1:]

            # Draw date on left, time on right with guaranteed gap
            # Date max "12/25" = 5 chars = 30px, ends at x=34
            # Time starts at x=36 minimum to ensure gap
            self.draw_text(4, y_pos + 9, game_date, DIM_WHITE, FONT_5X7)
            if time_short:
                # Right-align time but don't go past x=36
                time_width = len(time_short) * 6
                time_x = max(36, 58 - time_width)
                self.draw_text(time_x, y_pos + 9, time_short, (150, 150, 150), FONT_5X7)

            y_pos += row_height

            # Draw separator line between games
            if i < min(len(games), 3) - 1:
                self.draw_line(3, y_pos - 1, 62, y_pos - 1, (30, 30, 30))

    def draw_connecting(self):
        """Draw WiFi connecting screen."""
        self.display.clear()
        self.draw_text_centered(25, "WIFI", YELLOW, FONT_5X7)
        self.draw_text_centered(35, "...", WHITE, FONT_5X7)

    def draw_error(self, message):
        """Draw error message."""
        self.display.clear()
        self.draw_text_centered(20, "ERROR", RED, FONT_5X7)
        # Truncate message to fit
        if len(message) > 10:
            message = message[:10]
        self.draw_text_centered(35, message, WHITE, FONT_5X7)

    def draw_update_available(self, version):
        """Draw update notification."""
        self.display.clear()
        self.draw_text_centered(15, "UPDATE", YELLOW, FONT_5X7)
        self.draw_text_centered(28, f"v{version}", WHITE, FONT_5X7)
        self.draw_text_centered(41, "AVAIL", YELLOW, FONT_5X7)

    def draw_progress(self, percent, label=""):
        """
        Draw progress bar.

        Args:
            percent: 0-100
            label: Optional label above bar
        """
        self.display.clear()

        if label:
            self.draw_text_centered(20, label, WHITE, FONT_5X7)

        # Progress bar outline
        bar_x = 8
        bar_y = 35
        bar_w = 48
        bar_h = 8
        self.draw_rect(bar_x, bar_y, bar_w, bar_h, DIM_WHITE)

        # Progress fill
        fill_w = int((bar_w - 2) * percent / 100)
        if fill_w > 0:
            self.draw_rect(bar_x + 1, bar_y + 1, fill_w, bar_h - 2, GREEN, filled=True)

        # Percentage text
        self.draw_text_centered(50, f"{percent}%", WHITE, FONT_5X7)

    def draw_ip_address(self, ip):
        """Draw IP address for user."""
        self.display.clear()
        self.draw_text_centered(15, "IP:", DIM_WHITE, FONT_5X7)

        # Split IP into lines if needed
        parts = ip.split('.')
        if len(parts) == 4:
            line1 = f"{parts[0]}.{parts[1]}"
            line2 = f".{parts[2]}.{parts[3]}"
            self.draw_text_centered(28, line1, WHITE, FONT_5X7)
            self.draw_text_centered(38, line2, WHITE, FONT_5X7)
        else:
            self.draw_text_centered(30, ip[:10], WHITE, FONT_5X7)

    def draw_scoreboard(self, games):
        """
        Draw multi-game scoreboard.

        Args:
            games: List of game dicts
        """
        self.display.clear()

        if not games:
            self.draw_idle()
            return

        # Show up to 2 games stacked
        y_offset = 0
        for i, game in enumerate(games[:2]):
            if i > 0:
                y_offset = 32
                self.draw_line(0, 31, 64, 31, DIM_WHITE)

            away = game.get('away_team', 'AWY')[:3]
            home = game.get('home_team', 'HME')[:3]
            away_score = str(game.get('away_score', 0))
            home_score = str(game.get('home_score', 0))

            away_color = TEAM_COLORS.get(away, DEFAULT_TEAM_COLOR)
            home_color = TEAM_COLORS.get(home, DEFAULT_TEAM_COLOR)

            # Compact layout
            self.draw_text(2, y_offset + 4, away, away_color, FONT_5X7)
            self.draw_text(40, y_offset + 4, away_score, WHITE, FONT_5X7)
            self.draw_text(2, y_offset + 16, home, home_color, FONT_5X7)
            self.draw_text(40, y_offset + 16, home_score, WHITE, FONT_5X7)


# Test when run directly
if __name__ == '__main__':
    print("Renderer test - using simulator")

    from simulator import DisplaySimulator

    display = DisplaySimulator(64, 64)
    renderer = Renderer(display)

    # Test text
    print("\nTest: Drawing text")
    renderer.draw_text(5, 5, "HELLO", WHITE)
    renderer.draw_text(5, 15, "WORLD", YELLOW)
    display.show('compact')

    # Test game display
    print("\nTest: Game display")
    display.clear()
    game = {
        'away_team': 'DET',
        'home_team': 'GB',
        'away_score': 24,
        'home_score': 17,
        'status': 'live',
        'period': 'Q2',
        'time_remaining': '5:42'
    }
    renderer.draw_game(game)
    display.show('compact')

    # Test idle
    print("\nTest: Idle screen")
    renderer.draw_idle()
    display.show('compact')

    print("\nRenderer tests complete!")
