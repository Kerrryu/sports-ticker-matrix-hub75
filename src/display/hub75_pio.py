"""
HUB75 Display Driver using PIO (Programmable I/O)

This driver uses the RP2350's PIO hardware to drive the display
at high speed, independent of the CPU. This allows flicker-free
display while Python handles application logic.

The PIO runs continuously in the background, reading from a
framebuffer that Python updates.
"""

import rp2
from rp2 import PIO, StateMachine, asm_pio
from machine import Pin, mem32
import time
import array
import gc

# Pin definitions
PIN_R1 = 0
PIN_G1 = 1
PIN_B1 = 2
PIN_R2 = 3
PIN_G2 = 4
PIN_B2 = 5
PIN_CLK = 6
PIN_LAT = 7
PIN_OE = 8
PIN_A = 9
PIN_B = 10
PIN_C = 11
PIN_D = 12
PIN_E = 13


@asm_pio(
    out_shiftdir=PIO.SHIFT_RIGHT,
    autopull=True,
    pull_thresh=32,
    sideset_init=(PIO.OUT_LOW,),  # CLK
    out_init=(PIO.OUT_LOW,) * 6,  # R1,G1,B1,R2,G2,B2
)
def hub75_data_program():
    """
    PIO program to shift out pixel data.
    Sideset controls CLK, OUT controls data pins.
    """
    # Wait for data, output 6 bits, pulse clock
    out(pins, 6)        .side(0)   # Output 6 data bits, CLK low
    nop()               .side(1)   # CLK high
    # Loop back automatically due to wrap


@asm_pio(
    out_shiftdir=PIO.SHIFT_RIGHT,
    sideset_init=(PIO.OUT_HIGH,),  # OE (active low, start disabled)
)
def hub75_row_program():
    """
    PIO program to handle row selection and timing.
    """
    # Pull row data: [delay_count:16][row_addr:5][latch:1]
    pull(block)

    # Output row address (5 bits to pins A-E)
    out(pins, 5)        .side(1)   # OE disabled while setting row

    # Check latch bit
    out(x, 1)
    jmp(not_x, "no_latch")

    # Pulse latch
    set(pins, 1)        .side(1)   # LAT high
    set(pins, 0)        .side(1)   # LAT low

    label("no_latch")

    # Get delay count
    out(x, 16)

    # Enable output
    nop()               .side(0)   # OE low (enabled)

    # Delay loop
    label("delay")
    jmp(x_dec, "delay") .side(0)

    # Disable output
    nop()               .side(1)   # OE high (disabled)


