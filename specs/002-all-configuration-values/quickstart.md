# Quickstart: Configuration Values Consolidation

## Overview
Quick validation and setup guide for the configuration values consolidation feature. This guide validates that all configuration files are properly set up and the application can start successfully with the new configuration system.

## Prerequisites
- Python 3.x installed
- Existing EPGB Options application codebase
- Administrative access to modify configuration files

## Step 1: Install Dependencies

```bash
pip install python-dotenv
```

**Validation**: Verify dotenv installation
```python
python -c "from dotenv import load_dotenv; print('python-dotenv installed successfully')"
```

## Step 2: Run Configuration Migration

Execute the migration utility to generate configuration files:

```bash
python create_configs.py
```

**Expected Output**:
```
1️⃣ Extracting configuration values from main_HM.py...
✅ Excel configuration found: EPGB OC-DI - Python.xlsb
✅ pyRofex URLs found: https://api.cocos.xoms.com.ar/

2️⃣ Validating extracted values...
✅ All extracted values are valid

3️⃣ Generating configuration files...
✅ excel_config.py created successfully
✅ pyRofex_config.py created with placeholders

4️⃣ Configuration migration complete!
```

**Validation**: Check generated files exist
```bash
dir excel_config.py pyRofex_config.py
```

## Step 3: Configure Credentials

Open `pyRofex_config.py` and replace placeholder values:

```python
# Replace these placeholder values with real credentials:
USER = 'your_actual_username'        # Replace 'REPLACE_WITH_YOUR_USERNAME'
PASSWORD = 'your_actual_password'    # Replace 'REPLACE_WITH_YOUR_PASSWORD'  
ACCOUNT = 'your_actual_account'      # Replace 'REPLACE_WITH_YOUR_ACCOUNT'
```

**Security Setup** (Required):
```bash
# Windows - Restrict file permissions
icacls pyRofex_config.py /grant:r %USERNAME%:F /inheritance:r

# Alternative: Use environment variables (see Step 4)
```

**Validation**: Check credentials are not placeholders
```python
python -c "
import pyRofex_config
if 'REPLACE_WITH_' in pyRofex_config.USER.upper():
    print('❌ USER still contains placeholder')
else:
    print('✅ USER configured')
"
```

## Step 4: Environment Variables (Optional)

Create `.env` file for environment variable overrides:

```bash
# Copy template
copy .env.example .env

# Edit .env with your values
PYROFEX_USER=your_username_here
PYROFEX_PASSWORD=your_password_here
PYROFEX_ACCOUNT=your_account_here
APP_ENV=development
```

**Validation**: Test environment loading
```python
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print(f'Environment loaded: {os.getenv(\"PYROFEX_USER\", \"not found\")}')
"
```

## Step 5: Configuration Validation Test

Test configuration validation without running the full application:

```python
# Create validation test script: test_config.py
import excel_config
import pyRofex_config

print("Testing configuration validation...")

# Test Excel configuration
excel_errors = excel_config.validate_excel_config()
if excel_errors:
    print("❌ Excel configuration errors:")
    for error in excel_errors:
        print(f"  - {error}")
else:
    print("✅ Excel configuration valid")

# Test pyRofex configuration  
pyRofex_errors = pyRofex_config.validate_pyrofex_config()
if pyRofex_errors:
    print("❌ pyRofex configuration errors:")
    for error in pyRofex_errors:
        print(f"  - {error}")
else:
    print("✅ pyRofex configuration valid")

# Overall result
if not excel_errors and not pyRofex_errors:
    print("🎉 All configurations valid - ready for application startup!")
else:
    print("🛑 Fix configuration errors before running the application")
```

**Run validation**:
```bash
python test_config.py
```

**Expected Output**:
```
Testing configuration validation...
✅ Excel configuration valid
✅ pyRofex configuration valid
🎉 All configurations valid - ready for application startup!
```

## Step 6: Application Startup Test

Test the application starts with new configuration system:

```bash
python main_HM.py
```

