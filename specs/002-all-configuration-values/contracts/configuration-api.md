# Configuration Module Contracts

## ExcelConfiguration Contract

### Module: excel_config.py

**Public Interface:**
```python
# Configuration Constants
EXCEL_FILE: str              # Excel workbook filename
SHEET_HOMEBROKER: str       # HomeBroker sheet name  
SHEET_TICKERS: str          # Tickers sheet name
EXCEL_PATH: str             # Directory path to Excel file

# Validation Function
def validate_excel_config() -> List[str]:
    """
    Validates Excel configuration values.
    
    Returns:
        List[str]: List of validation error messages. Empty list if valid.
    
    Validation Rules:
        - EXCEL_FILE must have valid Excel extension (.xlsb, .xlsx, .xls)
        - SHEET_HOMEBROKER must be non-empty string
        - SHEET_TICKERS must be non-empty string  
        - EXCEL_PATH must be valid directory path
    """
```

**Environment Variable Overrides:**
- `EXCEL_FILE` → overrides EXCEL_FILE
- `EXCEL_PATH` → overrides EXCEL_PATH
- `SHEET_HOMEBROKER` → overrides SHEET_HOMEBROKER  
- `SHEET_TICKERS` → overrides SHEET_TICKERS

**Usage Contract:**
```python
# Import configuration
import excel_config

# Access values (guaranteed to be loaded with env var precedence)
workbook_path = os.path.join(excel_config.EXCEL_PATH, excel_config.EXCEL_FILE)
wb = xw.Book(workbook_path)
homebroker_sheet = wb.sheets(excel_config.SHEET_HOMEBROKER)
tickers_sheet = wb.sheets(excel_config.SHEET_TICKERS)

# Validate before use
errors = excel_config.validate_excel_config()
if errors:
    for error in errors:
        print(f"Excel config error: {error}")
    exit(1)
```

## PyRofexConfiguration Contract

### Module: pyRofex_config.py

**Public Interface:**
```python
# API Configuration Constants
API_URL: str                      # pyRofex REST API endpoint
WS_URL: str                       # pyRofex WebSocket endpoint
ENVIRONMENT: str                  # 'LIVE' or 'TEST'

# Authentication Constants  
USER: str                         # Username (plain text)
PASSWORD: str                     # Password (plain text)
ACCOUNT: str                      # Account identifier

# Connection Parameters
MAX_RECONNECTION_ATTEMPTS: int    # Maximum reconnection attempts
RECONNECTION_DELAYS: List[int]    # Delay sequence for reconnections

# Validation Function
def validate_pyrofex_config() -> List[str]:
    """
    Validates pyRofex configuration values.
    
    Returns:
        List[str]: List of validation error messages. Empty list if valid.
        
    Validation Rules:
        - API_URL must use HTTPS protocol
        - WS_URL must use WSS protocol
        - ENVIRONMENT must be 'LIVE' or 'TEST' (case-sensitive)
        - USER, PASSWORD, ACCOUNT must not contain placeholder values
        - MAX_RECONNECTION_ATTEMPTS must be positive integer
        - RECONNECTION_DELAYS must be non-empty list of positive numbers
    """
```

**Environment Variable Overrides:**
- `PYROFEX_API_URL` → overrides API_URL
- `PYROFEX_WS_URL` → overrides WS_URL
- `PYROFEX_ENVIRONMENT` → overrides ENVIRONMENT
- `PYROFEX_USER` → overrides USER
- `PYROFEX_PASSWORD` → overrides PASSWORD
- `PYROFEX_ACCOUNT` → overrides ACCOUNT
- `APP_ENV` → influences default ENVIRONMENT value

**Usage Contract:**
```python
# Import configuration
import pyRofex_config

# Validate before use (REQUIRED - halt on failure)
errors = pyRofex_config.validate_pyrofex_config()
if errors:
    print("pyRofex configuration validation failed:")
    for error in errors:
        print(f"  - {error}")
    exit(1)

# Use configuration values
pyRofex._set_environment_parameter('url', pyRofex_config.API_URL, 
                                 getattr(pyRofex.Environment, pyRofex_config.ENVIRONMENT))
pyRofex._set_environment_parameter('ws', pyRofex_config.WS_URL,
                                 getattr(pyRofex.Environment, pyRofex_config.ENVIRONMENT))

# Authentication
pyRofex.initialize(user=pyRofex_config.USER,
                  password=pyRofex_config.PASSWORD, 
                  account=pyRofex_config.ACCOUNT)
```

