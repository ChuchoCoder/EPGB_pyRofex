"""
Configuration management module for EPGB Options.

This module provides centralized configuration management with 
environment variable support using python-dotenv.
"""

# Import all configuration variables and functions
try:
    from .excel_config import (
        EXCEL_FILE, EXCEL_PATH, SHEET_HOMEBROKER, SHEET_TICKERS,
        validate_excel_config
    )
    from .pyrofex_config import (
        ENVIRONMENT, API_URL, WS_URL, USER, PASSWORD, ACCOUNT,
        validate_pyRofex_config
    )
    
    __all__ = [
        # Excel configuration
        'EXCEL_FILE', 'EXCEL_PATH', 'SHEET_HOMEBROKER', 'SHEET_TICKERS',
        'validate_excel_config',
        
        # pyRofex configuration  
        'ENVIRONMENT', 'API_URL', 'WS_URL', 'USER', 'PASSWORD', 'ACCOUNT',
        'validate_pyRofex_config'
    ]
    
except ImportError as e:
    # Graceful fallback if config modules are not available
    print(f"Warning: Could not import configuration modules: {e}")
    __all__ = []