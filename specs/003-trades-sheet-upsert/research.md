# Research: Trades Sheet Upsert

**Feature**: `003-trades-sheet-upsert`  
**Date**: 2025-10-22  
**Purpose**: Resolve technical unknowns and establish best practices for implementing idempotent trades ingestion from pyRofex API to Excel.

---

## Research Questions

### RQ1: How does pyRofex API expose filled/partially-filled executions?

**Context**: Need to determine if pyRofex provides WebSocket subscriptions for order status updates or requires REST polling for filled executions.

**Decision**: Use **pyRofex WebSocket subscriptions for order updates** with REST API as fallback for backfill.

**Rationale**:
- pyRofex 0.5.0+ provides `order_report_subscription()` for real-time order status updates
- WebSocket handler receives order reports containing execution details (fills, partial fills, status changes)
- REST endpoint `get_order_status()` available for historical backfill and reconciliation
- WebSocket approach aligns with existing real-time market data pattern in codebase (see `api_client.py` market data subscriptions)

**Alternatives Considered**:
1. **REST polling only** — Rejected: Higher latency (>30s), more API load, doesn't meet SC-006 timeliness requirement (95% within 30 seconds)
2. **Database change feed** — Rejected: pyRofex doesn't expose database directly; all access via API
3. **Hybrid WebSocket + periodic REST reconciliation** — Selected alternative: Use WebSocket as primary, REST for hourly reconciliation to catch missed events

**Implementation Notes**:
```python
# pyRofex order subscription pattern (based on market data pattern)
import pyRofex

# Subscribe to order reports for specific account
pyRofex.order_report_subscription()

# Register handler
def order_report_handler(message):
    # Process order report
    # Extract executions from message['orderReport']['executions']
    pass

pyRofex.add_websocket_order_report_handler(order_report_handler)
```

**API Response Structure** (from pyRofex docs):
```json
{
  "orderReport": {
    "clOrdId": "user_order_123",
    "orderId": "broker_order_456",
    "account": "ACCOUNT123",
    "instrumentId": {"symbol": "GGAL - 24hs"},
    "side": "BUY",
    "orderQty": 100,
    "ordType": "LIMIT",
    "price": 1500.0,
    "ordStatus": "PARTIALLY_FILLED",
    "cumQty": 50,
    "leavesQty": 50,
    "lastQty": 25,
    "lastPx": 1499.0,
    "transactTime": "2025-10-22T14:30:45.123Z",
    "executions": [
      {
        "execId": "exec_789",
        "lastQty": 25,
        "lastPx": 1499.0,
        "execType": "TRADE",
        "transactTime": "2025-10-22T14:30:45.123Z"
      }
    ]
  }
}
```

---

### RQ2: What is the best practice for implementing idempotent upserts in pandas + xlwings?

**Context**: Need to efficiently match incoming executions against existing Trades sheet rows using composite key (Execution ID + Order ID + Broker Account) and update in-place for partial→final transitions.

**Decision**: Use **pandas DataFrame merge with indicator + bulk xlwings range update**.

**Rationale**:
- pandas `merge(how='outer', indicator=True)` efficiently identifies new, updated, and unchanged rows
- Bulk DataFrame operations in-memory minimize Excel COM calls (critical per Constitution II)
- Single `sheet.range().value = bulk_array` write for all upserts (follows existing pattern in `update_market_data_to_prices_sheet()`)
- Composite key as DataFrame MultiIndex enables O(1) lookups for deduplication

**Alternatives Considered**:
1. **Individual row lookups via xlwings** — Rejected: Violates Constitution II bulk write requirement; O(n) COM calls per update
2. **SQLite temp database + merge** — Rejected: Over-engineering for utility script; violates Constitution I (Simplicity First)
3. **Read full sheet → pandas → upsert in-memory → write back** — Selected: Aligns with existing pattern and constitution

