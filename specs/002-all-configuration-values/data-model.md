# Data Model: Configuration Values Consolidation

## Overview
Data model for configuration management system with separate modules for Excel and pyRofex API configuration, environment variable integration, and validation framework.

## Configuration Entities

### ExcelConfiguration
**Purpose**: Manages Excel file access and sheet configuration
**Module**: `excel_config.py`

**Attributes**:
- `EXCEL_FILE`: str - Name of Excel workbook file (e.g., "EPGB OC-DI - Python.xlsb")
- `SHEET_HOMEBROKER`: str - Name of HomeBroker data sheet (e.g., "HomeBroker")  
- `SHEET_TICKERS`: str - Name of Tickers configuration sheet (e.g., "Tickers")
- `EXCEL_PATH`: str - Directory path containing Excel file (e.g., "./")

**Validation Rules**:
- EXCEL_FILE must have valid Excel extension (.xlsb, .xlsx, .xls)
- SHEET_HOMEBROKER and SHEET_TICKERS must be non-empty strings
- EXCEL_PATH must be valid directory path
- Excel file at EXCEL_PATH/EXCEL_FILE should be accessible

**State Transitions**: N/A (static configuration)

**Relationships**: Used by main_HM.py and Options_Helper_HM.py for xlwings operations

### PyRofexConfiguration  
**Purpose**: Manages pyRofex API connection settings and credentials
**Module**: `pyRofex_config.py`

**Attributes**:
- `API_URL`: str - pyRofex REST API endpoint (e.g., "https://api.cocos.xoms.com.ar/")
- `WS_URL`: str - pyRofex WebSocket endpoint (e.g., "wss://api.cocos.xoms.com.ar/")
- `ENVIRONMENT`: str - Trading environment, must be "LIVE" or "TEST"  
- `USER`: str - Authentication username (plain text with security warnings)
- `PASSWORD`: str - Authentication password (plain text with security warnings)
- `ACCOUNT`: str - Account identifier for trading operations
- `MAX_RECONNECTION_ATTEMPTS`: int - Maximum WebSocket reconnection attempts (default: 10)
- `RECONNECTION_DELAYS`: list[int] - Delay sequence for reconnections (default: [1, 2, 4, 8, 15, 30])

**Validation Rules**:
- API_URL must use HTTPS protocol
- WS_URL must use WSS protocol  
- ENVIRONMENT must be exactly "LIVE" or "TEST" (case-sensitive)
- USER, PASSWORD, ACCOUNT must not contain placeholder values
- MAX_RECONNECTION_ATTEMPTS must be positive integer
- RECONNECTION_DELAYS must be non-empty list of positive numbers

**State Transitions**: N/A (static configuration)

**Relationships**: Used by main_HM.py for pyRofex API initialization

### EnvironmentVariables
**Purpose**: Environment variable integration using python-dotenv
**Module**: Both config modules via dotenv integration

**Attributes** (Environment Variable Names):
- `EXCEL_FILE`: Overrides excel_config.EXCEL_FILE
- `EXCEL_PATH`: Overrides excel_config.EXCEL_PATH
- `PYROFEX_API_URL`: Overrides pyRofex_config.API_URL
- `PYROFEX_WS_URL`: Overrides pyRofex_config.WS_URL  
- `PYROFEX_USER`: Overrides pyRofex_config.USER
- `PYROFEX_PASSWORD`: Overrides pyRofex_config.PASSWORD
- `PYROFEX_ACCOUNT`: Overrides pyRofex_config.ACCOUNT
- `PYROFEX_ENVIRONMENT`: Overrides pyRofex_config.ENVIRONMENT
- `APP_ENV`: Determines active configuration profile (development/production)

**Precedence Rule**: Environment variables ALWAYS override config file values

**State Transitions**: Loaded once at module import time

**Relationships**: Primary source for all configuration modules

### ConfigurationValidator
**Purpose**: Validates configuration values at application startup  
**Module**: Validation functions within each config module

**Methods**:
- `validate_excel_config()`: Returns list of Excel configuration errors
- `validate_pyrofex_config()`: Returns list of pyRofex configuration errors  
- `validate_all_configs()`: Validates all configuration, halts on any errors

