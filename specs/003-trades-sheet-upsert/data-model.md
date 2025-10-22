# Data Model: Trades Sheet Upsert

**Feature**: `003-trades-sheet-upsert`  
**Date**: 2025-10-22  
**Purpose**: Define data entities, relationships, and state transitions for trades ingestion system.

---

## Entities

### 1. Execution (Primary Entity)

Represents a single execution event from the broker API (pyRofex). An execution is a filled or partially-filled order event.

**Attributes**:

| Field | Type | Required | Description | Source | Validation |
|-------|------|----------|-------------|--------|------------|
| `ExecutionID` | string | Yes | Unique execution identifier from broker | pyRofex `execId` | Non-empty, unique within (OrderID, Account) |
| `OrderID` | string | Yes | Parent order identifier | pyRofex `orderId` | Non-empty |
| `Account` | string | Yes | Broker account identifier | pyRofex `account` | Non-empty |
| `Symbol` | string | Yes | Instrument symbol (e.g., "GGAL - 24hs") | pyRofex `instrumentId.symbol` | Valid instrument from cache |
| `Side` | enum | Yes | Order side: BUY or SELL | pyRofex `side` | Must be "BUY" or "SELL" |
| `Quantity` | int | Yes | Total order quantity | pyRofex `orderQty` | > 0 |
| `Price` | decimal | Yes | Order limit price | pyRofex `price` | >= 0 |
| `FilledQty` | int | Yes | Cumulative filled quantity | pyRofex `cumQty` | 0 <= FilledQty <= Quantity |
| `LastQty` | int | No | Quantity of this specific execution | pyRofex `lastQty` | >= 0 |
| `LastPx` | decimal | No | Price of this specific execution | pyRofex `lastPx` | >= 0 |
| `TimestampUTC` | datetime | Yes | Execution timestamp (UTC) | pyRofex `transactTime` | ISO 8601, UTC timezone |
| `Status` | enum | Yes | Order status | pyRofex `ordStatus` | See Status Values below |
| `ExecutionType` | enum | Yes | Execution type | pyRofex `execType` | See Execution Type Values |
| `Source` | string | Yes | Data source identifier | Constant "pyRofex" | Non-empty |

**Status Values** (from pyRofex `ordStatus`):
- `NEW` — Order accepted, not filled
- `PARTIALLY_FILLED` — Partially executed
- `FILLED` — Fully executed
- `CANCELED` — Canceled before complete fill
- `REJECTED` — Order rejected by broker
- `EXPIRED` — Order expired

**Execution Type Values** (from pyRofex `execType`):
- `NEW` — New order accepted
- `TRADE` — Execution occurred (fill or partial fill)
- `CANCELED` — Order cancellation
- `REJECTED` — Order rejection
- `EXPIRED` — Order expiration

**Composite Key** (for upsert deduplication):
- Primary Key: `(ExecutionID, OrderID, Account)`
- Fallback Key (if ExecutionID missing): `(OrderID, TimestampUTC, Account)`

**Relationships**:
- One Execution belongs to one Order (via `OrderID`)
- One Execution belongs to one Account (via `Account`)
- One Execution references one Instrument (via `Symbol`)

---

### 2. ExecutionAudit (Embedded in Execution)

Audit metadata tracking updates to an Execution record (for partial→final transitions, cancellations).

**Attributes**:

| Field | Type | Required | Description | Populated When | Default |
|-------|------|----------|-------------|----------------|---------|
| `PreviousFilledQty` | int | No | Filled quantity before update | FilledQty changes | NULL |
| `PreviousTimestampUTC` | datetime | No | Timestamp of previous state | Any update occurs | NULL |
| `Superseded` | boolean | No | Flag indicating row was updated | Any update occurs | FALSE |
| `CancelReason` | string | No | Reason for cancellation | Status → CANCELED | "" (empty string) |
| `UpdateCount` | int | No | Number of updates to this execution | Any update occurs | 0 |

