# Quickstart: PyRofex Integration Testing

## Prerequisites Verification

1. **Dependencies Installed**
   ```bash
   pip install pyRofex xlwings pandas
   ```

2. **Excel File Available**
   - Verify `EPGB OC-DI - Python.xlsb` exists
   - Ensure Tickers sheet has symbol lists in appropriate columns
   - Confirm HomeBroker sheet exists for data output

3. **Credentials Available**
   - COCOS broker username
   - COCOS broker password  
   - Account identifier

## Manual Testing Steps

### Step 1: Environment Configuration
```python
import pyRofex

# Set COCOS broker environment
pyRofex._set_environment_parameter("url", "https://api.cocos.xoms.com.ar/", pyRofex.Environment.LIVE)
pyRofex._set_environment_parameter("ws", "wss://api.cocos.xoms.com.ar/", pyRofex.Environment.LIVE)
```

**Expected**: No errors, environment parameters set

### Step 2: Authentication Test
```python
# Initialize with credentials
pyRofex.initialize(user="your_username", password="your_password", account="your_account", environment=pyRofex.Environment.LIVE)
```

**Expected**: Successful authentication or clear error message
**On Failure**: Stop testing - manual intervention required per FR-003

### Step 3: Symbol Transformation Test
```python
import re

def transform_symbol(raw_symbol):
    # Skip if already has MERV prefix
    if raw_symbol.startswith("MERV - XMEV - "):
        return raw_symbol
    
    symbol = raw_symbol.strip()
    
    # Replace " - spot" with " - CI"
    if symbol.endswith(" - spot"):
        symbol = symbol.replace(" - spot", " - CI")
    
    # Check if needs default " - 24hs" suffix
    settlement_suffixes = [" - 24hs", " - 48hs", " - 72hs", " - CI", " - spot", " - T0", " - T1", " - T2"]
    has_suffix = any(symbol.endswith(suffix) for suffix in settlement_suffixes)
    
    # Check exceptions: CAUCIONES, INDICES, FUTUROS
    is_caucion = "PESOS" in symbol and symbol.split(" - ")[-1].endswith("D") and symbol.split(" - ")[-1][:-1].isdigit()
    is_index = symbol.startswith("I.") or symbol.startswith("IND.")
    is_future = "/" in symbol or bool(re.search(r'(ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)\d{2}', symbol))
    
    # Add default suffix if needed
    if not has_suffix and not is_caucion and not is_index and not is_future:
        symbol = f"{symbol} - 24hs"
    
    # Add prefix
    return "MERV - XMEV - " + symbol

# Test cases - including default suffix behavior
test_symbols = [
    "YPFD - 24hs",    # Existing suffix preserved
    "GGAL - spot",    # spot → CI conversion
    "BBAR - CI",      # Existing suffix preserved
    "YPFD",           # Default suffix added
    "ALUA - 48hs",    # Existing suffix preserved
    "PESOS - 3D",     # Exception: Caucion, no default
    "I.MERV",         # Exception: Index, no default
    "DLR/FEB25",      # Exception: Future, no default
]

print("Symbol Transformation Tests:")
for symbol in test_symbols:
    print(f"{symbol:20} → {transform_symbol(symbol)}")
```

**Expected Output**:
- `YPFD - 24hs` → `MERV - XMEV - YPFD - 24hs` (preserved)
- `GGAL - spot` → `MERV - XMEV - GGAL - CI` (converted)
- `BBAR - CI` → `MERV - XMEV - BBAR - CI` (preserved)
- `YPFD` → `MERV - XMEV - YPFD - 24hs` (default added)
- `ALUA - 48hs` → `MERV - XMEV - ALUA - 48hs` (preserved)
- `PESOS - 3D` → `MERV - XMEV - PESOS - 3D` (exception: caucion)
- `I.MERV` → `MERV - XMEV - I.MERV` (exception: index)
- `DLR/FEB25` → `MERV - XMEV - DLR/FEB25` (exception: future)

### Step 4: WebSocket Connection Test
```python
def market_data_handler(message):
    print(f"Market Data: {message}")

def error_handler(message):
    print(f"Error: {message}")
    
def exception_handler(exception):
    print(f"Exception: {exception}")

# Initialize websocket connection
pyRofex.init_websocket_connection(
    market_data_handler=market_data_handler,
    error_handler=error_handler,
    exception_handler=exception_handler
)
```