**Validation Flow**:
1. Load environment variables via dotenv
2. Apply environment variable overrides to config values
3. Run validation functions for all config modules
4. If any errors found: print clear messages and exit(1)
5. If validation passes: continue application startup

**Error Handling**: Halt application startup immediately on validation failure

**Relationships**: Called by main_HM.py during initialization

### ConfigurationMigration
**Purpose**: Extracts hardcoded values and generates configuration files
**Module**: `create_configs.py` (enhanced existing utility)

**Attributes**:
- `source_file`: str - Path to file containing hardcoded values (main_HM.py)
- `excel_config_template`: str - Template for excel_config.py generation
- `pyrofex_config_template`: str - Template for pyRofex_config.py generation

**Methods**:
- `extract_hardcoded_values()`: Parse source files for configuration values
- `generate_excel_config()`: Create excel_config.py with extracted values
- `generate_pyrofex_config()`: Create pyRofex_config.py with placeholders
- `validate_generated_files()`: Verify generated configurations are valid

**Migration Process**:
1. Scan existing code files for hardcoded configuration patterns
2. Extract values into structured data
3. Generate configuration files using templates
4. Include security warnings and setup instructions
5. Provide deployment guidance for manual restart requirement

**Safety Features**:
- Never overwrites existing configuration files
- Validates extracted values before file generation
- Provides clear instructions for credential replacement

**Relationships**: Standalone utility, creates files consumed by other config modules

## Configuration Loading Flow

### Startup Sequence
1. **Import Phase**: Configuration modules loaded
2. **Environment Loading**: dotenv loads .env file if present
3. **Override Phase**: Environment variables override config file values
4. **Validation Phase**: All configuration validated, halt on errors
5. **Application Phase**: Validated configuration used by application

### Profile Management
- `APP_ENV=development`: Use TEST environment, development credentials
- `APP_ENV=production`: Use LIVE environment, production credentials  
- Default: development profile if APP_ENV not set

### Error States
- **Missing Config**: Configuration file not found → halt startup
- **Invalid Values**: Validation failure → halt startup with specific errors
- **Missing Credentials**: Placeholder values detected → halt with credential setup instructions

## File Permissions Security

### Configuration Files
- **excel_config.py**: Standard file permissions (contains file paths only)
- **pyRofex_config.py**: Restricted permissions (contains credentials)
- **.env**: Restricted permissions, added to .gitignore

### Security Documentation
- Include file permission setup instructions in generated configs
- Provide .gitignore patterns for credential protection
- Document environment variable setup for production deployments

## Backward Compatibility

### Import Changes
- **Before**: `wb = xw.Book('EPGB OC-DI - Python.xlsb')`
- **After**: `import excel_config; wb = xw.Book(excel_config.EXCEL_FILE)`

### API Initialization Changes  
- **Before**: `pyRofex._set_environment_parameter('url', 'https://api.cocos.xoms.com.ar/', pyRofex.Environment.LIVE)`
- **After**: `import pyRofex_config; pyRofex._set_environment_parameter('url', pyRofex_config.API_URL, getattr(pyRofex.Environment, pyRofex_config.ENVIRONMENT))`

### Functional Compatibility
- All existing Excel operations unchanged (xlwings patterns preserved)
- All existing API operations unchanged (pyRofex patterns preserved)
- Same error handling behavior (improved with validation)
- Same performance characteristics (minimal startup overhead)

## Configuration Templates

### .env.example Template
```
# Excel Configuration
EXCEL_FILE=EPGB OC-DI - Python.xlsb
EXCEL_PATH=./

# pyRofex Configuration
PYROFEX_API_URL=https://api.cocos.xoms.com.ar/
PYROFEX_WS_URL=wss://api.cocos.xoms.com.ar/
PYROFEX_ENVIRONMENT=LIVE
PYROFEX_USER=your_username_here
PYROFEX_PASSWORD=your_password_here  
PYROFEX_ACCOUNT=your_account_here

# Environment Profile
APP_ENV=development
```