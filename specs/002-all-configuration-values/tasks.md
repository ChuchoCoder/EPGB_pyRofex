# Tasks: Configuration Values Consolidation

**Input**: Design documents from `/specs/002-all-configuration-values/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Tech stack: Python 3.x, python-dotenv, xlwings, pyRofex, pandas
   → Structure: Single project with root-level configuration files
2. Load design documents:
   → data-model.md: ExcelConfiguration, PyRofexConfiguration, ConfigurationValidator, ConfigurationMigration
   → contracts/: Excel config module, pyRofex config module, validation contracts
   → quickstart.md: 8 validation steps from dependency install to rollback
3. Generate tasks by constitutional alignment:
   → Setup: Dependencies, migration enhancement
   → Config Modules: Excel config, pyRofex config (parallel creation)
   → Integration: Application refactoring, validation integration
   → Operational: Quickstart validation scenarios (no unit tests per Constitution V)
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Operational validation over formal testing
5. Number tasks sequentially (T001, T002...)
6. Focus on configuration transparency (Constitution IV)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Paths assume single project structure at repository root
- No unit test tasks per Constitution Principle V

## Phase 3.1: Setup and Dependencies
- [x] T001 Install python-dotenv dependency via pip
- [x] T002 [P] Create .env.example template with all configuration variables
- [x] T003 [P] Create .gitignore patterns for credential protection

## Phase 3.2: Migration Utility Enhancement
- [x] T004 Enhance create_configs.py with dotenv integration support
- [x] T005 Add environment variable template generation to create_configs.py
- [x] T006 Add validation feedback to create_configs.py migration process

## Phase 3.3: Configuration Modules (Core Implementation)
- [x] T007 [P] Create excel_config.py with dotenv integration and validation
- [x] T008 [P] Create pyRofex_config.py with dotenv integration and validation
- [x] T009 [P] Add security warnings and file permission instructions to config files

## Phase 3.4: Application Integration
- [x] T010 Refactor main_HM.py to import and use excel_config module
- [x] T011 Refactor main_HM.py to import and use pyRofex_config module  
- [x] T012 Refactor Options_Helper_HM.py to import and use excel_config module
- [x] T013 Add configuration validation calls to main_HM.py startup sequence

## Phase 3.5: Operational Validation (Constitutional Alignment)
- [x] T014 [P] Validate configuration loading and environment variable precedence
- [x] T015 [P] Validate halt-on-failure behavior for invalid configuration
- [x] T016 [P] Validate profile switching via APP_ENV environment variable
- [x] T017 [P] Validate Excel file access through configuration system
- [x] T018 [P] Validate pyRofex API initialization through configuration system

## Dependencies
- T001 (python-dotenv) blocks T007-T008 (config modules need dotenv)
- T004-T006 (migration utility) should complete before T007-T008 (config generation)
- T007-T008 (config modules) block T010-T013 (application integration)
- T013 (validation integration) blocks T014-T018 (operational validation)

## Parallel Execution Examples
```bash
# Phase 3.1 Setup (can run together):
Task: "Create .env.example template with all configuration variables"
Task: "Create .gitignore patterns for credential protection"

# Phase 3.3 Configuration Modules (can run together):
Task: "Create excel_config.py with dotenv integration and validation"  
Task: "Create pyRofex_config.py with dotenv integration and validation"
Task: "Add security warnings and file permission instructions to config files"