**Lifecycle**:
1. **Initial insert**: All audit fields are NULL/0/FALSE
2. **Update event** (e.g., partial→final):
   - Copy current `FilledQty` → `PreviousFilledQty`
   - Copy current `TimestampUTC` → `PreviousTimestampUTC`
   - Set `Superseded = TRUE`
   - Increment `UpdateCount`
3. **Cancellation**:
   - Populate `CancelReason` from broker event
   - Set `Superseded = TRUE`

---

### 3. TradesSheetConfig (Configuration Entity)

Configuration for Trades sheet location and structure in Excel workbook.

**Attributes**:

| Field | Type | Required | Description | Source | Default |
|-------|------|----------|-------------|--------|---------|
| `SheetName` | string | Yes | Name of Trades sheet in workbook | `EXCEL_SHEET_TRADES` env var | "Trades" |
| `HeaderRow` | int | Yes | Row number for column headers | `TRADES_HEADER_ROW` env var | 1 |
| `BatchSize` | int | Yes | Number of rows per batch for backfill | `TRADES_BATCH_SIZE` env var | 500 |
| `SyncEnabled` | boolean | Yes | Enable automatic sync | `TRADES_SYNC_ENABLED` env var | true |
| `SyncIntervalSeconds` | int | Yes | Interval between sync runs | `TRADES_SYNC_INTERVAL_SECONDS` env var | 300 (5 min) |
| `ColumnMapping` | dict | Yes | Map of field → Excel column letter | `TRADES_COLUMNS` dict | See research.md |

**Validation Rules**:
- `SheetName` must be non-empty and valid Excel sheet name (<= 31 chars, no special chars)
- `HeaderRow` must be >= 1
- `BatchSize` must be 1-10000
- `SyncIntervalSeconds` must be >= 10
- `ColumnMapping` must have no duplicate column letters

---

### 4. SyncCheckpoint (Metadata Entity)

Tracks last successful sync timestamp for incremental backfill resume capability.

**Attributes**:

| Field | Type | Required | Description | Storage Location | Default |
|-------|------|----------|-------------|------------------|---------|
| `LastBackfillCheckpoint` | datetime | No | Last processed execution timestamp (UTC) | Excel named range "LastBackfillCheckpoint" (cell Z1) | NULL (triggers full 30-day backfill) |
| `LastSyncTimestamp` | datetime | No | Last successful sync completion time | Excel named range "LastSyncTimestamp" (cell Z2) | NULL |

**Update Logic**:
1. **After successful batch**:
   - Set `LastBackfillCheckpoint` = max(`TimestampUTC`) from processed batch
   - Set `LastSyncTimestamp` = current UTC time
2. **On sync error**:
   - Do NOT update checkpoints (allows retry from same position)

---

## State Transitions

### Execution State Diagram

```
    NEW
     |
     v
PARTIALLY_FILLED ←→ PARTIALLY_FILLED (multiple partial fills)
     |
     v
   FILLED
     
Alternative paths:
- NEW → CANCELED
- PARTIALLY_FILLED → CANCELED
- NEW → REJECTED
- NEW → EXPIRED
```

**State Transition Rules**:

1. **NEW → PARTIALLY_FILLED**:
   - Trigger: First fill execution received
   - Actions:
     - Insert new row in Trades sheet
     - Populate all execution fields
     - Audit fields remain NULL/0/FALSE

2. **PARTIALLY_FILLED → PARTIALLY_FILLED** (additional fill):
   - Trigger: Subsequent fill execution received (same OrderID)
   - Actions:
     - Update existing row (matched by composite key)
     - Preserve previous `FilledQty` in `PreviousFilledQty`
     - Update `FilledQty`, `LastQty`, `LastPx`, `TimestampUTC`
     - Set `Superseded = TRUE`, increment `UpdateCount`

3. **PARTIALLY_FILLED → FILLED**:
   - Trigger: Final fill execution brings `FilledQty == Quantity`
   - Actions:
     - Update existing row
     - Preserve previous `FilledQty` in `PreviousFilledQty`
     - Update `Status = FILLED`, `FilledQty = Quantity`
     - Set `Superseded = TRUE`, increment `UpdateCount`

