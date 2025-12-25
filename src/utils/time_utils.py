"""
Time Utilities

Provides time-related functions for MicroPython.
Handles timezone conversion and NTP synchronization.

Usage:
    from utils.time_utils import get_local_time, sync_ntp, format_time
"""

import time

# Try to import ntptime (MicroPython)
try:
    import ntptime
    NTP_AVAILABLE = True
except ImportError:
    NTP_AVAILABLE = False


# Default timezone offset (Eastern Time)
_timezone_offset = -5  # Hours from UTC


def set_timezone(offset):
    """
    Set timezone offset from UTC.

    Args:
        offset: Hours offset (e.g., -5 for EST, -8 for PST)
    """
    global _timezone_offset
    _timezone_offset = offset


def get_timezone():
    """Get current timezone offset."""
    return _timezone_offset


def sync_ntp(timeout=10):
    """
    Synchronize system time with NTP server.

    Args:
        timeout: Connection timeout in seconds

    Returns:
        True if sync successful, False otherwise
    """
    if not NTP_AVAILABLE:
        print("TimeUtils: NTP not available")
        return False

    try:
        ntptime.timeout = timeout
        ntptime.settime()
        print("TimeUtils: NTP sync successful")
        return True
    except Exception as e:
        print(f"TimeUtils: NTP sync failed: {e}")
        return False


def get_utc_time():
    """
    Get current UTC time.

    Returns:
        Time tuple (year, month, day, hour, minute, second, weekday, yearday)
    """
    return time.gmtime()


def get_local_time():
    """
    Get current local time adjusted for timezone.

    Returns:
        Time tuple (year, month, day, hour, minute, second, weekday, yearday)
    """
    utc = time.time()
    local = utc + (_timezone_offset * 3600)
    return time.localtime(local)


def get_hour():
    """Get current local hour (0-23)."""
    return get_local_time()[3]


def get_minute():
    """Get current local minute (0-59)."""
    return get_local_time()[4]


def get_day_of_week():
    """
    Get current day of week.

    Returns:
        Day number (0=Monday, 6=Sunday)
    """
    return get_local_time()[6]


def format_time(t=None, include_seconds=False):
    """
    Format time as HH:MM or HH:MM:SS string.

    Args:
        t: Time tuple (uses current time if None)
        include_seconds: Include seconds in output

    Returns:
        Formatted time string
    """
    if t is None:
        t = get_local_time()

    hour = t[3]
    minute = t[4]
    second = t[5]

    if include_seconds:
        return f"{hour:02d}:{minute:02d}:{second:02d}"
    return f"{hour:02d}:{minute:02d}"


def format_time_12h(t=None):
    """
    Format time as 12-hour format with AM/PM.

    Args:
        t: Time tuple (uses current time if None)

    Returns:
        Formatted time string (e.g., "3:45 PM")
    """
    if t is None:
        t = get_local_time()

    hour = t[3]
    minute = t[4]

    period = "AM" if hour < 12 else "PM"
    hour_12 = hour % 12
    if hour_12 == 0:
        hour_12 = 12

    return f"{hour_12}:{minute:02d} {period}"


def format_date(t=None, short=False):
    """
    Format date as string.

    Args:
        t: Time tuple (uses current time if None)
        short: Use short format (MM/DD)

    Returns:
        Formatted date string
    """
    if t is None:
        t = get_local_time()

    year = t[0]
    month = t[1]
    day = t[2]

    if short:
        return f"{month}/{day}"
    return f"{month}/{day}/{year}"


def format_datetime(t=None):
    """
    Format date and time as string.

    Args:
        t: Time tuple (uses current time if None)

    Returns:
        Formatted datetime string
    """
    if t is None:
        t = get_local_time()

    return f"{format_date(t)} {format_time(t)}"


def is_dst():
    """
    Check if Daylight Saving Time is in effect.

    Simple approximation for US DST rules.
    Second Sunday in March to first Sunday in November.

    Returns:
        True if DST is in effect
    """
    t = get_local_time()
    month = t[1]
    day = t[2]
    weekday = t[6]  # 0=Monday

    # Not DST in Jan, Feb, Dec
    if month < 3 or month > 11:
        return False

    # Always DST in Apr-Oct
    if 4 <= month <= 10:
        return True

    # March: DST starts second Sunday
    if month == 3:
        # Find second Sunday
        # Day of first Sunday: (7 - weekday of 1st) % 7 + 1
        first_of_month_weekday = (weekday - (day - 1)) % 7
        first_sunday = (7 - first_of_month_weekday) % 7 + 1
        second_sunday = first_sunday + 7
        return day >= second_sunday

    # November: DST ends first Sunday
    if month == 11:
        first_of_month_weekday = (weekday - (day - 1)) % 7
        first_sunday = (7 - first_of_month_weekday) % 7 + 1
        return day < first_sunday

    return False


