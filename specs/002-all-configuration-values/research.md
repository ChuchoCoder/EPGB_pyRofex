# Research: Configuration Values Consolidation

## Overview
Research findings for consolidating hardcoded configuration values into dedicated configuration files with python-dotenv integration.

## Python-dotenv Integration Patterns

**Decision**: Use python-dotenv with environment variable precedence over config files

**Rationale**: 
- Industry standard for Python configuration management
- Enables secure credential handling without storing in version control
- Supports multiple deployment environments (dev/test/prod)
- Maintains fallback to config files when env vars unavailable

**Implementation Pattern**:
```python
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Environment variable with config file fallback
API_URL = os.getenv('PYROFEX_API_URL', 'https://api.cocos.xoms.com.ar/')
```

**Alternatives Considered**:
- ConfigParser (.ini files): More complex syntax, less Python-native
- YAML/JSON configs: Requires additional parsing, less secure for credentials
- Environment variables only: No fallback mechanism for development

## Configuration File Security

**Decision**: Plain text credentials with file permission warnings

**Rationale**:
- Aligns with clarification Q1 answer
- Simpler implementation for utility script context
- File permissions provide adequate security for development use case
- Clear documentation guides users on protection measures

**Implementation**:
- Include security warnings in generated config files
- Provide file permission setup instructions
- Document .gitignore patterns for credential protection

**Alternatives Considered**:
- Encrypted config files: Adds complexity with key management overhead
- External secret management: Over-engineering for utility script scope

## Configuration Validation Strategy

**Decision**: Halt-on-failure validation at startup

**Rationale**:
- Aligns with clarification Q2 answer
- Prevents runtime failures with incomplete configuration
- Clear feedback mechanism for deployment issues
- Follows fail-fast principle for operational reliability

**Validation Approach**:
```python
def validate_config():
    errors = []
    if not API_URL.startswith('https://'):
        errors.append("API_URL must use HTTPS")
    if errors:
        print("Configuration validation failed:")
        for error in errors:
            print(f"  - {error}")
        exit(1)
```

## Environment Profile Management

**Decision**: APP_ENV environment variable for profile selection

**Rationale**:
- Aligns with clarification Q4 answer
- Standard environment variable naming convention
- Simple conditional logic for profile-specific values
- Compatible with deployment automation tools

**Profile Implementation**:
```python
APP_ENV = os.getenv('APP_ENV', 'development')

if APP_ENV == 'production':
    # Production-specific defaults
    ENVIRONMENT = 'LIVE'
else:
    # Development defaults
    ENVIRONMENT = 'TEST'
```

## Migration Strategy

**Decision**: Manual deployment with restart requirement

**Rationale**:
- Aligns with clarification Q5 answer
- Safest approach for production systems
- Clear cutover point for new configuration system
- No complex hot-reload mechanisms needed

**Migration Steps**:
1. Generate config files from existing hardcoded values
2. Update application code to use config imports
3. Deploy new code and config files together
4. Restart application to load new configuration system

## Excel Integration Compatibility

**Decision**: Maintain existing xlwings patterns

**Rationale**:
- Constitutional requirement for Excel live integration
- Configuration changes don't affect Excel access patterns
- File paths remain configurable through excel_config.py

**Configuration Mapping**:
- Excel file name → excel_config.EXCEL_FILE  
- Sheet names → excel_config.SHEET_HOMEBROKER, excel_config.SHEET_TICKERS
- File path → excel_config.EXCEL_PATH

## pyRofex API Configuration

**Decision**: Separate config module for API settings

**Rationale**:
- Clean separation between Excel and API configuration
- Enables independent configuration management
- Supports different security requirements (API credentials vs. file paths)

**Configuration Structure**:
- API URLs → pyRofex_config.API_URL, pyRofex_config.WS_URL
- Credentials → pyRofex_config.USER, pyRofex_config.PASSWORD, pyRofex_config.ACCOUNT
- Connection params → pyRofex_config.ENVIRONMENT, pyRofex_config.MAX_RECONNECTION_ATTEMPTS

## Implementation Dependencies

**Required Libraries**:
- python-dotenv: Environment variable loading (new dependency)
- os: Built-in module for environment access
- sys: Built-in module for exit() functionality

**No Changes Required**:
- xlwings: Existing Excel integration
- pyRofex: Existing API client
- pandas: Existing data processing

## Performance Considerations

**Configuration Loading**: One-time startup cost ~50ms
**Validation**: One-time startup cost ~10ms  
**Memory Impact**: Minimal - configuration values loaded once at import

**Optimization**: Import config modules only where needed to minimize startup overhead.