"""
pyRofex API Configuration Module

This module contains all pyRofex API-related configuration values.
Environment variables take precedence over these default values.

⚠️  CRITICAL SECURITY WARNING ⚠️
=====================================
This file contains sensitive API credentials stored as PLAIN TEXT.

REQUIRED SECURITY MEASURES:
1. Set restrictive file permissions (owner read/write only):
   Windows: icacls pyRofex_config.py /grant:r %USERNAME%:F /inheritance:r
   
2. Ensure this file is NOT committed to version control
   (Check your .gitignore includes *.py config files if needed)
   
3. For production deployments, use environment variables instead:
   - Set PYROFEX_USER, PYROFEX_PASSWORD, PYROFEX_ACCOUNT in your environment
   - This file will automatically use environment variables when available
   
4. Regularly rotate credentials and monitor for unauthorized access

ALTERNATIVE: Use environment variables exclusively by setting all 
PYROFEX_* values in your .env file and leaving defaults as placeholders.
=====================================
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# pyRofex API Configuration - Environment variables override these defaults
ENVIRONMENT = os.getenv('PYROFEX_ENVIRONMENT', 'LIVE')
API_URL = os.getenv('PYROFEX_API_URL', 'https://api.cocos.xoms.com.ar/')
WS_URL = os.getenv('PYROFEX_WS_URL', 'wss://api.cocos.xoms.com.ar/')

# CREDENTIALS - Replace with actual values or use environment variables
USER = os.getenv('PYROFEX_USER', 'REPLACE_WITH_YOUR_USERNAME')
PASSWORD = os.getenv('PYROFEX_PASSWORD', 'REPLACE_WITH_YOUR_PASSWORD')
ACCOUNT = os.getenv('PYROFEX_ACCOUNT', 'REPLACE_WITH_YOUR_ACCOUNT')


def validate_pyRofex_config():
    """
    Validate pyRofex configuration values.
    Returns list of errors, empty list if all valid.
    """
    errors = []
    
    # Check URLs have proper protocol
    if not API_URL.startswith(('http://', 'https://')):
        errors.append(f"Invalid API_URL protocol: {API_URL}. Expected http:// or https://")
    
    if not WS_URL.startswith(('ws://', 'wss://')):
        errors.append(f"Invalid WS_URL protocol: {WS_URL}. Expected ws:// or wss://")
    
    # Check credentials are not placeholders
    placeholder_values = ['REPLACE_WITH_YOUR_USERNAME', 'REPLACE_WITH_YOUR_PASSWORD', 'REPLACE_WITH_YOUR_ACCOUNT']
    
    if USER in placeholder_values:
        errors.append("USER still contains placeholder value. Replace with actual username or set PYROFEX_USER environment variable")
    
    if PASSWORD in placeholder_values:
        errors.append("PASSWORD still contains placeholder value. Replace with actual password or set PYROFEX_PASSWORD environment variable")
        
    if ACCOUNT in placeholder_values:
        errors.append("ACCOUNT still contains placeholder value. Replace with actual account or set PYROFEX_ACCOUNT environment variable")
    
    # Check credentials are not empty
    if not USER.strip():
        errors.append("USER cannot be empty")
        
    if not PASSWORD.strip():
        errors.append("PASSWORD cannot be empty")
        
    if not ACCOUNT.strip():
        errors.append("ACCOUNT cannot be empty")
    
    # Check environment is valid
    valid_environments = ['LIVE', 'REMARKET', 'DEMO']
    if ENVIRONMENT not in valid_environments:
        errors.append(f"Invalid ENVIRONMENT: {ENVIRONMENT}. Expected one of: {', '.join(valid_environments)}")
    
    return errors


if __name__ == "__main__":
    # Test configuration when run directly
    errors = validate_pyRofex_config()
    if errors:
        print("❌ pyRofex configuration errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ pyRofex configuration is valid")
