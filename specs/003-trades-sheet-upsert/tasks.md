# Implementation Tasks: Trades Sheet Upsert

**Feature**: `003-trades-sheet-upsert`  
**Date**: 2025-10-22  
**Status**: In Progress

---

## Task Phases

### Phase 0: Setup (Est: 30 min)

- [X] **T0.1**: Verify project structure and ignore files
  - Files: `.gitignore`, `.dockerignore` (if applicable)
  - Actions: Ensure Python patterns present (\_\_pycache\_\/, \*.pyc, .venv/, etc.)
  
- [X] **T0.2**: Validate existing configuration
  - Files: `src/epgb_options/config/excel_config.py`, `.env`
  - Actions: Run `python src/epgb_options/config/excel_config.py` to verify current config
  
- [X] **T0.3**: Review existing dependencies
  - Files: `requirements.txt`, `pyproject.toml`
  - Actions: Verify pyRofex>=0.5.0, xlwings>=0.31.0, pandas>=2.0.0, python-dotenv>=1.0.0

---

### Phase 1: Configuration (Est: 15 min)

- [X] **T1.1**: Add Trades sheet configuration to excel_config.py
  - Files: `src/epgb_options/config/excel_config.py`
  - Actions: Add EXCEL_SHEET_TRADES, TRADES_BATCH_SIZE, TRADES_SYNC_ENABLED, TRADES_SYNC_INTERVAL_SECONDS, TRADES_COLUMNS dict
  - Dependencies: None
  
- [X] **T1.2**: Implement validate_trades_config() function
  - Files: `src/epgb_options/config/excel_config.py`
  - Actions: Add validation for sheet name, batch size, sync interval, column uniqueness
  - Dependencies: T1.1
  
- [X] **T1.3**: Update validate_excel_config() to call validate_trades_config()
  - Files: `src/epgb_options/config/excel_config.py`
  - Actions: Extend existing validation function
  - Dependencies: T1.2
  
- [ ] **T1.4**: Update .env with Trades configuration (optional)
  - Files: `.env`
  - Actions: Add EXCEL_SHEET_TRADES, TRADES_BATCH_SIZE, TRADES_SYNC_ENABLED, TRADES_SYNC_INTERVAL_SECONDS
  - Dependencies: T1.1

---

### Phase 2: Create Trades Module Structure (Est: 10 min)

- [X] **T2.1**: Create trades module directory
  - Files: `src/epgb_options/trades/` (directory)
  - Actions: Create directory if not exists
  - Dependencies: None

- [X] **T2.2**: Create module __init__.py with exports
  - Files: `src/epgb_options/trades/__init__.py`
  - Actions: Create file with ExecutionFetcher, TradesProcessor, TradesUpserter exports
  - Dependencies: T2.1

- [X] **T2.3**: Create placeholder files for module components
  - Files: `src/epgb_options/trades/execution_fetcher.py`, `trades_processor.py`, `trades_upsert.py`
  - Actions: Create empty Python files
  - Dependencies: T2.1

---

### Phase 3: Execution Fetcher Implementation (Est: 1.5 hours)

- [X] **T3.1**: Implement ExecutionFetcher class skeleton
  - Files: `src/epgb_options/trades/execution_fetcher.py`
  - Actions: Create class with __init__, subscribe_order_reports, fetch_historical_executions methods
  - Dependencies: T2.3
  
- [X] **T3.2**: Implement _parse_order_report method
  - Files: `src/epgb_options/trades/execution_fetcher.py`
  - Actions: Parse pyRofex WebSocket message to execution dict, validate required fields, handle fallback ExecutionID
  - Dependencies: T3.1
  
- [X] **T3.3**: Implement subscribe_order_reports method
  - Files: `src/epgb_options/trades/execution_fetcher.py`
  - Actions: Register WebSocket handler, subscribe to order reports, implement callback pattern
  - Dependencies: T3.2
  
- [X] **T3.4**: Implement fetch_historical_executions method
  - Files: `src/epgb_options/trades/execution_fetcher.py`
  - Actions: Call pyRofex REST API, filter FILLED/PARTIALLY_FILLED, extract executions, handle pagination
  - Dependencies: T3.1

---

### Phase 4: Trades Processor Implementation (Est: 45 min)

- [X] **T4.1**: Implement TradesProcessor class skeleton
  - Files: `src/epgb_options/trades/trades_processor.py`
  - Actions: Create class with process_executions method
  - Dependencies: T2.3
  
- [X] **T4.2**: Implement process_executions method
  - Files: `src/epgb_options/trades/trades_processor.py`
  - Actions: Convert executions list to DataFrame, parse timestamps, sort by TimestampUTC, set composite index, validate
  - Dependencies: T4.1
  
- [X] **T4.3**: Add data type conversions and validations
  - Files: `src/epgb_options/trades/trades_processor.py`
  - Actions: Convert numeric fields, validate enums, check field requirements
  - Dependencies: T4.2

---

### Phase 5: Trades Upserter Implementation (Est: 2 hours)

- [X] **T5.1**: Implement TradesUpserter class skeleton
  - Files: `src/epgb_options/trades/trades_upsert.py`
  - Actions: Create class with __init__, upsert_executions method
  - Dependencies: T2.3
  
- [X] **T5.2**: Implement _get_or_create_trades_sheet method
  - Files: `src/epgb_options/trades/trades_upsert.py`
  - Actions: Get sheet by name, create if missing, add headers
  - Dependencies: T5.1
  
- [X] **T5.3**: Implement _create_headers method
  - Files: `src/epgb_options/trades/trades_upsert.py`
  - Actions: Write header row using TRADES_COLUMNS, format as bold
  - Dependencies: T5.2
  