**Implementation Pattern**:
```python
import pandas as pd
import xlwings as xw

def upsert_executions_to_sheet(sheet: xw.Sheet, new_executions_df: pd.DataFrame):
    """
    Idempotent upsert of executions to Trades sheet.
    
    Args:
        sheet: xlwings Sheet object for Trades sheet
        new_executions_df: DataFrame with columns [ExecutionID, OrderID, Account, ...]
                          and composite index
    """
    # Read existing trades from Excel (bulk read)
    existing_range = sheet.range('A2').expand('table')  # Skip header row
    existing_df = pd.DataFrame(existing_range.value, columns=TRADES_COLUMNS)
    
    # Set composite key as index
    existing_df.set_index(['ExecutionID', 'OrderID', 'Account'], inplace=True)
    new_executions_df.set_index(['ExecutionID', 'OrderID', 'Account'], inplace=True)
    
    # Merge with indicator to identify updates vs inserts
    merged = existing_df.merge(
        new_executions_df, 
        how='outer', 
        left_index=True, 
        right_index=True, 
        indicator=True,
        suffixes=('_old', '_new')
    )
    
    # Identify rows needing updates (partial→final, cancellations)
    needs_update = merged['_merge'] == 'both'
    needs_insert = merged['_merge'] == 'right_only'
    
    # Build final DataFrame with audit columns
    final_df = build_final_with_audit(merged, needs_update, needs_insert)
    
    # CRITICAL: Bulk write entire table back to Excel in single operation
    sheet.range('A2').value = final_df.reset_index().values
    
    return {
        'inserted': needs_insert.sum(),
        'updated': needs_update.sum(),
        'unchanged': (merged['_merge'] == 'left_only').sum()
    }
```

**Performance Considerations**:
- For 50k rows: pandas merge ~100ms, xlwings bulk write ~2s → total <3s (well within 10s goal)
- Batching strategy: Process in 500-row batches if backfilling to bound memory (~10MB per batch)

---

### RQ3: How should partial→final execution transitions preserve historical context?

**Context**: When a partial fill (e.g., 50/100 qty) later completes (100/100 qty), need to update row while retaining audit trail per FR-011.

**Decision**: **In-place row update with audit columns** (PreviousFilledQty, PreviousTimestampUTC, Superseded flag, CancelReason).

**Rationale**:
- Keeps Trades sheet compact (one row per execution) while preserving sufficient historical context
- Aligns with user choice from clarifications (Option B: update + audit marker)
- Audit columns provide traceability without requiring separate audit sheet (avoids over-engineering)
- Excel formulas and pivot tables can operate on single-table structure

**Alternatives Considered**:
1. **Append new row for each state change** — Rejected: Creates duplicates, violates FR-004 idempotency, complicates downstream analysis
2. **Separate audit log sheet** — Rejected: Over-engineering for utility script; unnecessary complexity
3. **Event sourcing pattern** — Rejected: Violates Constitution I (Simplicity First)

**Audit Column Schema**:
| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `PreviousFilledQty` | int | Quantity before update | 50 (when partial→final) |
| `PreviousTimestampUTC` | datetime | Timestamp of previous state | 2025-10-22T14:30:00Z |
| `Superseded` | bool | Flag indicating row was updated | TRUE |
| `CancelReason` | str | Reason if canceled | "USER_CANCELED" or "" |
| `UpdateCount` | int | Number of updates to this execution | 2 |

**State Transition Logic**:
```python
def build_audit_columns(old_row, new_row):
    """
    Build audit columns when updating an execution row.
    
    Args:
        old_row: Existing row from Excel (Series)
        new_row: New execution data (Series)
        
    Returns:
        dict: Audit column values
    """
    audit = {}
    
    # Preserve previous filled quantity if changed
    if old_row['FilledQty'] != new_row['FilledQty']:
        audit['PreviousFilledQty'] = old_row['FilledQty']
        audit['PreviousTimestampUTC'] = old_row['TimestampUTC']
        audit['Superseded'] = True
        audit['UpdateCount'] = old_row.get('UpdateCount', 0) + 1
    
    # Handle cancellations
    if new_row['Status'] == 'CANCELED':
        audit['CancelReason'] = new_row.get('CancelReason', 'BROKER_CANCELED')
        audit['Superseded'] = True
    
    return audit
```

---

### RQ4: What are best practices for batched processing with resume tokens in Python/pandas?

**Context**: Need to support incremental backfills of large datasets (up to 50k rows) with resume capability per FR-014.

**Decision**: **Cursor-based pagination with persistent state in Excel metadata**.

**Rationale**:
- pyRofex REST API supports `from_date` parameter for historical order queries
- Store last processed timestamp in Excel sheet metadata (named range or hidden cell)
- Process in configurable batch sizes (default 500) to bound memory
- If process crashes, resume from last checkpoint timestamp

