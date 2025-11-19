"""
Centralized logging configuration for the application.
Provides file-based logging with daily rotation, similar to Django's logging.
"""
import logging
import os
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

# Create logs directory if it doesn't exist
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
LOG_DIR = BASE_DIR / "applog"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "logs.log"

# Define log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(log_level: str = "INFO"):
    """
    Configure application-wide logging with file rotation.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Get the root logger
    root_logger = logging.getLogger()
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Set log level
    level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    
    # File handler with daily rotation
    # when='midnight' rotates at midnight
    # interval=1 means every 1 day
    # backupCount=30 keeps 30 days of logs
    file_handler = TimedRotatingFileHandler(
        filename=LOG_FILE,
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    file_handler.suffix = "%Y-%m-%d"  # Append date to rotated files
    
    # Console handler (for development)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Log the initialization
    root_logger.info("="*80)
    root_logger.info("Logging system initialized")
    root_logger.info(f"Log file: {LOG_FILE}")
    root_logger.info(f"Log level: {log_level.upper()}")
    root_logger.info(f"Rotation: Daily at midnight (keeps 30 days)")
    root_logger.info("="*80)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Name of the logger (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
