"""
Logging system for SI3LN Game
Centralized logging with different levels and error handling
"""
import logging
import sys
from pathlib import Path

# Create logs directory if it doesn't exist
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Logger instance
_logger = None


def setup_logging(level=logging.INFO, log_to_file=True):
    """
    Setup the logging system
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_to_file: Whether to log to a file
    """
    global _logger
    
    # Create logger
    _logger = logging.getLogger('SI3LN')
    _logger.setLevel(level)
    
    # Prevent duplicate handlers
    if _logger.handlers:
        return _logger
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    simple_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # Console handler (simple format)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(simple_formatter)
    _logger.addHandler(console_handler)
    
    # File handler (detailed format)
    if log_to_file:
        log_file = LOG_DIR / 'game.log'
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Log everything to file
        file_handler.setFormatter(detailed_formatter)
        _logger.addHandler(file_handler)
    
    return _logger


def get_logger():
    """
    Get the logger instance
    If not initialized, creates one with default settings
    """
    global _logger
    if _logger is None:
        setup_logging()
    return _logger


# Convenience functions for common log operations
def debug(message, *args, **kwargs):
    """Log a debug message"""
    get_logger().debug(message, *args, **kwargs)


def info(message, *args, **kwargs):
    """Log an info message"""
    get_logger().info(message, *args, **kwargs)


def warning(message, *args, **kwargs):
    """Log a warning message"""
    get_logger().warning(message, *args, **kwargs)


def error(message, *args, **kwargs):
    """Log an error message"""
    get_logger().error(message, *args, **kwargs)


def exception(message, *args, exc_info=True, **kwargs):
    """Log an exception with traceback"""
    get_logger().error(message, *args, exc_info=exc_info, **kwargs)