4. **PARTIALLY_FILLED → CANCELED**:
   - Trigger: Cancellation event received
   - Actions:
     - Update existing row
     - Set `Status = CANCELED`
     - Populate `CancelReason` from broker event
     - Set `Superseded = TRUE`, increment `UpdateCount`

5. **NEW → CANCELED** (no fills):
   - Trigger: Order canceled before any fills
   - Actions:
     - If row exists: update `Status = CANCELED`, set audit fields
     - If no row: skip (no execution occurred, not relevant for Trades sheet)

**Edge Cases**:

1. **Out-of-order events** (timestamp skew):
   - Sort all incoming executions by `TimestampUTC` before processing
   - Process in chronological order to ensure correct state progression

2. **Duplicate events** (same ExecutionID):
   - Composite key deduplication ensures idempotency
   - Second occurrence of same ExecutionID is a no-op (no update needed)

3. **Missing ExecutionID** (broker API limitation):
   - Use fallback composite key: `(OrderID, TimestampUTC, Account)`
   - Log warning for missing ExecutionID

---

## Relationships Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Execution                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ ExecutionID (PK)                                      │  │
│  │ OrderID (FK)                                          │  │
│  │ Account (FK)                                          │  │
│  │ Symbol → InstrumentCache                             │  │
│  │ Side, Quantity, Price, FilledQty, ...                │  │
│  │ TimestampUTC, Status, ExecutionType                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────── Embedded ─────────────────────────────┐ │
│  │ ExecutionAudit                                         │ │
│  │  - PreviousFilledQty                                  │ │
│  │  - PreviousTimestampUTC                               │ │
│  │  - Superseded                                         │ │
│  │  - CancelReason                                       │ │
│  │  - UpdateCount                                        │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
         │
         │ stored in
         v
┌──────────────────────────────┐
│   Excel Trades Sheet         │
│  (One row per Execution)     │
│                              │
│  Columns A-Q:                │
│  A: ExecutionID              │
│  B: OrderID                  │
│  C: Account                  │
│  D: Symbol                   │
│  E: Side                     │
│  F: Quantity                 │
│  G: Price                    │
│  H: FilledQty                │
│  I: TimestampUTC             │
│  J: Status                   │
│  K: ExecutionType            │
│  L: Source                   │
│  M: PreviousFilledQty        │
│  N: PreviousTimestampUTC     │
│  O: Superseded               │
│  P: CancelReason             │
│  Q: UpdateCount              │
└──────────────────────────────┘
         │
         │ references (via Symbol)
         v
