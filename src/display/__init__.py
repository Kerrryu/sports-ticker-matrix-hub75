# Display module - LED matrix drivers and rendering

# Fonts are always available
from .fonts import FONT_5X7, FONT_6X8

# Simulator works on any Python
from .simulator import DisplaySimulator

# Hardware modules only available on MicroPython
try:
    from .hub75 import HUB75Display
    from .renderer import Renderer
except ImportError:
    # Running on CPython (development/simulator mode)
    HUB75Display = None
    Renderer = None