## Environment Variable Integration Contract

### Module: Both config modules via python-dotenv

**Loading Contract:**
```python
from dotenv import load_dotenv
import os

# Load environment variables from .env file (if exists)
load_dotenv()

# Environment variable with fallback pattern
CONFIG_VALUE = os.getenv('ENV_VAR_NAME', default_from_config_file)
```

**Precedence Rules:**
1. Environment variables (highest priority)
2. Config file values (fallback)
3. No hardcoded defaults in application code

**Profile Selection Contract:**
```python
APP_ENV = os.getenv('APP_ENV', 'development')

# Profile-specific defaults
if APP_ENV == 'production':
    default_environment = 'LIVE'
else:
    default_environment = 'TEST'
    
ENVIRONMENT = os.getenv('PYROFEX_ENVIRONMENT', default_environment)
```

## Configuration Migration Contract

### Module: create_configs.py (enhanced)

**Public Interface:**
```python
def extract_hardcoded_values() -> Dict[str, Any]:
    """
    Extract configuration values from existing code files.
    
    Returns:
        Dict[str, Any]: Extracted configuration values
        
    Raises:
        FileNotFoundError: If source files not found
        ValueError: If required values cannot be extracted
    """

def generate_config_files(config_values: Dict[str, Any]) -> bool:
    """
    Generate configuration files from extracted values.
    
    Args:
        config_values: Configuration values to write
        
    Returns:
        bool: True if files generated successfully
        
    Safety:
        - Never overwrites existing files
        - Validates values before writing
        - Includes security warnings in generated files
    """

def main():
    """
    Main migration utility entry point.
    
    Process:
        1. Extract hardcoded values from existing code
        2. Validate extracted values
        3. Generate configuration files (if not exist)
        4. Provide setup instructions
        
    Exit codes:
        0: Success
        1: Extraction or validation failed
        2: File generation failed
    """
```

**Usage Contract:**
```bash
# Run migration utility
python create_configs.py

# Expected output files:
# - excel_config.py (if not exists)
# - pyRofex_config.py (if not exists)  
# - Setup instructions printed to console
```

## Validation Framework Contract

### Cross-Module Validation

**Startup Validation Pattern:**
```python
def validate_all_configurations():
    """
    Validate all configuration modules at application startup.
    
    Behavior:
        - Calls validation function for each config module
        - Collects all validation errors
        - If any errors found: prints clear messages and exits
        - If validation passes: returns silently
        
    Exit behavior:
        - exit(1) on any validation failure (halt startup)
        - No return on success (continues execution)
    """
    all_errors = []
    
    # Validate each configuration module
    all_errors.extend(excel_config.validate_excel_config())
    all_errors.extend(pyRofex_config.validate_pyrofex_config())
    
    if all_errors:
        print("❌ Configuration validation failed:")
        for error in all_errors:
            print(f"  - {error}")
        print("🛑 Fix configuration errors before running the application")
        exit(1)
```

**Integration Points:**
- Called by main_HM.py during startup (before any Excel/API operations)
- Called by create_configs.py to validate generated configurations
- Called by any module that imports configuration (fail-fast principle)

## File Generation Templates

### .env Template Contract
```bash
# Generated by create_configs.py migration utility
# Copy to .env and customize for your environment

# Excel Configuration
EXCEL_FILE=EPGB OC-DI - Python.xlsb
EXCEL_PATH=./

# pyRofex Configuration (⚠️  REPLACE PLACEHOLDER VALUES)
PYROFEX_API_URL=https://api.cocos.xoms.com.ar/
PYROFEX_WS_URL=wss://api.cocos.xoms.com.ar/
PYROFEX_ENVIRONMENT=LIVE
PYROFEX_USER=REPLACE_WITH_YOUR_USERNAME
PYROFEX_PASSWORD=REPLACE_WITH_YOUR_PASSWORD
PYROFEX_ACCOUNT=REPLACE_WITH_YOUR_ACCOUNT

# Environment Profile
APP_ENV=development
```

### Security Documentation Contract

**Included in Generated Files:**
- File permission setup instructions
- .gitignore patterns for credential protection
- Environment variable setup guidance
- Deployment security considerations
- Credential replacement warnings

**File Permission Instructions:**
```bash
# Windows
icacls pyRofex_config.py /grant:r %USERNAME%:F /inheritance:r

# Linux/Mac  
chmod 600 pyRofex_config.py
```