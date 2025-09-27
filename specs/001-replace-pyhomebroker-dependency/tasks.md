# Tasks: Replace PyHomeBroker with PyRofex

**Input**: Design documents from `/specs/001-replace-pyhomebroker-dependency/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory ✓
   → Extract: Python 3.x, pyRofex/xlwings/pandas, single project structure
2. Load optional design documents: ✓
   → data-model.md: Market Data Stream, Instrument Symbol, Excel Data Range, Broker Connection
   → contracts/: pyRofex WebSocket API contracts  
   → research.md: COCOS broker config, symbol transformation, error handling
   → quickstart.md: Manual testing procedures
3. Generate tasks by category:
   → Setup: dependency installation, environment configuration
   → Core: symbol transformation, websocket handlers, market data processing
   → Integration: pyRofex initialization, Excel integration updates
   → Validation: manual testing per constitutional principles
4. Apply constitutional rules:
   → No formal testing phase (Principle V: No Testing Overhead)
   → Focus on operational reliability through error handling
   → Simplicity first - modify existing files rather than complex restructuring
5. Number tasks sequentially (T001, T002...)
6. Constitutional compliance: No TDD phase, focus on working implementation
7. Validate task completeness: All contracts implemented, Excel integration preserved
8. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: Repository root with existing files
- Paths: `main_HM.py`, `Options_Helper_HM.py`, `EPGB OC-DI - Python.xlsb`

## Phase 3.1: Setup & Dependencies
- [ ] T001 Install pyRofex dependency: `pip install pyRofex` (replace pyhomebroker)
- [ ] T002 [P] Update import statements in `main_HM.py` from pyhomebroker to pyRofex
- [ ] T003 [P] Update import statements in `Options_Helper_HM.py` if needed

## Phase 3.2: Core Implementation - Symbol Transformation
- [ ] T004 [P] Create symbol transformation function in `Options_Helper_HM.py`:
  - Add "MERV - XMEV - " prefix to all symbols
  - Replace " - spot" suffix with " - CI"  
  - Preserve other suffixes (" - 24hs", etc.)
- [ ] T005 Update all symbol list functions in `Options_Helper_HM.py` to apply transformation

## Phase 3.3: PyRofex Environment Configuration
- [ ] T006 Replace broker configuration section in `main_HM.py`:
  - Remove pyhomebroker initialization 
  - Add pyRofex environment parameter setup for COCOS broker
  - Set URL: "https://api.cocos.xoms.com.ar/" 
  - Set WebSocket: "wss://api.cocos.xoms.com.ar/"
- [ ] T007 Implement pyRofex authentication in `main_HM.py`:
  - Replace pyhomebroker auth with pyRofex.initialize()
  - Use Environment.LIVE parameter
  - Add error handling per FR-003 (stop execution on auth failure)

## Phase 3.4: WebSocket Implementation
- [ ] T008 Create market data handler function in `main_HM.py`:
  - Replace on_options() function for pyRofex websocket format
  - Parse pyRofex message structure: symbol, bid, ask, bid_size, ask_size, last, change, open, high, low, previous_close, turnover, volume, operations, datetime
  - Implement data validation for critical fields per FR-008:
    - symbol: required, non-empty string
    - price fields (bid, ask, last): required, positive float
    - volume fields: optional, non-negative integer if present
  - Handle invalid symbols per FR-013: catch "SYMBOL_NOT_FOUND" errors, mark as "unavailable" in Excel, continue processing
  - Transform pyRofex data to pandas DataFrame compatible with existing Excel structure
  - Map datetime field to Excel-compatible timestamp format
- [ ] T009 Create websocket error handler in `main_HM.py`:
  - Implement exponential backoff reconnection per FR-010 (1s, 2s, 4s, 8s)
  - Add connection error logging
- [ ] T010 Create websocket exception handler in `main_HM.py`:
  - Handle websocket exceptions gracefully
  - Log exceptions for troubleshooting
- [ ] T011 Update securities handler function in `main_HM.py`:
  - Adapt on_securities() for pyRofex message format (replace pyhomebroker quotes structure)
  - Parse pyRofex securities data: symbol, settlement, change, datetime + market data fields
  - Maintain symbol concatenation logic: `symbol + ' - ' + settlement`
  - Apply data transformations:
    - Reset DataFrame index and set symbol as new index
    - Drop settlement column after concatenation
    - Convert change from percentage (divide by 100) to decimal format
    - Convert datetime string to pandas datetime object
  - Apply data validation rules from T008 (symbol required, price fields positive)
  - Update global everything DataFrame with processed securities data
- [ ] T012 Update repos handler function in `main_HM.py`:
  - Adapt on_repos() for pyRofex cauciones data format (replace pyhomebroker quotes structure)
  - Parse pyRofex cauciones data: symbol, settlement, bid_rate, ask_rate, last, turnover, bid_amount, ask_amount
  - Apply PESOS filtering: filter symbols containing 'PESOS' string
  - Apply data transformations:
    - Reset index and set settlement as datetime index
    - Convert rates from percentage (divide by 100): last, bid_rate, ask_rate
    - Drop unnecessary columns: open, high, low, volume, operations, datetime
    - Reorder columns: ['last', 'turnover', 'bid_amount', 'bid_rate', 'ask_rate', 'ask_amount']
  - Apply data validation rules from T008 (required fields validation)
  - Update global cauciones DataFrame with processed repos data

## Phase 3.5: WebSocket Connection & Subscription
- [ ] T013 Initialize websocket connection in `main_HM.py`:
  - Replace HomeBroker() instantiation with pyRofex websocket setup
  - Connect market_data_handler, error_handler, exception_handler
- [ ] T014 Implement market data subscriptions in `main_HM.py`:
  - Replace hb.online.subscribe_*() calls with pyRofex.market_data_subscription()
  - Apply symbol transformations to all subscription lists using T004 transformation function
  - Subscribe to BIDS, OFFERS, LAST market data entries per MarketDataEntry enum
  - Handle subscription errors for invalid symbols:
    - Catch "SYMBOL_NOT_FOUND" error codes from pyRofex response
    - Log invalid symbols with timestamp for debugging
    - Continue subscription process with remaining valid symbols
    - Track invalid symbols list for Excel marking as "unavailable"
  - Implement subscription confirmation validation:
    - Verify subscription response status for each symbol
    - Retry failed subscriptions once before marking as invalid
    - Log successful subscriptions for monitoring

## Phase 3.6: Excel Integration Updates  
- [ ] T015 Update Excel data processing in `main_HM.py`:
  - Adapt DataFrame updates to handle pyRofex data structure
  - Ensure existing Excel column mapping is preserved
  - Add Excel file access error handling per FR-014 (skip updates, continue collecting)
- [ ] T016 Test Excel xlwings compatibility:
  - Verify .xlsb format compatibility maintained
  - Test HomeBroker and Tickers sheet access
  - Confirm 2-second update frequency preserved

## Phase 3.7: Error Handling & Resilience
- [ ] T017 Implement comprehensive error handling in `main_HM.py`:
  - Add try-catch blocks around critical operations
  - Log errors without stopping execution (except authentication)
  - Implement graceful degradation for Excel file locks
- [ ] T018 Add connection resilience in `main_HM.py`:
  - Verify exponential backoff reconnection implementation
  - Add connection status tracking
  - Log connection events for monitoring

## Phase 3.8: Manual Validation (Per Constitutional Principles)
- [ ] T019 Execute quickstart.md Step 1-3: Environment and authentication testing
  - **Step 1**: Verify pyRofex environment parameters set (COCOS URLs) - expect no errors
  - **Step 2**: Test authentication with provided credentials - expect success or clear error message
  - **Step 3**: Test symbol transformation function with test cases:
    - "YPFD - 24hs" → "MERV - XMEV - YPFD - 24hs" ✓
    - "GGAL - spot" → "MERV - XMEV - GGAL - CI" ✓
    - "BBAR - CI" → "MERV - XMEV - BBAR - CI" ✓
  - **Success Criteria**: All transformations correct, authentication succeeds
  - **Failure Action**: Stop if authentication fails (per FR-003)

- [ ] T020 Execute quickstart.md Step 4-5: WebSocket connection and subscription testing
  - **Step 4**: Initialize websocket with handlers - expect connection established
  - **Step 5**: Subscribe to test tickers ["MERV - XMEV - YPFD - 24hs", "MERV - XMEV - GGAL - CI"]
  - **Success Criteria**: Market data messages received within 5 seconds
  - **Performance Baseline**: Initial data received <10 seconds, subsequent updates <2 seconds
  - **Error Handling**: Connection failures trigger exponential backoff (1s, 2s, 4s, 8s)

- [ ] T021 Execute quickstart.md Step 6-7: Data validation and Excel integration testing  
  - **Step 6**: Validate market data structure with critical fields check:
    - Required fields present: symbol, bid, ask, last ✓
    - Price fields positive numbers ✓
    - Data types correct for Excel compatibility ✓
  - **Step 7**: Test Excel integration with EPGB OC-DI - Python.xlsb:
    - HomeBroker sheet accessible ✓
    - Data update successful or graceful error handling ✓
    - .xlsb format compatibility maintained ✓
  - **Success Criteria**: Valid data passes validation, Excel updates without blocking UI

- [ ] T022 Execute quickstart.md Step 8: End-to-end integration testing
  - **Integration Test**: Full pipeline from websocket → validation → Excel update
  - **Connection Cleanup**: Close websocket connection cleanly
  - **Data Integrity**: Verify complete data flow maintains structure and format
  - **Success Criteria**: All components work together, clean shutdown, no data corruption

- [ ] T023 [P] Verify error scenarios from quickstart.md:
  - **Connection failure recovery**:
    - Disconnect network during operation
    - Verify exponential backoff attempts (1s, 2s, 4s, 8s intervals)
    - Confirm data collection resumes after reconnection
  - **Excel file lock handling**:
    - Lock Excel file in another process
    - Verify system continues collecting data (per FR-014)
    - Confirm updates resume when file available
  - **Invalid symbol handling**:
    - Subscribe to "INVALID_SYMBOL_TEST"
    - Verify "SYMBOL_NOT_FOUND" error caught gracefully (per FR-013)
    - Confirm processing continues with valid symbols
  - **Success Criteria**: All error scenarios handled per functional requirements, no crashes

- [ ] T024 [P] Performance verification from quickstart.md:
  - **Update frequency baseline**: Excel refreshes every 2 seconds (±0.5s tolerance)
  - **Memory usage stability**:
    - Baseline: <100MB for ~500 symbols
    - No memory leaks during 30-minute test run
    - DataFrame processing <50ms per update
  - **Excel UI responsiveness**:
    - User can edit cells during updates ✓
    - No UI freezing >1 second ✓
    - Scroll/navigation remains fluid ✓
  - **Network efficiency**:
    - Websocket maintains connection during market hours
    - Reconnection time <30 seconds after network restore
  - **Success Criteria**: All performance baselines met, system stable under normal load
  - Excel UI non-blocking operation

## Dependencies
- Setup (T001-T003) before core implementation
- Symbol transformation (T004-T005) before websocket subscriptions (specifically T004 before T014)
- Environment setup (T006-T007) before websocket connection
- WebSocket error handlers (T009-T010) before connection initialization (T013)
- WebSocket handlers (T008-T012) before connection initialization (T013-T014)
- Symbol transformation (T004) must complete before market data subscriptions (T014)
- Core implementation (T004-T014) before Excel integration (T015-T016)
- Error handling (T017-T018) can run parallel with other phases
- Manual validation (T019-T024) requires all implementation complete

### Critical Path Dependencies
1. **T004 → T014**: Symbol transformation function must exist before subscription process
2. **T009-T010 → T013**: Error handlers must be defined before websocket connection setup
3. **T006-T007 → T013**: Environment configuration must complete before connection attempts
4. **T008-T012 → T013-T014**: All handlers must be ready before connection and subscription

## Parallel Execution Examples

```bash
# Phase 3.1 - Parallel setup:
T002: "Update import statements in main_HM.py from pyhomebroker to pyRofex"
T003: "Update import statements in Options_Helper_HM.py if needed"

