"""
Utilidades auxiliares generales para EPGB Options.

Este módulo provee funciones de utilidad general usadas en toda la aplicación.
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
        logger.debug(f"No se pudo convertir {value} a float, usando valor por defecto {default}")
        return default


def transform_symbol_for_pyrofex(raw_symbol: str) -> str:
    """
    Transform symbols for pyRofex compatibility.
    
    Rules based on actual pyRofex API symbols (instruments_cache.json analysis):
    - Add "MERV - XMEV - " prefix ONLY to MERV market securities (stocks, bonds, etc.)
    - Do NOT add prefix to: options, futures (ROS/DLR/ORO/WTI/etc), most indices
    - Exception: I.MERVAL gets MERV prefix, other I.* indices don't
    - Replace " - spot" suffix with " - CI"
    - Add " - 24hs" as default suffix ONLY for MERV securities without suffix
    - Preserve existing suffixes (" - 24hs", " - 48hs", " - 72hs", " - CI", etc.)
    
    Args:
        raw_symbol: Raw symbol from Excel
        
    Returns:
        str: Transformed symbol for pyRofex
        
    Examples:
        MERV Securities (with prefix):
        - "YPFD" → "MERV - XMEV - YPFD - 24hs" (prefix + default suffix)
        - "YPFD - 24hs" → "MERV - XMEV - YPFD - 24hs" (prefix + preserved suffix)
        - "GGAL - spot" → "MERV - XMEV - GGAL - CI" (prefix + spot→CI conversion)
        - "I.MERVAL" → "MERV - XMEV - I.MERVAL" (special case: MERVAL index gets prefix)
        
        Non-MERV Securities (NO prefix):
        - "SOJ.ROS/MAY26 292 C" → "SOJ.ROS/MAY26 292 C" (option, no changes)
        - "DLR/FEB26" → "DLR/FEB26" (future, no changes)
        - "I.BTC" → "I.BTC" (index, no changes)
        - "GIR.ROS.P/DISPO" → "GIR.ROS.P/DISPO" (special market, no changes)
        - "PESOS - 3D" → "MERV - XMEV - PESOS - 3D" (caucion gets prefix, no default suffix)
    """
    if not raw_symbol or not isinstance(raw_symbol, str):
        return raw_symbol
    
    # Strip whitespace
    symbol = raw_symbol.strip()
    
    # Skip if already has MERV prefix
    if symbol.startswith("MERV - XMEV - "):
        return symbol
    
    # Replace " - spot" with " - CI" (before checking prefix logic)
    if symbol.endswith(" - spot"):
        symbol = symbol.replace(" - spot", " - CI")
    
    # Determine if this symbol needs MERV prefix
    needs_prefix = _should_add_merv_prefix(symbol)
    
    # If needs prefix, also check if needs default suffix
    if needs_prefix:
        needs_default_suffix = _should_add_default_suffix(symbol)
        if needs_default_suffix:
            symbol = f"{symbol} - 24hs"
        
        # Add MERV prefix
        return f"MERV - XMEV - {symbol}"
    else:
        # No prefix needed, return as-is
        return symbol


def _should_add_merv_prefix(symbol: str) -> bool:
    """
    Determine if a symbol should have the "MERV - XMEV - " prefix added.
    
    Based on analysis of instruments_cache.json:
    - 7093/7590 (93%) symbols have MERV prefix
    - 497/7590 (7%) symbols DON'T have MERV prefix
    
    Symbols WITHOUT MERV prefix:
    - Options (ROS): 295 símbolos (e.g., "SOJ.ROS/MAY26 292 C")
    - Futures (ROS): 52 símbolos (e.g., "MAI.ROS/MAR26")
    - Dollar futures/options: 62+22 símbolos (e.g., "DLR/FEB26", "DLR/OCT25 1520 C")
    - Indices (except MERVAL): 4 símbolos (e.g., "I.BTC", "I.SOJCONT")
    - International/Other markets: ~60 símbolos (e.g., "ORO/ENE26", "WTI/NOV25", ".CME/", ".BRA/")
    
    Special case: "I.MERVAL" DOES have MERV prefix in the API
    
    Args:
        symbol: Symbol to check (without MERV - XMEV prefix)
        
    Returns:
        bool: True if MERV prefix should be added
    """
    # Special case: I.MERVAL gets prefix
    if symbol == "I.MERVAL":
        return True
    
    # Check if it's an option (ends with " C" or " P" after a number)
    # Pattern: "XXX/MMM## NNN C" or "XXX/MMM## NNN P"
    import re
    if re.search(r'\s+\d+\s+[CP]$', symbol):
        return False
    
    # Check if it's a ROS market future/option (contains ".ROS/")
    if ".ROS/" in symbol:
        return False
    
    # Check if it's a DLR future/option (starts with "DLR/")
    if symbol.startswith("DLR/"):
        return False
    
    # Check if it's an index (starts with "I." but not I.MERVAL)
    if symbol.startswith("I."):
        return False
    
    # Check if it's other commodity/international futures
    # Patterns: ORO/, WTI/, YPFD/, etc. (ticker followed by /)
    if "/" in symbol and not any(x in symbol for x in [" - ", "PESOS"]):
        return False
    
    # Check for other international markets (.CME/, .BRA/, .MIN/, .CRN/, etc.)
    if re.search(r'\.(CME|BRA|MIN|CRN)/', symbol):
        return False
    
    # Check for DISPO market (e.g., "GIR.ROS.P/DISPO")
    if "/DISPO" in symbol or symbol.endswith("/DISPO"):
        return False
    
    # Default: MERV securities (stocks, bonds, cauciones, cedears, etc.) get prefix
    return True


def _should_add_default_suffix(symbol: str) -> bool:
    """
    Determine if a symbol should have the default " - 24hs" suffix added.
    
    A suffix should be added if:
    - The symbol doesn't already have a settlement suffix (" - 24hs", " - 48hs", " - CI", etc.)
    - The symbol is NOT a caucion (PESOS - XD format)
    - The symbol is NOT an option (ends with C or P)
    - The symbol is NOT a future (contains "/" - but this is only called for MERV symbols)
    - The symbol is NOT an index starting with I.
    
    Note: This function is only called for symbols that will get MERV prefix,
    so futures/options from other markets are already excluded.
    
    Args:
        symbol: Symbol to check (without MERV - XMEV prefix)
        
    Returns:
        bool: True if default suffix should be added
    """
    # Known settlement suffixes
    settlement_suffixes = [
        " - 24hs", " - 48hs", " - 72hs",
        " - CI", " - spot",  # CI/spot are equivalent
        " - T0", " - T1", " - T2",  # Settlement codes
    ]
    
    # Check if already has a settlement suffix
    for suffix in settlement_suffixes:
        if symbol.endswith(suffix):
            return False
    
    # Check if it's a CAUCION (format: "PESOS - XD" where X is 1-2 digits)
    if "PESOS" in symbol:
        parts = symbol.split(" - ")
        if len(parts) >= 2 and parts[-1].endswith("D") and parts[-1][:-1].isdigit():
            return False
    
    # Check if it's an option (ends with " C" or " P")
    import re
    if re.search(r'\s+\d+\s+[CP]$', symbol):
        return False
    
    # Check if it's an INDEX (starts with I.)
    # Note: I.MERVAL will reach here, but we don't add suffix to indices
    if symbol.startswith("I."):
        return False
    
    # Check if it's a future (contains "/" for expiration)
    # This handles edge cases like company futures that might get MERV prefix
    if "/" in symbol:
        return False
    
    # Check for month codes in futures (e.g., "DLR/ENE25", "GGAL/FEB25")
    # This is redundant with "/" check but kept for clarity
    month_pattern = r'(ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)\d{2}'
    if re.search(month_pattern, symbol):
        return False
    
    # Default: add suffix (for stocks, bonds, cedears, etc.)
    return True


def clean_symbol_for_display(symbol: str, is_option: bool = False) -> str:
    """
    Clean symbol for Excel display by removing "MERV - XMEV - " prefix.
    For options, also remove the " - 24hs" suffix.
    
    Args:
        symbol: Symbol with pyRofex format (e.g., "MERV - XMEV - GGAL - 24hs")
        is_option: Whether the symbol represents an option
        
    Returns:
        str: Cleaned symbol for display
        
    Examples:
        - "MERV - XMEV - GGAL - 24hs" → "GGAL - 24hs" (regular security)
        - "MERV - XMEV - GFGV38566O - 24hs" → "GFGV38566O" (option, no suffix)
        - "MERV - XMEV - PESOS - 3D" → "PESOS - 3D" (caucion)
        - "GGAL - 24hs" → "GGAL - 24hs" (unchanged if no prefix)
    """
    if not symbol or not isinstance(symbol, str):
        return symbol
    
    # Remove "MERV - XMEV - " prefix if present
    prefix = "MERV - XMEV - "
    result = symbol
    if symbol.startswith(prefix):
        result = symbol[len(prefix):]
    
    # For options, also remove " - 24hs" suffix
    if is_option and result.endswith(" - 24hs"):
        result = result[:-len(" - 24hs")]
    
    return result


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
        raise ValueError("El tamaño del lote debe ser positivo")
    
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