┌──────────────────────────────┐
│  InstrumentCache             │
│  (existing module)           │
│  - validate symbols          │
│  - option detection          │
└──────────────────────────────┘
```

---

## Data Validation Rules

### On Insert (New Execution)

1. **Composite key uniqueness**:
   - Check if `(ExecutionID, OrderID, Account)` already exists in sheet
   - If exists → treat as update, not insert

2. **Field validations**:
   - `ExecutionID`, `OrderID`, `Account` must be non-empty
   - `Symbol` must exist in InstrumentCache (valid instrument)
   - `Side` must be "BUY" or "SELL"
   - `Quantity` > 0
   - `FilledQty` must be 0 <= FilledQty <= Quantity
   - `TimestampUTC` must be valid ISO 8601 datetime
   - `Status` must be valid enum value
   - `Price`, `LastPx` >= 0

3. **Required fields check**:
   - All fields marked "Required" in Execution entity must be present

### On Update (Existing Execution)

1. **State transition validation**:
   - New `Status` must be valid transition from old `Status` (see state diagram)
   - Example: Cannot transition FILLED → PARTIALLY_FILLED (invalid backward transition)

2. **Audit field logic**:
   - If `FilledQty` changed → populate `PreviousFilledQty`
   - If any field updated → set `Superseded = TRUE`, increment `UpdateCount`
   - If `Status = CANCELED` → require `CancelReason` (non-empty)

3. **Monotonicity checks**:
   - `FilledQty` should only increase (never decrease) unless cancellation
   - `TimestampUTC` of update should be >= original timestamp (detect out-of-order)

### On Batch Processing

1. **Deduplication within batch**:
   - If batch contains multiple events for same composite key, process chronologically (oldest first)

2. **Memory bounds**:
   - Batch size must not exceed configured `TRADES_BATCH_SIZE`
   - Fail batch if memory usage exceeds reasonable threshold (~100MB)

---

## Excel Schema

### Trades Sheet Layout

**Sheet Name**: Configurable via `EXCEL_SHEET_TRADES` (default: "Trades")

**Header Row** (Row 1):

| Column | Header | Data Type | Format | Example |
|--------|--------|-----------|--------|---------|
| A | ExecutionID | string | General | "exec_789" |
| B | OrderID | string | General | "order_456" |
| C | Account | string | General | "ACCOUNT123" |
| D | Symbol | string | General | "GGAL - 24hs" |
| E | Side | string | General | "BUY" |
| F | Quantity | integer | Number (0 decimals) | 100 |
| G | Price | decimal | Currency (2 decimals) | $1500.00 |
| H | FilledQty | integer | Number (0 decimals) | 50 |
| I | TimestampUTC | datetime | yyyy-mm-dd hh:mm:ss | 2025-10-22 14:30:45 |
| J | Status | string | General | "PARTIALLY_FILLED" |
| K | ExecutionType | string | General | "TRADE" |
| L | Source | string | General | "pyRofex" |
| M | PreviousFilledQty | integer | Number (0 decimals) | 25 |
| N | PreviousTimestampUTC | datetime | yyyy-mm-dd hh:mm:ss | 2025-10-22 14:25:00 |
| O | Superseded | boolean | General (TRUE/FALSE) | TRUE |
| P | CancelReason | string | General | "USER_CANCELED" |
| Q | UpdateCount | integer | Number (0 decimals) | 2 |

**Metadata Cells** (Hidden Column Z):

| Cell | Name | Purpose | Format |
|------|------|---------|--------|
| Z1 | LastBackfillCheckpoint | Resume cursor for backfill | ISO 8601 string |
| Z2 | LastSyncTimestamp | Last successful sync time | ISO 8601 string |

**Conditional Formatting** (Optional, for user experience):
- Highlight rows where `Superseded = TRUE` in light yellow
- Highlight rows where `Status = CANCELED` in light red
- Highlight rows where `Status = FILLED` in light green

---

## Data Flow Summary

```
pyRofex WebSocket           pyRofex REST API
Order Reports               (Historical Backfill)
      |                            |
      v                            v
┌──────────────────────────────────────────┐
│  execution_fetcher.py                    │
│  - Subscribe to order updates            │
│  - Fetch historical executions           │
│  - Parse pyRofex responses               │
└──────────────────────────────────────────┘
      |
      v
┌──────────────────────────────────────────┐
│  trades_processor.py                     │
│  - Validate execution data               │
│  - Build Execution entities              │
│  - Sort by TimestampUTC                  │
│  - Convert to pandas DataFrame           │
└──────────────────────────────────────────┘
      |
      v
┌──────────────────────────────────────────┐
│  trades_upsert.py                        │
│  - Read existing Trades sheet (bulk)     │
│  - Merge new executions (pandas)         │
│  - Identify inserts/updates              │
│  - Build audit columns                   │
│  - Write back to Excel (BULK RANGE)      │
│  - Update checkpoints                    │
└──────────────────────────────────────────┘
      |
      v
┌──────────────────────────────────────────┐
│  Excel Trades Sheet                      │
│  - Persistent storage                    │
│  - User-visible execution history        │
└──────────────────────────────────────────┘
```

---

**Data Model Complete**: All entities, relationships, validations, and state transitions defined. Ready for contract generation (Phase 1 continued).
