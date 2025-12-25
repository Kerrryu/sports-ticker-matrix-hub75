"""
Tests for Display Module

Tests display functionality including:
- Simulator rendering
- Font rendering
- Color calculations
- Coordinate handling
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Use simulator for testing (no hardware required)
from display.simulator import DisplaySimulator
from display.fonts import get_char_bitmap, get_text_width, get_font_height, FONT_5X7, FONT_6X8


class TestDisplaySimulator:
    """Tests for DisplaySimulator class."""

    def test_init(self):
        """Test simulator initialization."""
        display = DisplaySimulator(64, 64)
        assert display.width == 64
        assert display.height == 64
        assert len(display.framebuffer) == 64 * 64 * 3
        assert display.brightness == 255

    def test_set_pixel_valid(self):
        """Test setting pixels within bounds."""
        display = DisplaySimulator(64, 64)
        display.set_pixel(10, 10, 255, 0, 0)
        r, g, b = display.get_pixel(10, 10)
        assert r == 255
        assert g == 0
        assert b == 0

    def test_set_pixel_out_of_bounds(self):
        """Test that out-of-bounds pixels are ignored."""
        display = DisplaySimulator(64, 64)
        # These should not raise exceptions
        display.set_pixel(-1, 10, 255, 0, 0)
        display.set_pixel(10, -1, 255, 0, 0)
        display.set_pixel(64, 10, 255, 0, 0)
        display.set_pixel(10, 64, 255, 0, 0)
        display.set_pixel(100, 100, 255, 0, 0)

    def test_clear(self):
        """Test clearing display."""
        display = DisplaySimulator(64, 64)
        display.set_pixel(10, 10, 255, 0, 0)
        display.clear()
        r, g, b = display.get_pixel(10, 10)
        assert r == 0 and g == 0 and b == 0

    def test_clear_with_color(self):
        """Test clearing with specific color."""
        display = DisplaySimulator(64, 64)
        display.clear(0, 255, 0)  # Green
        r, g, b = display.get_pixel(0, 0)
        assert r == 0 and g == 255 and b == 0

    def test_brightness(self):
        """Test brightness affects pixel values."""
        display = DisplaySimulator(64, 64)
        display.set_brightness(128)  # 50% brightness
        display.set_pixel(10, 10, 255, 255, 255)
        r, g, b = display.get_pixel(10, 10)
        # At 50% brightness, values should be about 127
        assert 126 <= r <= 128
        assert 126 <= g <= 128
        assert 126 <= b <= 128

    def test_brightness_clamp(self):
        """Test brightness is clamped to valid range."""
        display = DisplaySimulator(64, 64)
        display.set_brightness(-50)
        assert display.brightness == 0
        display.set_brightness(500)
        assert display.brightness == 255

    def test_multiple_pixels(self):
        """Test setting multiple pixels."""
        display = DisplaySimulator(64, 64)
        for x in range(10):
            display.set_pixel(x, 0, x * 25, 0, 0)

        for x in range(10):
            r, g, b = display.get_pixel(x, 0)
            assert r == x * 25


class TestFonts:
    """Tests for font rendering."""

    def test_font_5x7_exists(self):
        """Test 5x7 font has characters."""
        assert 'A' in FONT_5X7
        assert '0' in FONT_5X7
        assert ' ' in FONT_5X7

    def test_font_6x8_exists(self):
        """Test 6x8 font has characters."""
        assert 'A' in FONT_6X8
        assert '0' in FONT_6X8
        assert ' ' in FONT_6X8

    def test_get_char_bitmap_5x7(self):
        """Test getting character bitmap."""
        bitmap = get_char_bitmap('A', FONT_5X7)
        assert bitmap is not None
        assert len(bitmap) == 7  # 7 rows

    def test_get_char_bitmap_missing(self):
        """Test getting missing character returns default."""
        # Unicode character not in font
        bitmap = get_char_bitmap('\u2605', FONT_5X7)
        # Should return space or question mark
        assert bitmap is not None

    def test_get_text_width(self):
        """Test text width calculation."""
        width = get_text_width('ABC', FONT_5X7)
        # 3 characters * 5 pixels + 2 gaps = 17
        assert width == 17

    def test_get_text_width_empty(self):
        """Test empty text width."""
        width = get_text_width('', FONT_5X7)
        assert width == 0

    def test_get_font_height(self):
        """Test font height."""
        assert get_font_height(FONT_5X7) == 7
        assert get_font_height(FONT_6X8) == 8


class TestRendererHelpers:
    """Tests for renderer helper functions."""

    def test_draw_horizontal_line(self):
        """Test drawing horizontal line."""
        display = DisplaySimulator(64, 64)
        for x in range(10, 20):
            display.set_pixel(x, 10, 255, 255, 255)

        for x in range(10, 20):
            r, g, b = display.get_pixel(x, 10)
            assert r == 255

    def test_draw_vertical_line(self):
        """Test drawing vertical line."""
        display = DisplaySimulator(64, 64)
        for y in range(10, 20):
            display.set_pixel(10, y, 255, 255, 255)

        for y in range(10, 20):
            r, g, b = display.get_pixel(10, y)
            assert r == 255

    def test_draw_rectangle(self):
        """Test drawing rectangle outline."""
        display = DisplaySimulator(64, 64)

        # Draw rectangle from (10,10) to (20,20)
        for x in range(10, 21):
            display.set_pixel(x, 10, 255, 0, 0)  # Top
            display.set_pixel(x, 20, 255, 0, 0)  # Bottom
        for y in range(10, 21):
            display.set_pixel(10, y, 255, 0, 0)  # Left
            display.set_pixel(20, y, 255, 0, 0)  # Right

        # Check corners
        r, g, b = display.get_pixel(10, 10)
        assert r == 255
        r, g, b = display.get_pixel(20, 20)
        assert r == 255

        # Check center is empty
        r, g, b = display.get_pixel(15, 15)
        assert r == 0


class TestColorUtilities:
    """Tests for color-related functions."""

    def test_rgb_values(self):
        """Test RGB value handling."""
        display = DisplaySimulator(64, 64)

        # Test pure colors
        display.set_pixel(0, 0, 255, 0, 0)
        display.set_pixel(1, 0, 0, 255, 0)
        display.set_pixel(2, 0, 0, 0, 255)

        assert display.get_pixel(0, 0) == (255, 0, 0)
        assert display.get_pixel(1, 0) == (0, 255, 0)
        assert display.get_pixel(2, 0) == (0, 0, 255)

    def test_color_mix(self):
        """Test mixed colors."""
        display = DisplaySimulator(64, 64)

        # Yellow = Red + Green
        display.set_pixel(0, 0, 255, 255, 0)
        assert display.get_pixel(0, 0) == (255, 255, 0)

        # White
        display.set_pixel(1, 0, 255, 255, 255)
        assert display.get_pixel(1, 0) == (255, 255, 255)


def run_tests():
    """Run all tests and print results."""
    import traceback

    test_classes = [
        TestDisplaySimulator,
        TestFonts,
        TestRendererHelpers,
        TestColorUtilities,
    ]

    passed = 0
    failed = 0
    errors = []

    for test_class in test_classes:
        print(f"\n{test_class.__name__}")
        print("-" * 40)

        instance = test_class()

        for method_name in dir(instance):
            if not method_name.startswith('test_'):
                continue

            try:
                method = getattr(instance, method_name)
                method()
                print(f"  [PASS] {method_name}")
                passed += 1
            except AssertionError as e:
                print(f"  [FAIL] {method_name}: {e}")
                failed += 1
                errors.append((method_name, str(e)))
            except Exception as e:
                print(f"  [ERROR] {method_name}: {e}")
                failed += 1
                errors.append((method_name, traceback.format_exc()))

    print("\n" + "=" * 40)
    print(f"Results: {passed} passed, {failed} failed")

    if errors:
        print("\nFailures:")
        for name, error in errors:
            print(f"  - {name}: {error}")

    return failed == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
