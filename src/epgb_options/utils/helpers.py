"""
General helper utilities for EPGB Options.

This module provides general utility functions used across the application.
"""

from datetime import date, datetime
from typing import Any, Optional

import numpy as np
import pandas as pd

from ..utils.logging import get_logger

logger = get_logger(__name__)


def format_timestamp(timestamp: datetime = None, format_string: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format a timestamp to string.
    
    Args:
        timestamp: Timestamp to format (default: current time)
        format_string: Format string for datetime
        
    Returns:
        str: Formatted timestamp string
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    return timestamp.strftime(format_string)


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


def transform_symbol_for_pyrofex(raw_symbol: str) -> str:
    """
    Transform symbols for pyRofex compatibility.
    
    - Add "MERV - XMEV - " prefix to all symbols
    - Replace " - spot" suffix with " - CI"
    - Preserve other suffixes (" - 24hs", etc.)
    
    Args:
        raw_symbol: Raw symbol from Excel
        
    Returns:
        str: Transformed symbol for pyRofex
        
    Examples:
        - "YPFD - 24hs" → "MERV - XMEV - YPFD - 24hs"
        - "GGAL - spot" → "MERV - XMEV - GGAL - CI" 
        - "BBAR - CI" → "MERV - XMEV - BBAR - CI"
    """
    if not raw_symbol or not isinstance(raw_symbol, str):
        return raw_symbol
    
    # Strip whitespace
    symbol = raw_symbol.strip()
    
    # Skip if already has MERV prefix
    if symbol.startswith("MERV - XMEV - "):
        return symbol
    
    # Replace " - spot" with " - CI"
    if symbol.endswith(" - spot"):
        symbol = symbol.replace(" - spot", " - CI")
    
    # Add MERV prefix
    return f"MERV - XMEV - {symbol}"


def clean_symbol_for_display(symbol: str) -> str:
    """
    Clean symbol for Excel display by removing "MERV - XMEV - " prefix.
    
    Args:
        symbol: Symbol with pyRofex format (e.g., "MERV - XMEV - GGAL - 24hs")
        
    Returns:
        str: Cleaned symbol for display (e.g., "GGAL - 24hs")
        
    Examples:
        - "MERV - XMEV - GGAL - 24hs" → "GGAL - 24hs"
        - "MERV - XMEV - PESOS - 3D" → "PESOS - 3D"
        - "GGAL - 24hs" → "GGAL - 24hs" (unchanged if no prefix)
    """
    if not symbol or not isinstance(symbol, str):
        return symbol
    
    # Remove "MERV - XMEV - " prefix if present
    prefix = "MERV - XMEV - "
    if symbol.startswith(prefix):
        return symbol[len(prefix):]
    
    return symbol


def restore_symbol_prefix(display_symbol: str) -> str:
    """
    Restore "MERV - XMEV - " prefix to a cleaned display symbol.
    
    Args:
        display_symbol: Cleaned symbol from Excel (e.g., "GGAL - 24hs")
        
    Returns:
        str: Full symbol with prefix (e.g., "MERV - XMEV - GGAL - 24hs")
        
    Examples:
        - "GGAL - 24hs" → "MERV - XMEV - GGAL - 24hs"
        - "PESOS - 3D" → "MERV - XMEV - PESOS - 3D"
        - "MERV - XMEV - GGAL - 24hs" → "MERV - XMEV - GGAL - 24hs" (unchanged if already has prefix)
    """
    if not display_symbol or not isinstance(display_symbol, str):
        return display_symbol
    
    # Skip if already has prefix
    prefix = "MERV - XMEV - "
    if display_symbol.startswith(prefix):
        return display_symbol
    
    return f"{prefix}{display_symbol}"


def clean_dataframe_for_excel(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean DataFrame for Excel output.
    
    Args:
        df: DataFrame to clean
        
    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    if df.empty:
        return df
    
    # Create a copy to avoid modifying original
    cleaned_df = df.copy()
    
    # Replace inf values with NaN, then with 0
    cleaned_df = cleaned_df.replace([float('inf'), float('-inf')], pd.NA)
    cleaned_df = cleaned_df.fillna(0)
    
    # Round numeric columns to reasonable precision
    numeric_columns = cleaned_df.select_dtypes(include=['float64', 'float32']).columns
    for col in numeric_columns:
        cleaned_df[col] = cleaned_df[col].round(6)
    
    return cleaned_df


def get_excel_safe_value(value: Any) -> Any:
    """
    Get Excel-safe value (handle None, inf, etc.).
    
    Args:
        value: Value to make Excel-safe
        
    Returns:
        Any: Excel-safe value
    """
    if value is None:
        return 0
    
    if isinstance(value, (int, float)):
        if pd.isna(value) or np.isinf(value):
            return 0
        return value
    
    if isinstance(value, str):
        return value.strip()
    
    return value


def batch_list(items: list, batch_size: int) -> list:
    """
    Split a list into batches.
    
    Args:
        items: List to split
        batch_size: Size of each batch
        
    Returns:
        list: List of batches (sublists)
    """
    if batch_size <= 0:
        raise ValueError("Batch size must be positive")
    
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]


def safe_get_dict_value(dictionary: dict, key: str, default: Any = None) -> Any:
    """
    Safely get value from dictionary with nested key support.
    
    Args:
        dictionary: Dictionary to search
        key: Key to look for (supports dot notation for nested keys)
        default: Default value if key not found
        
    Returns:
        Any: Value from dictionary or default
        
    Example:
        safe_get_dict_value({"a": {"b": "value"}}, "a.b") returns "value"
    """
    if not isinstance(dictionary, dict):
        return default
    
    # Handle nested keys with dot notation
    if '.' in key:
        keys = key.split('.')
        current = dictionary
        
        for k in keys:
            if not isinstance(current, dict) or k not in current:
                return default
            current = current[k]
            
        return current
    else:
        return dictionary.get(key, default)