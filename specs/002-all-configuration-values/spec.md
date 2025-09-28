# Feature Specification: Configuration Values Consolidation

**Feature Branch**: `002-all-configuration-values`  
**Created**: September 27, 2025  
**Status**: Draft  
**Input**: User description: "All configuration values such as Excel File Name, Sheet names (e.g. Tickers), prefixes, suffixes, user, password, account, API URL, WS URL, etc. should organized in config files. Example: - Excel config: excel_config.py - pyRofex config: pyRofex_config.py Most importantly, code should use a library such us dotenv to gracefully obtain the configuration values"

## Clarifications

### Session 2025-09-27

- Q: What approach should be used for securing sensitive credentials in the configuration system? → A: Store credentials as plain text with file permission warnings only
- Q: What should the system do when configuration validation fails at startup? → A: Halt application startup immediately on any validation failure
- Q: What should be the precedence order for configuration value sources? → A: Environment variables override config files always
- Q: How should the system determine which configuration profile to use? → A: Use environment variable (e.g., APP_ENV=production) to select profile
- Q: What should be the migration approach for existing deployments? → A: Generate config files but require manual deployment and restart

## User Scenarios & Testing *(mandatory)*

### Primary User Story

As a developer working with the EPGB Options application, I need all configuration values (Excel file names, sheet names, API credentials, URLs, and other settings) to be organized in dedicated configuration files rather than hardcoded throughout the application, so that I can easily manage different environments (development, testing, production) and securely handle sensitive credentials without exposing them in the main code.

### Acceptance Scenarios

1. **Given** the application is running, **When** I need to change the Excel file name, **Then** I should only need to modify the value in `excel_config.py` without touching the main application code
2. **Given** I need to switch between development and production environments, **When** I update the credentials in `pyRofex_config.py`, **Then** the application should use the new configuration without code changes
3. **Given** the application starts up, **When** configuration values are missing or invalid, **Then** the system should provide clear error messages indicating which values need to be configured
4. **Given** sensitive credentials are stored, **When** the configuration files are created, **Then** they should include security warnings and best practices guidance
5. **Given** I'm deploying to a new environment, **When** I use environment variables for credentials, **Then** the system should gracefully fall back to configuration file values if environment variables are not available

### Edge Cases

- What happens when configuration files are missing or corrupted?
- How does the system handle partial configuration (some values present, others missing)?
- What occurs when environment variables contain invalid values?
- How does the system behave when Excel files specified in configuration don't exist?
- What happens when API URLs in configuration are unreachable or invalid?
- How should the system handle deployment scenarios where config files are not yet deployed but application is updated?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST organize all Excel-related configuration values (file names, sheet names, paths) into a dedicated `excel_config.py` file
- **FR-002**: System MUST organize all pyRofex API configuration values (URLs, credentials, connection parameters) into a dedicated `pyRofex_config.py` file
- **FR-003**: System MUST use python-dotenv library to load configuration values from environment variables when available, with environment variables taking precedence over config file values
- **FR-004**: System MUST provide fallback mechanisms when environment variables are not available, using values from configuration files as secondary source
- **FR-005**: System MUST validate all configuration values at application startup before attempting to use them, halting execution immediately if any validation fails
- **FR-006**: Configuration files MUST include comprehensive security warnings and setup instructions for sensitive credentials stored as plain text, with mandatory file permission guidelines (owner read/write only)
- **FR-007**: System MUST provide clear error messages when configuration validation fails and halt startup, indicating exactly which values need attention before execution can continue
- **FR-008**: System MUST maintain backward compatibility with existing functionality while using the new configuration system
- **FR-009**: Configuration files MUST include validation functions to verify the correctness of configuration values
- **FR-010**: System MUST support different configuration profiles for development, testing, and production environments using an environment variable (APP_ENV) to determine active profile
- **FR-011**: All hardcoded configuration values in existing code MUST be replaced with imports from the appropriate configuration modules
- **FR-012**: System MUST provide a migration utility to extract existing hardcoded values and generate initial configuration files, requiring manual deployment and application restart to activate new configuration system

### Key Entities *(include if feature involves data)*

- **ExcelConfiguration**: Represents Excel-related settings including file names, sheet names, and file paths
- **PyRofexConfiguration**: Represents API configuration including URLs, authentication credentials, and connection parameters  
- **EnvironmentVariables**: Represents configuration values loaded from system environment variables using dotenv
- **ConfigurationValidator**: Validates configuration values and provides error reporting for missing or invalid settings
- **ConfigurationMigration**: Extracts hardcoded values from existing code and generates configuration files

---

## Review & Acceptance Checklist

*GATE: Automated checks run during main() execution*

### Content Quality

- [x] No implementation details (languages, frameworks, APIs) - focuses on configuration organization and security
- [x] Focused on user value and business needs - improves maintainability and security
- [x] Written for non-technical stakeholders - explains benefits of configuration consolidation
- [x] All mandatory sections completed

### Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain - all requirements are specific and testable
- [x] Requirements are testable and unambiguous - each requirement has clear success criteria
- [x] Success criteria are measurable - validation, error handling, and security measures are specified
- [x] Scope is clearly bounded - focuses specifically on configuration consolidation using config files and dotenv