**Expected Startup Sequence**:
```
📁 Initializing Excel connection...
✅ Excel file connected successfully
✅ Excel sheets ('HomeBroker' and 'Tickers') accessible

🔧 Configuring pyRofex environment parameters...
✅ Environment parameters configured successfully

🔐 Validating credentials...
✅ Credentials validated

OK: STARTING AUTHENTICATION AND CONFIGURATION
```

**Validation Success Criteria**:
- [ ] No "Configuration validation failed" messages
- [ ] No "REPLACE_WITH_" placeholder errors
- [ ] Excel file opens successfully using config values
- [ ] pyRofex environment parameters set correctly
- [ ] Authentication proceeds without configuration errors

## Step 7: Profile Testing (Optional)

Test different configuration profiles:

**Development Profile**:
```bash
set APP_ENV=development
python main_HM.py
```
Expected: Uses TEST environment settings

**Production Profile**:
```bash  
set APP_ENV=production
python main_HM.py
```
Expected: Uses LIVE environment settings

## Step 8: Environment Variable Override Test

Test environment variable precedence:

```bash
# Set environment override
set EXCEL_FILE=Test-File.xlsb
python -c "
import excel_config
print(f'Excel file from config: {excel_config.EXCEL_FILE}')
# Should show 'Test-File.xlsb' instead of default
"
```

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'dotenv'`
**Solution**: Install python-dotenv: `pip install python-dotenv`

**Issue**: `Configuration validation failed: USER contains placeholder value`  
**Solution**: Edit `pyRofex_config.py` and replace `REPLACE_WITH_YOUR_USERNAME` with actual username

**Issue**: `FileNotFoundError: [Errno 2] No such file or directory: 'EPGB OC-DI - Python.xlsb'`
**Solution**: Verify Excel file exists in directory specified by `excel_config.EXCEL_PATH`

**Issue**: `API_URL must use HTTPS protocol`
**Solution**: Ensure API_URL starts with `https://` in configuration

**Issue**: `ENVIRONMENT must be 'LIVE' or 'TEST'`  
**Solution**: Set ENVIRONMENT to exactly 'LIVE' or 'TEST' (case-sensitive)

### Validation Commands

**Check all config files exist**:
```bash
python -c "
import os
files = ['excel_config.py', 'pyRofex_config.py']  
for f in files:
    print(f'{f}: {\"✅\" if os.path.exists(f) else \"❌\"} {\"exists\" if os.path.exists(f) else \"missing\"}')
"
```

**Check configuration loading**:
```bash
python -c "
try:
    import excel_config, pyRofex_config
    print('✅ Configuration modules loaded successfully')
    print(f'Excel file: {excel_config.EXCEL_FILE}')
    print(f'API URL: {pyRofex_config.API_URL}')
except Exception as e:
    print(f'❌ Configuration loading failed: {e}')
"
```

**Check environment variables**:
```bash
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
vars_to_check = ['PYROFEX_USER', 'PYROFEX_API_URL', 'APP_ENV']
for var in vars_to_check:
    value = os.getenv(var)
    print(f'{var}: {\"✅\" if value else \"❌\"} {value or \"not set\"}')
"
```

## Success Criteria

The quickstart is successful when:
- [ ] Migration utility runs without errors
- [ ] Configuration files generated successfully  
- [ ] All placeholder credentials replaced with actual values
- [ ] Configuration validation passes completely
- [ ] Application starts without configuration errors
- [ ] Excel file access works through configuration
- [ ] pyRofex API initialization works through configuration
- [ ] Environment variable overrides function correctly

## Next Steps

After successful quickstart:
1. Set up production environment variables for deployment
2. Configure file permissions on production servers
3. Set up .gitignore patterns to protect credentials
4. Document environment-specific configuration procedures
5. Consider automated configuration deployment procedures

## Rollback Procedure

If issues occur, rollback by:
1. Temporarily rename generated config files: `ren excel_config.py excel_config.py.bak`
2. Application will fail fast - indicating config system is properly integrated
3. Restore config files and fix identified issues
4. Re-run validation tests before attempting startup

**Note**: The configuration system uses fail-fast validation, so any issues will be caught at startup rather than during runtime operation.