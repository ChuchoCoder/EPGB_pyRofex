"""
Excel Configuration Module

This module contains all Excel-related configuration values.
Environment variables take precedence over these default values.

SECURITY WARNING: This file may contain sensitive information.
Ensure proper file permissions are set (owner read/write only).

Windows: icacls excel_config.py /grant:r %USERNAME%:F /inheritance:r
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Robust .env loading: try project root, then data/.env fallback
_ROOT = Path(__file__).resolve().parents[3]
_loaded = load_dotenv()
if not _loaded:
    for candidate in (_ROOT / '.env', _ROOT / 'data' / '.env'):
        if candidate.exists():
            load_dotenv(dotenv_path=candidate)
            break

# Excel Configuration - Environment variables override these defaults
EXCEL_FILE = os.getenv('EXCEL_FILE', 'EPGB OC-DI - Python.xlsb')
EXCEL_PATH = os.getenv('EXCEL_PATH', './data/')
SHEET_HOMEBROKER = os.getenv('SHEET_HOMEBROKER', 'HomeBroker')
SHEET_TICKERS = os.getenv('SHEET_TICKERS', 'Tickers')


def validate_excel_config():
    """
    Validate Excel configuration values.
    Returns list of errors, empty list if all valid.
    """
    errors = []
    
    # Check file extension
    if not EXCEL_FILE.lower().endswith(('.xlsx', '.xlsb', '.xlsm')):
        errors.append(f"Invalid Excel file extension: {EXCEL_FILE}. Expected .xlsx, .xlsb, or .xlsm")
    
    # Check if file exists
    excel_file_path = os.path.join(EXCEL_PATH, EXCEL_FILE)
    if not os.path.exists(excel_file_path):
        errors.append(f"Excel file not found: {excel_file_path}")
    
    # Check sheet names are not empty
    if not SHEET_HOMEBROKER.strip():
        errors.append("SHEET_HOMEBROKER cannot be empty")
        
    if not SHEET_TICKERS.strip():
        errors.append("SHEET_TICKERS cannot be empty")
    
    return errors


if __name__ == "__main__":
    # Test configuration when run directly
    errors = validate_excel_config()
    if errors:
        print("❌ Excel configuration errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ Excel configuration is valid")