# Phase 3.5 Operational Validation (can run together):
Task: "Validate configuration loading and environment variable precedence"
Task: "Validate halt-on-failure behavior for invalid configuration"
Task: "Validate profile switching via APP_ENV environment variable"
Task: "Validate Excel file access through configuration system"
Task: "Validate pyRofex API initialization through configuration system"
```

## Task Specifications

### T001: Install python-dotenv dependency
**File**: `requirements.txt` (if exists) or direct pip install
**Description**: Add python-dotenv to project dependencies
**Command**: `pip install python-dotenv`
**Validation**: `python -c "from dotenv import load_dotenv; print('Success')"`

### T002: Create .env.example template
**File**: `.env.example`
**Description**: Create environment variable template with all configuration options
**Content**: Include EXCEL_*, PYROFEX_*, APP_ENV variables with example values
**Security**: Use placeholder values, not real credentials

### T003: Create .gitignore patterns
**File**: `.gitignore`
**Description**: Add patterns to protect credentials from version control
**Patterns**: `.env`, `*_config.py` (optional), credential-containing files

### T004: Enhance create_configs.py - dotenv integration
**File**: `create_configs.py`
**Description**: Add python-dotenv import and load_dotenv() calls to migration utility
**Enhancement**: Support environment variable overrides during config generation

### T005: Environment variable template generation
**File**: `create_configs.py`
**Description**: Generate .env.example file as part of migration process
**Template**: Include all configurable values with REPLACE_WITH_ placeholders

### T006: Validation feedback in migration
**File**: `create_configs.py`
**Description**: Add configuration validation calls after file generation
**Feedback**: Report validation status and setup requirements to user

### T007: Create excel_config.py
**File**: `excel_config.py`
**Description**: Excel configuration module with dotenv integration
**Interface**: EXCEL_FILE, EXCEL_SHEET_PRICES, EXCEL_SHEET_TICKERS, EXCEL_PATH constants
**Validation**: validate_excel_config() function with file extension and path checks
**Environment**: Support EXCEL_* environment variable overrides

### T008: Create pyRofex_config.py  
**File**: `pyRofex_config.py`
**Description**: pyRofex configuration module with dotenv integration
**Interface**: API_URL, WS_URL, ENVIRONMENT, USER, PASSWORD, ACCOUNT constants
**Validation**: validate_pyRofex_config() function with protocol and credential checks
**Environment**: Support PYROFEX_* environment variable overrides
**Security**: Include comprehensive security warnings and file permission instructions

### T009: Security warnings in config files
**Files**: `excel_config.py`, `pyRofex_config.py`
**Description**: Add security documentation and file permission instructions
**Windows**: icacls commands for file permission restrictions
**Content**: Credential protection best practices, .gitignore guidance

### T010: Refactor main_HM.py - Excel configuration
**File**: `main_HM.py`
**Description**: Replace hardcoded Excel file and sheet names with excel_config imports
**Changes**: 
  - `import excel_config`
  - Replace `'EPGB OC-DI - Python.xlsb'` with `excel_config.EXCEL_FILE`
  - Replace `'HomeBroker'` with `excel_config.EXCEL_SHEET_PRICES`
  - Replace `'Tickers'` with `excel_config.EXCEL_SHEET_TICKERS`

### T011: Refactor main_HM.py - pyRofex configuration
**File**: `main_HM.py`
**Description**: Replace hardcoded pyRofex settings with pyRofex_config imports
**Changes**:
  - `import pyRofex_config`
  - Replace API URL with `pyRofex_config.API_URL`
  - Replace WebSocket URL with `pyRofex_config.WS_URL`
  - Replace credentials with `pyRofex_config.USER`, `PASSWORD`, `ACCOUNT`
  - Replace environment with `getattr(pyRofex.Environment, pyRofex_config.ENVIRONMENT)`

### T012: Refactor Options_Helper_HM.py
**File**: `Options_Helper_HM.py`  
**Description**: Replace hardcoded Excel references with excel_config imports
**Changes**:
  - `import excel_config`
  - Replace `'EPGB OC-DI - Python.xlsb'` with `excel_config.EXCEL_FILE`
  - Replace `'Tickers'` with `excel_config.EXCEL_SHEET_TICKERS`

### T013: Add configuration validation to startup
**File**: `main_HM.py`
**Description**: Add configuration validation calls at application startup
**Implementation**:
  - Call `excel_config.validate_excel_config()` before Excel operations
  - Call `pyRofex_config.validate_pyRofex_config()` before API operations
  - Exit with clear error messages if validation fails
  - Implement halt-on-failure behavior per clarifications

### T014: Validate configuration loading
**Description**: Operational validation of dotenv loading and configuration access
**Cross-reference**: Quickstart Step 4 (Environment Variables) and Step 5 (Configuration Validation Test)
**Test Cases**:
  - Configuration modules import successfully
  - Environment variables override config file values
  - Missing .env file doesn't break configuration loading
  - All configuration constants are accessible

### T015: Validate halt-on-failure behavior
**Description**: Operational validation of validation error handling
**Cross-reference**: Quickstart Step 5 error scenarios and Step 6 startup validation
**Test Cases**:
  - Invalid EXCEL_FILE extension causes startup halt
  - Invalid API URLs cause startup halt
  - Placeholder credentials cause startup halt with clear messages
  - Validation passes with valid configuration

### T016: Validate profile switching
**Description**: Operational validation of APP_ENV profile management
**Cross-reference**: Quickstart Step 4 (.env file setup with APP_ENV=development)
**Test Cases**:
  - APP_ENV=development uses appropriate defaults
  - APP_ENV=production uses appropriate defaults
  - Missing APP_ENV defaults to development profile
  - Profile-specific environment variables work correctly

### T017: Validate Excel integration
**Description**: Operational validation of Excel file access through configuration
**Cross-reference**: Quickstart Step 6 Excel initialization sequence
**Test Cases**:
  - Excel file opens using excel_config.EXCEL_FILE
  - Sheet access using excel_config.EXCEL_SHEET_PRICES and EXCEL_SHEET_TICKERS
  - Path resolution using excel_config.EXCEL_PATH
  - Environment variable overrides work for Excel settings

### T018: Validate pyRofex integration
**Description**: Operational validation of pyRofex API through configuration
**Cross-reference**: Quickstart Step 6 pyRofex environment and authentication
**Test Cases**:
  - API environment parameters set using pyRofex_config values
  - Authentication works with pyRofex_config credentials
  - Environment variable overrides work for API settings
  - Connection parameters (reconnection attempts, delays) applied correctly

## Constitutional Alignment Notes
- **No Unit Tests**: Per Constitution Principle V, no formal unit testing tasks included
- **Operational Validation**: Focus on functional validation through quickstart scenarios
- **Configuration Transparency**: Primary goal per Constitution Principle IV
- **Simplicity First**: Single project structure, minimal complexity per Constitution Principle I
- **Excel Integration**: Maintains xlwings compatibility per Constitution Principle II

## Success Criteria
- All hardcoded configuration values moved to dedicated modules
- Environment variable precedence working correctly
- Configuration validation provides clear error messages
- Application startup halts immediately on configuration errors
- Excel and pyRofex operations work through configuration system
- Security warnings and file permissions properly documented
- Migration utility successfully extracts and generates configuration files

## Notes
- Prefer operational validation over formal testing per constitutional requirements
- Each task is specific enough for LLM completion without additional context
- Parallel tasks operate on different files to avoid conflicts
- Dependencies ensure proper build order without formal testing framework
- Focus on configuration transparency and operational reliability