**Expected**: Connection established without errors
**On Failure**: Should trigger exponential backoff reconnection per FR-010

### Step 5: Market Data Subscription Test
```python
import time

# Test with a few symbols
test_tickers = ["MERV - XMEV - YPFD - 24hs", "MERV - XMEV - GGAL - CI"]
entries = [pyRofex.MarketDataEntry.BIDS, pyRofex.MarketDataEntry.OFFERS, pyRofex.MarketDataEntry.LAST]

# Subscribe to market data
pyRofex.market_data_subscription(tickers=test_tickers, entries=entries)

# Wait for data
time.sleep(5)
```

**Expected**: Market data messages received for valid symbols
**On Invalid Symbol**: Should be handled gracefully per FR-013

### Step 6: Data Validation Test
```python
def validate_market_data(data):
    # Critical field validation per FR-008
    required_fields = ['symbol', 'bid', 'ask', 'last']
    
    for field in required_fields:
        if field not in data or data[field] is None:
            return False, f"Missing required field: {field}"
    
    # Price validation
    price_fields = ['bid', 'ask', 'last']
    for field in price_fields:
        if not isinstance(data[field], (int, float)) or data[field] < 0:
            return False, f"Invalid price for {field}: {data[field]}"
    
    return True, "Valid"

# Test with sample data
sample_data = {
    'symbol': 'MERV - XMEV - YPFD - 24hs',
    'bid': 150.50,
    'ask': 151.00,
    'last': 150.75
}

is_valid, message = validate_market_data(sample_data)
print(f"Validation result: {is_valid}, {message}")
```

**Expected**: Validation passes for good data, fails for invalid data

### Step 7: Excel Integration Test
```python
import xlwings as xw
import pandas as pd

# Test Excel connection
try:
    wb = xw.Book('EPGB OC-DI - Python.xlsb')
    shtHomeBroker = wb.sheets('HomeBroker')
    print("Excel connection successful")
    
    # Test data update
    test_df = pd.DataFrame([{
        'symbol': 'MERV - XMEV - YPFD - 24hs',
        'bid': 150.50,
        'ask': 151.00,
        'last': 150.75,
        'volume': 1000
    }])
    
    shtHomeBroker.range('A1').options(index=True, header=True).value = test_df
    print("Excel update successful")
    
except Exception as e:
    print(f"Excel error (should continue collecting data): {e}")
    # Per FR-014: Skip updates, continue collecting data
```

**Expected**: Successful Excel update or graceful error handling

### Step 8: End-to-End Integration Test
```python
# Close websocket connection
pyRofex.close_websocket_connection()
print("Connection closed successfully")
```

**Expected**: Clean connection termination

## Acceptance Criteria Validation

### ✅ User Story 1: Configuration and Authentication
- [ ] pyRofex environment parameters set correctly
- [ ] Authentication successful with provided credentials
- [ ] Clear error messages on authentication failure

### ✅ User Story 2: Market Data Reception
- [ ] WebSocket connection established
- [ ] Market data received for subscribed instruments
- [ ] Data format matches expected structure

### ✅ User Story 3: Symbol Transformation
- [ ] "MERV - XMEV - " prefix added to all symbols
- [ ] " - spot" suffix correctly replaced with " - CI"
- [ ] Other suffixes preserved unchanged

### ✅ User Story 4: Excel Integration
- [ ] Excel workbook updated with market data
- [ ] Existing structure and formatting preserved
- [ ] Updates occur without blocking user interaction

## Error Scenario Testing

### Connection Failure Recovery
1. Disconnect network during operation
2. Verify exponential backoff reconnection attempts
3. Confirm data collection resumes after reconnection

### Excel File Lock Handling
1. Lock Excel file (open in another process)
2. Verify system continues collecting data
3. Confirm updates resume when file becomes available

### Invalid Symbol Handling
1. Subscribe to non-existent symbol
2. Verify graceful error handling
3. Confirm processing continues with valid symbols

## Performance Verification

### Update Frequency
- [ ] Excel updates occur every 2 seconds as specified
- [ ] Market data processed in real-time
- [ ] No blocking of Excel user interface

### Memory Usage
- [ ] Memory usage remains stable during extended operation
- [ ] No memory leaks observed
- [ ] DataFrame processing efficient

## Success Criteria
- All manual tests pass
- Error scenarios handled gracefully
- Performance meets specifications
- Excel integration preserved
- Real-time market data flowing