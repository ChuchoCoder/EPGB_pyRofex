"""
Validation utilities for EPGB Options.

This module provides data validation functions for market data,
symbols, and other application data.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
from ..utils.logging import get_logger

logger = get_logger(__name__)


def validate_symbol(symbol: str) -> bool:
    """
    Validate a financial instrument symbol.
    
    Args:
        symbol: Symbol to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not symbol or not isinstance(symbol, str):
        return False
        
    # Basic validation - symbol should not be empty after stripping
    symbol = symbol.strip()
    if not symbol:
        return False
        
    # Additional validation rules can be added here
    return True


def validate_market_data(data: Dict[str, Any]) -> bool:
    """
    Validate market data structure.
    
    Args:
        data: Market data dictionary
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not isinstance(data, dict):
        logger.warning("Market data must be a dictionary")
        return False
    
    # Check for required fields
    required_fields = ['instrumentId']
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        logger.warning(f"Missing required fields: {missing_fields}")
        return False
    
    # Validate symbol
    symbol = data.get('instrumentId', {}).get('symbol')
    if not validate_symbol(symbol):
        logger.warning(f"Invalid symbol: {symbol}")
        return False
    
    # Validate numeric fields if present
    numeric_fields = ['last', 'bid', 'ask', 'volume']
    for field in numeric_fields:
        if field in data:
            try:
                float(data[field])
            except (ValueError, TypeError):
                logger.warning(f"Invalid numeric value for {field}: {data[field]}")
                return False
    
    return True


def validate_pandas_dataframe(df: pd.DataFrame, required_columns: List[str] = None) -> bool:
    """
    Validate pandas DataFrame structure.
    
    Args:
        df: DataFrame to validate
        required_columns: List of required column names
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not isinstance(df, pd.DataFrame):
        logger.warning("Input is not a pandas DataFrame")
        return False
    
    if df.empty:
        logger.info("DataFrame is empty")
        return True  # Empty is valid
    
    if required_columns:
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.warning(f"Missing required columns: {missing_columns}")
            return False
    
    return True


def validate_excel_range_data(data: Any, allow_none: bool = True) -> bool:
    """
    Validate data retrieved from Excel ranges.
    
    Args:
        data: Data from Excel range
        allow_none: Whether None values are allowed
        
    Returns:
        bool: True if valid, False otherwise
    """
    if data is None:
        return allow_none
    
    if isinstance(data, list):
        # For lists, check each element
        for item in data:
            if item is None and not allow_none:
                return False
    
    return True


def validate_configuration_values(config_dict: Dict[str, Any]) -> List[str]:
    """
    Validate configuration values.
    
    Args:
        config_dict: Configuration dictionary to validate
        
    Returns:
        List[str]: List of validation error messages (empty if valid)
    """
    errors = []
    
    if not isinstance(config_dict, dict):
        errors.append("Configuration must be a dictionary")
        return errors
    
    # Check for empty values
    for key, value in config_dict.items():
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(f"Configuration value '{key}' is empty or None")
    
    return errors


def safe_float_conversion(value: Any, default: float = 0.0) -> float:
    """
    Safely convert a value to float.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        float: Converted value or default
    """
    if value is None:
        return default
    
    try:
        return float(value)
    except (ValueError, TypeError):
        logger.debug(f"Could not convert {value} to float, using default {default}")
        return default


def safe_int_conversion(value: Any, default: int = 0) -> int:
    """
    Safely convert a value to int.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        int: Converted value or default
    """
    if value is None:
        return default
    
    try:
        return int(float(value))  # Convert through float to handle strings like "123.0"
    except (ValueError, TypeError):
        logger.debug(f"Could not convert {value} to int, using default {default}")
        return default