**Alternatives Considered**:
1. **External state file (.json)** — Rejected: Adds file management complexity; Excel metadata simpler
2. **Process all at once** — Rejected: Fails for large backfills >10k rows; memory issues
3. **Database cursor** — Rejected: No database in architecture (Constitution I: Simplicity)

**Implementation Pattern**:
```python
def backfill_trades(api_client, sheet, batch_size=500):
    """
    Incrementally backfill trades with resume capability.
    
    Args:
        api_client: pyRofexClient instance
        sheet: xlwings Sheet object for Trades sheet
        batch_size: Number of executions per batch
    """
    # Read last checkpoint from Excel metadata
    last_checkpoint = sheet.range('LastBackfillCheckpoint').value  # ISO timestamp
    if not last_checkpoint:
        last_checkpoint = (datetime.now(UTC) - timedelta(days=30)).isoformat()
    
    while True:
        # Fetch next batch from API
        executions = api_client.get_historical_executions(
            from_date=last_checkpoint,
            limit=batch_size
        )
        
        if not executions:
            break  # No more data
        
        # Process batch
        executions_df = pd.DataFrame(executions)
        stats = upsert_executions_to_sheet(sheet, executions_df)
        
        # Update checkpoint
        last_timestamp = executions_df['TimestampUTC'].max()
        sheet.range('LastBackfillCheckpoint').value = last_timestamp
        
        logger.info(f"Backfill batch: {stats['inserted']} inserted, {stats['updated']} updated")
        
        # Memory management: Clear batch
        del executions_df
        
        if len(executions) < batch_size:
            break  # Last batch (incomplete)
    
    logger.info("Backfill complete")
```

**Checkpoint Storage**:
- Named range `LastBackfillCheckpoint` in Trades sheet (cell Z1, hidden column)
- Format: ISO 8601 UTC timestamp string
- Updated after each successful batch write
- Cleared on manual "full sync" operation

---

### RQ5: How should configuration for Trades sheet be exposed?

**Context**: Need configurable sheet name, column mapping, batch size, sync schedule per FR-007 while following existing config pattern.

**Decision**: **Extend `config/excel_config.py` with trades-specific section** + `.env` overrides.

**Rationale**:
- Aligns with existing configuration pattern (excel_config.py, pyrofex_config.py)
- .env support already implemented via python-dotenv
- Validation functions prevent misconfigurations
- Follows Constitution IV: Configuration Transparency

**Configuration Schema**:
```python
# In config/excel_config.py

# Trades Sheet Configuration
EXCEL_SHEET_TRADES = os.getenv('EXCEL_SHEET_TRADES', 'Trades')
TRADES_HEADER_ROW = int(os.getenv('TRADES_HEADER_ROW', '1'))
TRADES_BATCH_SIZE = int(os.getenv('TRADES_BATCH_SIZE', '500'))
TRADES_SYNC_ENABLED = os.getenv('TRADES_SYNC_ENABLED', 'true').lower() == 'true'
TRADES_SYNC_INTERVAL_SECONDS = int(os.getenv('TRADES_SYNC_INTERVAL_SECONDS', '300'))  # 5 min default

# Column mapping (Excel column letters)
TRADES_COLUMNS = {
    'ExecutionID': os.getenv('TRADES_COL_EXECUTION_ID', 'A'),
    'OrderID': os.getenv('TRADES_COL_ORDER_ID', 'B'),
    'Account': os.getenv('TRADES_COL_ACCOUNT', 'C'),
    'Symbol': os.getenv('TRADES_COL_SYMBOL', 'D'),
    'Side': os.getenv('TRADES_COL_SIDE', 'E'),
    'Quantity': os.getenv('TRADES_COL_QUANTITY', 'F'),
    'Price': os.getenv('TRADES_COL_PRICE', 'G'),
    'FilledQty': os.getenv('TRADES_COL_FILLED_QTY', 'H'),
    'TimestampUTC': os.getenv('TRADES_COL_TIMESTAMP', 'I'),
    'Status': os.getenv('TRADES_COL_STATUS', 'J'),
    'ExecutionType': os.getenv('TRADES_COL_EXEC_TYPE', 'K'),
    'Source': os.getenv('TRADES_COL_SOURCE', 'L'),
    # Audit columns
    'PreviousFilledQty': os.getenv('TRADES_COL_PREV_FILLED_QTY', 'M'),
    'PreviousTimestampUTC': os.getenv('TRADES_COL_PREV_TIMESTAMP', 'N'),
    'Superseded': os.getenv('TRADES_COL_SUPERSEDED', 'O'),
    'CancelReason': os.getenv('TRADES_COL_CANCEL_REASON', 'P'),
    'UpdateCount': os.getenv('TRADES_COL_UPDATE_COUNT', 'Q'),
}

def validate_trades_config():
    """Validate trades-specific configuration."""
    errors = []
    
    if not EXCEL_SHEET_TRADES.strip():
        errors.append("EXCEL_SHEET_TRADES cannot be empty")
    
    if TRADES_BATCH_SIZE < 1 or TRADES_BATCH_SIZE > 10000:
        errors.append(f"TRADES_BATCH_SIZE must be 1-10000, got {TRADES_BATCH_SIZE}")
    
    if TRADES_SYNC_INTERVAL_SECONDS < 10:
        errors.append(f"TRADES_SYNC_INTERVAL_SECONDS too low (min 10s), got {TRADES_SYNC_INTERVAL_SECONDS}")
    
    # Validate column uniqueness
    col_values = list(TRADES_COLUMNS.values())
    if len(col_values) != len(set(col_values)):
        errors.append("Duplicate column mappings detected in TRADES_COLUMNS")
    
    return errors
```

