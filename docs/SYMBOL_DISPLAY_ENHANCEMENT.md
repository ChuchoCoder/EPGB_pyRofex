# Symbol Display Formatting Enhancement

## Summary
Enhanced the Excel symbol display functionality to remove the " - 24hs" suffix from OPTIONS while preserving it for other instruments (stocks, bonds, etc.).

## Changes Made

### 1. Modified `clean_symbol_for_display()` in `helpers.py`
**File:** `src/epgb_options/utils/helpers.py`

**Changes:**
- Added `is_option` parameter to the function
- Added logic to remove " - 24hs" suffix when `is_option=True`
- Updated docstring with examples

**Behavior:**
- **Options:** `"MERV - XMEV - GFGV38566O - 24hs"` → `"GFGV38566O"` (removes both prefix and suffix)
- **Stocks:** `"MERV - XMEV - GGAL - 24hs"` → `"GGAL - 24hs"` (removes only prefix, keeps suffix)
- **Cauciones:** `"MERV - XMEV - PESOS - 3D"` → `"PESOS - 3D"` (removes only prefix, keeps suffix)

### 2. Updated `SheetOperations` class in `sheet_operations.py`
**File:** `src/epgb_options/excel/sheet_operations.py`

**Changes:**
- Modified `__init__()` to accept optional `instrument_cache` parameter
- Added `set_instrument_cache()` method to allow setting the cache after initialization
- Updated `_add_symbols_to_sheet()` to:
  - Check if each symbol is an option using `instrument_cache.is_option_symbol()`
  - Pass the `is_option` flag to `clean_symbol_for_display()`

**Implementation Details:**
```python
# Check if symbol is an option (for proper display formatting)
is_option = False
if self.instrument_cache:
    is_option = self.instrument_cache.is_option_symbol(symbol)

# Clean symbol for display (remove prefix, and " - 24hs" for options)
display_symbol = clean_symbol_for_display(symbol, is_option=is_option)
```

### 3. Updated initialization flow in `main.py`
**File:** `src/epgb_options/main.py`

**Changes:**
- Added call to `self.sheet_operations.set_instrument_cache()` after initializing market data components
- This ensures the instrument cache is available for option detection during symbol display

### 4. Added comprehensive test suite
**File:** `tests/test_symbol_display.py`

**Test Cases:**
- Regular stocks keeping " - 24hs" suffix
- Options removing " - 24hs" suffix
- Cauciones keeping their specific suffixes (e.g., " - 3D")
- Stocks with other suffixes (e.g., " - 48hs")
- Already cleaned symbols

## Testing Results

### New Test: `test_symbol_display.py`
✅ All 9 tests passed
- Verified options remove " - 24hs" suffix
- Verified regular securities keep their suffixes
- Verified edge cases (already clean symbols, different suffix types)

### Existing Test: `test_option_detection.py`
✅ All 10 tests passed
- Confirmed no regression in option detection functionality
- Cache statistics: 7,590 total instruments, 1,608 options detected

## Technical Details

### Option Detection Method
The implementation uses the `InstrumentCache.is_option_symbol()` method, which:
- Performs O(1) set membership lookup for maximum performance
- Checks the `cficode` field from the pyRofex API
- Options have cficode "OCASPS" (CALL) or "OPASPS" (PUT)

### Initialization Order
1. Excel components initialized (including `SheetOperations`)
2. Symbols loaded from Excel
3. Market data components initialized (including `InstrumentCache`)
4. Instrument cache set in `SheetOperations` via `set_instrument_cache()`

This order ensures backward compatibility while allowing the cache to be available when needed.

## Backward Compatibility
- The `instrument_cache` parameter is optional in `SheetOperations.__init__()`
- The `is_option` parameter defaults to `False` in `clean_symbol_for_display()`
- If no cache is available, symbols are displayed with the standard prefix removal (no suffix removal)

## Benefits
1. **Cleaner Excel Display:** Options show only their ticker (e.g., "GFGV38566O") without the redundant " - 24hs" suffix
2. **Maintains Context:** Other instruments keep their settlement suffixes for clarity
3. **No Breaking Changes:** All existing functionality preserved
4. **Efficient:** Uses O(1) lookup for option detection
5. **Well-Tested:** Comprehensive test coverage ensures reliability