- [X] **T5.4**: Implement _read_existing_trades method (BULK READ)
  - Files: `src/epgb_options/trades/trades_upsert.py`
  - Actions: Read entire table from A2 downward, convert to DataFrame with composite index
  - Dependencies: T5.1
  
- [X] **T5.5**: Implement _merge_executions method
  - Files: `src/epgb_options/trades/trades_upsert.py`
  - Actions: pandas merge with indicator='_merge', identify inserts/updates/no-ops
  - Dependencies: T5.4
  
- [X] **T5.6**: Implement _build_final_with_audit method
  - Files: `src/epgb_options/trades/trades_upsert.py`
  - Actions: Populate audit columns (PreviousFilledQty, PreviousTimestampUTC, Superseded, CancelReason, UpdateCount) for updated rows
  - Dependencies: T5.5
  
- [X] **T5.7**: Implement _write_bulk_to_excel method (CRITICAL: BULK WRITE)
  - Files: `src/epgb_options/trades/trades_upsert.py`
  - Actions: Convert DataFrame to 2D array, single range write (A2:Q{n}), log stats
  - Dependencies: T5.6
  
- [X] **T5.8**: Implement _calculate_stats helper method
  - Files: `src/epgb_options/trades/trades_upsert.py`
  - Actions: Calculate inserted/updated/unchanged counts from merge indicator
  - Dependencies: T5.5
  
- [X] **T5.9**: Implement upsert_executions orchestration method
  - Files: `src/epgb_options/trades/trades_upsert.py`
  - Actions: Call read → merge → build audit → write bulk → calculate stats
  - Dependencies: T5.4, T5.5, T5.6, T5.7, T5.8

---

### Phase 6: API Client Integration (Est: 30 min)

- [X] **T6.1**: Add subscribe_order_reports method to api_client
  - Files: `src/epgb_options/market_data/api_client.py`
  - Actions: Add method to subscribe to pyRofex order reports
  - Dependencies: None
  
- [X] **T6.2**: Add error handler registration for WebSocket
  - Files: `src/epgb_options/market_data/api_client.py`
  - Actions: Register error/exception handlers for WebSocket
  - Dependencies: T6.1

---

### Phase 7: Main Script Integration (Est: 45 min)

- [X] **T7.1**: Import trades module components in main.py
  - Files: `src/epgb_options/main.py`
  - Actions: Add imports for ExecutionFetcher, TradesProcessor, TradesUpserter
  - Dependencies: T2.2
  
- [X] **T7.2**: Initialize trades components in main() function
  - Files: `src/epgb_options/main.py`
  - Actions: Create instances of fetcher, processor, upserter if TRADES_SYNC_ENABLED
  - Dependencies: T7.1, T1.1
  
- [X] **T7.3**: Implement execution callback handler
  - Files: `src/epgb_options/main.py`
  - Actions: Define on_execution callback to process and upsert executions
  - Dependencies: T7.2
  
- [X] **T7.4**: Subscribe to order reports in main loop
  - Files: `src/epgb_options/main.py`
  - Actions: Call subscribe_order_reports with callback
  - Dependencies: T7.3, T6.1

---

### Phase 8: Testing (Est: 1.5 hours) [OPTIONAL per Constitution]

- [ ] **T8.1**: Create test_trades_processor.py
  - Files: `tests/test_trades_processor.py`
  - Actions: Write unit tests for process_executions (empty list, valid data, invalid data)
  - Dependencies: T4.2

- [ ] **T8.2**: Create test_trades_upsert.py
  - Files: `tests/test_trades_upsert.py`
  - Actions: Write unit tests for merge logic, audit column population
  - Dependencies: T5.9

- [ ] **T8.3**: Manual integration test with mock execution
  - Files: N/A (manual testing)
  - Actions: Start application, simulate order event, verify Trades sheet updates
  - Dependencies: T7.4

---

### Phase 9: Validation & Documentation (Est: 30 min)

- [X] **T9.1**: Run configuration validation
  - Files: `src/epgb_options/config/excel_config.py`
  - Actions: Execute `python src/epgb_options/config/excel_config.py` and verify no errors
  - Dependencies: T1.3

- [X] **T9.2**: Verify bulk write compliance (code review)
  - Files: `src/epgb_options/trades/trades_upsert.py`
  - Actions: Code review to ensure no individual cell loops, only bulk range writes
  - Dependencies: T5.7

- [ ] **T9.3**: Test end-to-end with production workbook
  - Files: N/A (manual testing)
  - Actions: Open production workbook, run application, verify Trades sheet auto-created and populated
  - Dependencies: T7.4

- [X] **T9.4**: Update GitHub Copilot context (already done by /speckit.plan)
  - Files: `.github/copilot-instructions.md`
  - Actions: Verify context includes Python 3.9+, pyRofex, trades module
  - Dependencies: None

---

## Summary

**Total Estimated Time**: ~7.5 hours (excluding optional testing)

**Critical Path**:
- Phase 0 → Phase 1 → Phase 2 → Phase 5 (Upserter) → Phase 7 (Integration) → Phase 9 (Validation)

**Parallelizable Tasks** [P]:
- T3 (Execution Fetcher) and T4 (Trades Processor) can be developed in parallel after Phase 2
- T8 (Testing) can run in parallel with final integration

**Constitution Compliance Checkpoints**:
- **T5.7**: CRITICAL - Must use bulk range write (Constitution II)
- **T9.2**: Code review for bulk write compliance
- **T1.1**: Configuration transparency (Constitution IV)

---

**Tasks Version**: 1.0  
**Last Updated**: 2025-10-22  
**Status**: Ready for implementation