**Example .env**:
```bash
# Trades Sheet Configuration
EXCEL_SHEET_TRADES=Trades
TRADES_BATCH_SIZE=500
TRADES_SYNC_ENABLED=true
TRADES_SYNC_INTERVAL_SECONDS=300

# Optional: Custom column mapping (defaults to A-Q)
# TRADES_COL_EXECUTION_ID=A
# TRADES_COL_ORDER_ID=B
# ...
```

---

## Best Practices Summary

### pyRofex WebSocket Integration
1. **Use existing handler pattern** from `api_client.py` market data subscriptions
2. **Register order report handler** via `pyRofex.add_websocket_order_report_handler()`
3. **Implement reconnection logic** for WebSocket disconnections (exponential backoff)
4. **Log all API errors** with structured logging (use existing `utils/logging.py`)

### Excel Bulk Updates (Constitution II)
1. **Always use range writes** — Never loop over individual cells
2. **Read entire table** → process in pandas → write back in single operation
3. **Minimize COM calls** — Batch all formatting and writes
4. **Example**: `sheet.range('A2:Q5001').value = df.values`

### Idempotency
1. **Composite key deduplication** — Use (ExecutionID, OrderID, Account) as DataFrame MultiIndex
2. **pandas merge with indicator** — Efficiently identify inserts/updates/no-ops
3. **Atomic writes** — Save workbook only after successful upsert batch

### Error Handling
1. **Broker API failures** — Log and skip failed operation (don't block entire sync)
2. **Excel write failures** — Retry once, then log error and continue
3. **Validation errors** — Log details and populate error column in sheet

### Performance
1. **Target <10s for normal sync** (hundreds of executions)
2. **Batch large backfills** in 500-row chunks to bound memory
3. **Use pandas vectorized operations** over Python loops
4. **Profile with cProfile** if sync exceeds 10s threshold

---

## Open Questions for Phase 1

1. **Q**: Should we create Trades sheet automatically if missing, or error?  
   **A**: Auto-create with headers (follows pattern from market data sheets). Log warning on first creation.

2. **Q**: What Excel cell format for timestamps — ISO string or Excel datetime?  
   **A**: Excel datetime (numeric) for filtering/sorting compatibility. Store UTC offset in separate column.

3. **Q**: Should backfill be manual-triggered or automatic on first run?  
   **A**: Automatic on first run (when LastBackfillCheckpoint is empty). Manual re-backfill via config flag.

4. **Q**: How to handle execution events arriving out-of-order (timestamp skew)?  
   **A**: Sort by TimestampUTC before upsert. Use execution timestamp as canonical ordering (not receive time).

---

**Research Complete**: All technical unknowns resolved. Ready to proceed to Phase 1 (Data Model & Contracts).