def seconds_until(hour, minute=0):
    """
    Calculate seconds until specified time.

    Args:
        hour: Target hour (0-23)
        minute: Target minute (0-59)

    Returns:
        Seconds until target time (may be next day)
    """
    now = get_local_time()
    current_hour = now[3]
    current_minute = now[4]
    current_second = now[5]

    # Convert to seconds since midnight
    current_secs = current_hour * 3600 + current_minute * 60 + current_second
    target_secs = hour * 3600 + minute * 60

    diff = target_secs - current_secs

    # If target is in the past, add a day
    if diff <= 0:
        diff += 24 * 3600

    return diff


def sleep_until(hour, minute=0):
    """
    Sleep until specified time.

    Args:
        hour: Target hour (0-23)
        minute: Target minute (0-59)
    """
    secs = seconds_until(hour, minute)
    time.sleep(secs)


def is_between_hours(start_hour, end_hour):
    """
    Check if current time is between two hours.

    Args:
        start_hour: Start hour (0-23)
        end_hour: End hour (0-23)

    Returns:
        True if current hour is in range
    """
    current = get_hour()

    if start_hour <= end_hour:
        # Simple range (e.g., 9-17)
        return start_hour <= current < end_hour
    else:
        # Overnight range (e.g., 23-7)
        return current >= start_hour or current < end_hour


def parse_game_time(time_str):
    """
    Parse game time string from API.

    Args:
        time_str: ISO format string (e.g., "2024-12-25T13:00:00Z")

    Returns:
        Local time tuple or None
    """
    try:
        # Simple ISO parsing (MicroPython compatible)
        # Format: "2024-12-25T13:00:00Z"
        date_part, time_part = time_str.replace('Z', '').split('T')

        year, month, day = map(int, date_part.split('-'))
        hour, minute, second = map(int, time_part.split(':')[:3])

        # Convert from UTC to local
        utc_secs = time.mktime((year, month, day, hour, minute, second, 0, 0))
        local_secs = utc_secs + (_timezone_offset * 3600)

        return time.localtime(local_secs)

    except Exception:
        return None


def format_game_time(time_str):
    """
    Format game time for display.

    Args:
        time_str: ISO format string from API

    Returns:
        Formatted string (e.g., "Today 1:00 PM" or "12/25 1:00 PM")
    """
    local = parse_game_time(time_str)
    if not local:
        return time_str

    now = get_local_time()
    game_month, game_day = local[1], local[2]
    now_month, now_day = now[1], now[2]

    time_12h = format_time_12h(local)

    if game_month == now_month and game_day == now_day:
        return f"Today {time_12h}"
    elif game_month == now_month and game_day == now_day + 1:
        return f"Tomorrow {time_12h}"
    else:
        return f"{game_month}/{game_day} {time_12h}"


# Test when run directly
if __name__ == '__main__':
    print("Time Utils Test")
    print("=" * 40)

    print(f"Timezone offset: UTC{_timezone_offset:+d}")
    print(f"UTC time: {format_time(get_utc_time(), include_seconds=True)}")
    print(f"Local time: {format_time(include_seconds=True)}")
    print(f"12-hour: {format_time_12h()}")
    print(f"Date: {format_date()}")
    print(f"Short date: {format_date(short=True)}")
    print(f"Full datetime: {format_datetime()}")
    print(f"Current hour: {get_hour()}")
    print(f"Day of week: {get_day_of_week()}")
    print(f"Is DST: {is_dst()}")
    print(f"Is 9-17: {is_between_hours(9, 17)}")
    print(f"Is 22-6: {is_between_hours(22, 6)}")
    print(f"Seconds until midnight: {seconds_until(0, 0)}")

    # Test game time parsing
    test_time = "2024-12-25T18:00:00Z"
    print(f"\nParsing: {test_time}")
    print(f"Formatted: {format_game_time(test_time)}")

    print("\nTime utils test complete!")
