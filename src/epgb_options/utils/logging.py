"""
Logging utilities for EPGB Options.

This module provides centralized logging configuration and utilities.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logging(level=logging.INFO, log_file=None):
    """
    Set up logging configuration.
    
    Args:
        level: Logging level (default: INFO)
        log_file: Optional log file path
    """
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        # Create log directory if it doesn't exist
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name):
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        logging.Logger: Configured logger
    """
    return logging.getLogger(name)


def log_validation_message(category, message, success=None):
    """
    Log a validation message with consistent formatting.
    
    Args:
        category: Category of validation
        message: Validation message
        success: True if successful, False if failed, None for info
    """
    logger = get_logger("validation")
    
    if success is True:
        logger.info(f"✅ {category}: {message}")
    elif success is False:
        logger.error(f"❌ {category}: {message}")
    else:
        logger.info(f"ℹ️ {category}: {message}")


def log_connection_event(event_type, details=""):
    """
    Log connection-related events.
    
    Args:
        event_type: Type of connection event
        details: Additional details
    """
    logger = get_logger("connection")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if details:
        logger.info(f"[{timestamp}] {event_type}: {details}")
    else:
        logger.info(f"[{timestamp}] {event_type}")


def log_market_data_event(symbol, event_type, data=None):
    """
    Log market data events.
    
    Args:
        symbol: Financial instrument symbol
        event_type: Type of market data event  
        data: Optional market data
    """
    logger = get_logger("market_data")
    
    if data:
        logger.debug(f"{symbol} - {event_type}: {data}")
    else:
        logger.info(f"{symbol} - {event_type}")