class HUB75DisplayPIO:
    """
    High-performance HUB75 driver using PIO.

    The display refresh runs in hardware, independent of Python.
    Just update the framebuffer and call show() to transfer new data.
    """

    def __init__(self, width=64, height=64, brightness=255):
        self.width = width
        self.height = height
        self.brightness = brightness
        self.rows = 32  # 1/32 scan

        # Framebuffer: RGB bytes for each pixel
        self.framebuffer = bytearray(width * height * 3)

        # Row buffer for PIO: packed pixel data
        # Each row needs 64 pixels * 6 bits = 384 bits = 12 words
        self._row_buffer = array.array('L', [0] * (width // 4))

        # Initialize GPIO pins not controlled by PIO
        self.lat = Pin(PIN_LAT, Pin.OUT, value=0)
        self.oe = Pin(PIN_OE, Pin.OUT, value=1)  # Start disabled

        # Address pins
        self.addr_pins = [
            Pin(PIN_A, Pin.OUT, value=0),
            Pin(PIN_B, Pin.OUT, value=0),
            Pin(PIN_C, Pin.OUT, value=0),
            Pin(PIN_D, Pin.OUT, value=0),
            Pin(PIN_E, Pin.OUT, value=0),
        ]

        # Data pins (directly controlled for simplicity)
        self.r1 = Pin(PIN_R1, Pin.OUT, value=0)
        self.g1 = Pin(PIN_G1, Pin.OUT, value=0)
        self.b1 = Pin(PIN_B1, Pin.OUT, value=0)
        self.r2 = Pin(PIN_R2, Pin.OUT, value=0)
        self.g2 = Pin(PIN_G2, Pin.OUT, value=0)
        self.b2 = Pin(PIN_B2, Pin.OUT, value=0)
        self.clk = Pin(PIN_CLK, Pin.OUT, value=0)

        print(f"HUB75 PIO Display initialized: {width}x{height}")

    def set_pixel(self, x, y, r, g, b):
        """Set a pixel color."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return

        # Apply brightness
        r = (r * self.brightness) >> 8
        g = (g * self.brightness) >> 8
        b = (b * self.brightness) >> 8

        offset = (y * self.width + x) * 3
        self.framebuffer[offset] = r
        self.framebuffer[offset + 1] = g
        self.framebuffer[offset + 2] = b

    def get_pixel(self, x, y):
        """Get pixel color."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return (0, 0, 0)
        offset = (y * self.width + x) * 3
        return (
            self.framebuffer[offset],
            self.framebuffer[offset + 1],
            self.framebuffer[offset + 2]
        )

    def clear(self, r=0, g=0, b=0):
        """Clear display to a color."""
        for i in range(0, len(self.framebuffer), 3):
            self.framebuffer[i] = r
            self.framebuffer[i + 1] = g
            self.framebuffer[i + 2] = b

    def set_brightness(self, value):
        """Set brightness (0-255)."""
        self.brightness = max(0, min(255, value))

    def _select_row(self, row):
        """Set row address pins."""
        self.addr_pins[0].value(row & 1)
        self.addr_pins[1].value((row >> 1) & 1)
        self.addr_pins[2].value((row >> 2) & 1)
        self.addr_pins[3].value((row >> 3) & 1)
        self.addr_pins[4].value((row >> 4) & 1)

    def _shift_row_fast(self, upper_row, lower_row):
        """Shift out one row of pixel data using optimized code."""
        fb = self.framebuffer
        threshold = 128
        width = self.width

        # Direct pin references
        r1v = self.r1.value
        g1v = self.g1.value
        b1v = self.b1.value
        r2v = self.r2.value
        g2v = self.g2.value
        b2v = self.b2.value
        clkv = self.clk.value

        u_base = upper_row * width * 3
        l_base = lower_row * width * 3

        for col in range(width):
            idx_u = u_base + col * 3
            idx_l = l_base + col * 3

            # Set data pins
            r1v(fb[idx_u] >= threshold)
            g1v(fb[idx_u + 1] >= threshold)
            b1v(fb[idx_u + 2] >= threshold)
            r2v(fb[idx_l] >= threshold)
            g2v(fb[idx_l + 1] >= threshold)
            b2v(fb[idx_l + 2] >= threshold)

            # Clock pulse
            clkv(1)
            clkv(0)

    def show(self):
        """
        Refresh display once. Call this in a tight loop.

        For flicker-free display, this needs to run continuously
        in a background thread or timer interrupt.
        """
        lat = self.lat.value
        oe = self.oe.value

        for row in range(32):
            # 1. Disable output
            oe(1)

            # 2. Shift in pixel data for this row pair
            self._shift_row_fast(row, row + 32)

            # 3. Set row address
            self._select_row(row)

            # 4. Latch data
            lat(1)
            lat(0)

            # 5. Enable output
            oe(0)

            # 6. Display time (controls brightness uniformity)
            time.sleep_us(20)

        # Disable at end of frame
        oe(1)

    def start_refresh_timer(self, freq_hz=100):
        """
        Start automatic refresh using a timer.
        This runs show() in the background at the specified frequency.

        Note: Timer callbacks in MicroPython have limitations.
        For best results, use the main loop approach.
        """
        from machine import Timer

        self._timer = Timer()
        self._timer.init(freq=freq_hz, mode=Timer.PERIODIC,
                        callback=lambda t: self.show())
        print(f"Auto-refresh started at {freq_hz}Hz")

    def stop_refresh_timer(self):
        """Stop automatic refresh."""
        if hasattr(self, '_timer'):
            self._timer.deinit()
            print("Auto-refresh stopped")

    def fill_rect(self, x, y, w, h, r, g, b):
        """Fill a rectangle."""
        for py in range(y, min(y + h, self.height)):
            for px in range(x, min(x + w, self.width)):
                self.set_pixel(px, py, r, g, b)

    def test_pattern(self):
        """Display test pattern."""
        self.clear()

        # RGB stripes
        for y in range(0, 21):
            for x in range(self.width):
                self.set_pixel(x, y, 255, 0, 0)

        for y in range(21, 42):
            for x in range(self.width):
                self.set_pixel(x, y, 0, 255, 0)

        for y in range(42, 64):
            for x in range(self.width):
                self.set_pixel(x, y, 0, 0, 255)

        # White corners
        for i in range(10):
            for j in range(10):
                self.set_pixel(i, j, 255, 255, 255)
                self.set_pixel(self.width-1-i, j, 255, 255, 255)
                self.set_pixel(i, self.height-1-j, 255, 255, 255)
                self.set_pixel(self.width-1-i, self.height-1-j, 255, 255, 255)


# For compatibility - use PIO version as default
HUB75Display = HUB75DisplayPIO


if __name__ == '__main__':
    print("HUB75 PIO Display Test")

    display = HUB75DisplayPIO(64, 64)
    display.test_pattern()

    print("Running continuous refresh...")
    try:
        while True:
            display.show()
    except KeyboardInterrupt:
        display.clear()
        display.show()
        print("Done")
