"""
Logger Utility

Provides simple logging for MicroPython with optional file output.
Designed for minimal memory footprint.

Usage:
    from utils.logger import Logger, get_logger

    log = Logger('MyModule')
    log.info('Starting up')
    log.error('Something went wrong')
"""

import time
import gc

# Log levels
DEBUG = 10
INFO = 20
WARNING = 30
ERROR = 40
CRITICAL = 50

LEVEL_NAMES = {
    DEBUG: 'DEBUG',
    INFO: 'INFO',
    WARNING: 'WARN',
    ERROR: 'ERROR',
    CRITICAL: 'CRIT',
}

# Global settings
_global_level = INFO
_file_logging = False
_log_file = None
_max_file_size = 50000  # 50KB max log file
_loggers = {}


def set_level(level):
    """Set global log level."""
    global _global_level
    _global_level = level


def enable_file_logging(filename='logs/debug.log', max_size=50000):
    """
    Enable logging to file.

    Args:
        filename: Log file path
        max_size: Maximum file size in bytes
    """
    global _file_logging, _log_file, _max_file_size
    _file_logging = True
    _log_file = filename
    _max_file_size = max_size

    # Create logs directory if needed
    try:
        import os
        parts = filename.split('/')
        if len(parts) > 1:
            dir_path = '/'.join(parts[:-1])
            try:
                os.mkdir(dir_path)
            except OSError:
                pass  # Directory exists
    except ImportError:
        pass


def disable_file_logging():
    """Disable file logging."""
    global _file_logging
    _file_logging = False


class Logger:
    """Simple logger with module name prefix."""

    def __init__(self, name, level=None):
        """
        Initialize logger.

        Args:
            name: Module/component name
            level: Log level (uses global if None)
        """
        self.name = name
        self._level = level

    @property
    def level(self):
        """Get effective log level."""
        return self._level if self._level is not None else _global_level

    @level.setter
    def level(self, value):
        """Set logger-specific level."""
        self._level = value

    def _log(self, level, message, *args):
        """
        Internal log method.

        Args:
            level: Log level
            message: Message string (can use % formatting)
            args: Format arguments
        """
        if level < self.level:
            return

        # Format message
        if args:
            try:
                message = message % args
            except:
                pass

        # Get timestamp
        try:
            t = time.localtime()
            timestamp = "{:02d}:{:02d}:{:02d}".format(t[3], t[4], t[5])
        except:
            timestamp = "??:??:??"

        # Build log line
        level_name = LEVEL_NAMES.get(level, '???')
        line = f"[{timestamp}] {level_name} {self.name}: {message}"

        # Print to console
        print(line)

        # Write to file if enabled
        if _file_logging and _log_file:
            self._write_to_file(line)

    def _write_to_file(self, line):
        """Write log line to file."""
        try:
            # Check file size and rotate if needed
            try:
                import os
                size = os.stat(_log_file)[6]
                if size > _max_file_size:
                    self._rotate_log()
            except OSError:
                pass  # File doesn't exist yet

            # Append to file
            with open(_log_file, 'a') as f:
                f.write(line + '\n')

        except Exception as e:
            print(f"Log write error: {e}")

    def _rotate_log(self):
        """Rotate log file when it gets too large."""
        try:
            import os

            # Delete old backup
            try:
                os.remove(_log_file + '.old')
            except OSError:
                pass

            # Rename current to backup
            try:
                os.rename(_log_file, _log_file + '.old')
            except OSError:
                pass

        except ImportError:
            pass

    def debug(self, message, *args):
        """Log debug message."""
        self._log(DEBUG, message, *args)

    def info(self, message, *args):
        """Log info message."""
        self._log(INFO, message, *args)

    def warning(self, message, *args):
        """Log warning message."""
        self._log(WARNING, message, *args)

    def warn(self, message, *args):
        """Log warning message (alias)."""
        self._log(WARNING, message, *args)

    def error(self, message, *args):
        """Log error message."""
        self._log(ERROR, message, *args)

    def critical(self, message, *args):
        """Log critical message."""
        self._log(CRITICAL, message, *args)

    def exception(self, message, exc=None):
        """Log error with exception info."""
        if exc:
            self._log(ERROR, f"{message}: {type(exc).__name__}: {exc}")
        else:
            self._log(ERROR, message)


def get_logger(name):
    """
    Get or create a logger by name.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    global _loggers

    if name not in _loggers:
        _loggers[name] = Logger(name)

    return _loggers[name]


# Memory monitoring helpers
def log_memory(logger=None):
    """Log current memory usage."""
    gc.collect()
    free = gc.mem_free()
    alloc = gc.mem_alloc()
    total = free + alloc

    if logger:
        logger.debug("Memory: %d/%d bytes free (%.1f%%)",
                     free, total, (free / total) * 100)
    else:
        print(f"Memory: {free}/{total} bytes free ({(free/total)*100:.1f}%)")


def log_memory_if_low(threshold=10000, logger=None):
    """Log memory warning if free memory is below threshold."""
    gc.collect()
    free = gc.mem_free()

    if free < threshold:
        if logger:
            logger.warning("Low memory: %d bytes free", free)
        else:
            print(f"WARNING: Low memory: {free} bytes free")
        return True
    return False


# Timing helper
class Timer:
    """Simple timing context manager for performance logging."""

    def __init__(self, name, logger=None):
        """
        Initialize timer.

        Args:
            name: Operation name
            logger: Logger instance (uses print if None)
        """
        self.name = name
        self.logger = logger
        self.start_time = None

    def __enter__(self):
        self.start_time = time.ticks_ms()
        return self

    def __exit__(self, *args):
        elapsed = time.ticks_diff(time.ticks_ms(), self.start_time)
        message = f"{self.name} took {elapsed}ms"

        if self.logger:
            self.logger.debug(message)
        else:
            print(message)


# Decorators
def log_calls(logger_name):
    """
    Decorator to log function calls.

    Usage:
        @log_calls('MyModule')
        def my_function():
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            log = get_logger(logger_name)
            log.debug("Calling %s", func.__name__)
            try:
                result = func(*args, **kwargs)
                log.debug("%s completed", func.__name__)
                return result
            except Exception as e:
                log.error("%s failed: %s", func.__name__, e)
                raise
        return wrapper
    return decorator


def timed(logger_name):
    """
    Decorator to time function execution.

    Usage:
        @timed('MyModule')
        def my_function():
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            log = get_logger(logger_name)
            start = time.ticks_ms()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed = time.ticks_diff(time.ticks_ms(), start)
                log.debug("%s took %dms", func.__name__, elapsed)
        return wrapper
    return decorator


# Test when run directly
if __name__ == '__main__':
    print("Logger Test")
    print("=" * 40)

    # Create logger
    log = get_logger('Test')

    # Test different levels
    set_level(DEBUG)

    log.debug("Debug message")
    log.info("Info message")
    log.warning("Warning message")
    log.error("Error message")
    log.critical("Critical message")

    # Test formatting
    log.info("Formatted: %s = %d", "value", 42)

    # Test exception logging
    try:
        raise ValueError("Test error")
    except Exception as e:
        log.exception("Caught exception", e)

    # Test memory logging
    log_memory(log)

    # Test timer
    with Timer("Test operation", log):
        time.sleep(0.1)

    # Test file logging
    print("\nEnabling file logging...")
    enable_file_logging('test.log')
    log.info("This goes to file too")
    disable_file_logging()

    print("\nLogger test complete!")