# Phase 3.2 - Symbol transformation (must complete before T014):
T004: "Create symbol transformation function in Options_Helper_HM.py"
T005: "Update all symbol list functions to apply transformation"

# Phase 3.3 - Environment setup (must complete before T013):
T006: "Replace broker configuration section in main_HM.py"
T007: "Implement pyRofex authentication in main_HM.py"

# Phase 3.4 - Parallel handler creation (must complete before T013):
T008: "Create market data handler function in main_HM.py"
T009: "Create websocket error handler in main_HM.py" (required before T013)
T010: "Create websocket exception handler in main_HM.py" (required before T013)
T011: "Update securities handler function in main_HM.py"
T012: "Update repos handler function in main_HM.py"

# Phase 3.5 - Sequential connection setup (dependencies enforced):
T013: "Initialize websocket connection" (requires T009-T010, T006-T007)
T014: "Implement market data subscriptions" (requires T004, T013)

# Phase 3.8 - Parallel validation:
T023: "Verify error scenarios from quickstart.md"
T024: "Performance verification from quickstart.md"
```

## Performance Baselines & Acceptance Thresholds

### Timing Requirements
- **Excel Update Frequency**: 2 seconds ±0.5s (1.5-2.5 second range acceptable)
- **Initial Data Reception**: <10 seconds after websocket connection
- **Subsequent Updates**: <2 seconds from market data event to Excel refresh
- **Connection Timeout**: 30 seconds maximum for initial connection
- **Reconnection Time**: <30 seconds after network restore

### Memory & Resource Limits
- **Memory Usage**: <100MB baseline for ~500 symbols during normal operation
- **Memory Stability**: No growth >10MB over 30-minute test period (leak detection)
- **DataFrame Processing**: <50ms per market data update transformation
- **CPU Usage**: <5% average during steady state operation

### Excel Integration Performance
- **UI Responsiveness**: User can edit cells during updates without >1 second delay
- **Sheet Access Time**: HomeBroker/Tickers sheet operations <500ms
- **Data Writing**: xlwings updates complete <200ms per batch
- **File Lock Recovery**: Resume updates within 5 seconds after lock release

### Network & Connection Stability
- **Websocket Uptime**: >99% connection time during market hours
- **Reconnection Success**: >95% success rate with exponential backoff
- **Data Integrity**: Zero missing updates during stable connection periods
- **Error Recovery**: System operational within 1 minute of error resolution

### Validation Pass Criteria
- **Functional**: All user stories and acceptance scenarios pass
- **Performance**: All baselines met during 30-minute sustained test
- **Error Handling**: All error scenarios handled per FR specifications
- **Constitutional**: No violations of simplicity, Excel integration, or operational principles

## Constitutional Compliance Notes
- **No formal testing phase**: Per Principle V (No Testing Overhead)
- **Operational reliability**: Focus on error handling and logging
- **Simplicity**: Modify existing files rather than major restructuring
- **Excel integration**: Preserve xlwings compatibility (Principle II)
- **Real-time updates**: WebSocket implementation (Principle III)
- **Configuration transparency**: Clear symbol transformation rules (Principle IV)

## Task Execution Rules
- [P] tasks = different files or independent operations, no dependencies
- Sequential tasks must complete before dependent tasks begin
- Manual validation replaces formal testing per constitutional principles
- Each task should be completable in 15-30 minutes
- Include exact file paths and specific implementation details
- Focus on operational reliability over test coverage