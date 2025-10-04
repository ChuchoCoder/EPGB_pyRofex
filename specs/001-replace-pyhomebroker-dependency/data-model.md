# Data Model: PyRofex Market Data Integration

## Core Entities

### Market Data Stream
**Purpose**: Real-time financial data received from pyRofex websocket

**Attributes**:
- symbol: string (instrument identifier with MERV-XMEV prefix)
- bid: float (highest buy price)
- ask: float (lowest sell price) 
- bid_size: int (volume at bid price)
- ask_size: int (volume at ask price)
- last: float (last traded price)
- change: float (price change as decimal, not percentage)
- open: float (opening price)
- high: float (highest price)
- low: float (lowest price)
- previous_close: float (previous session close)
- turnover: float (total value traded)
- volume: int (total shares/contracts traded)
- operations: int (number of trades)
- datetime: datetime (timestamp of data)

**Validation Rules**:
- symbol: required, non-empty string
- price fields (bid, ask, last): required, positive float
- volume fields: required, non-negative integer
- datetime: required, valid datetime object

**State Transitions**: Static data snapshot per update

### Instrument Symbol
**Purpose**: Financial instrument identifier with transformation logic

**Attributes**:
- raw_symbol: string (original symbol from Tickers sheet)
- pyrofex_symbol: string (transformed symbol with prefix/suffix changes)
- instrument_type: string (options, stocks, bonds, cedears, cauciones)

**Transformation Rules** (based on analysis of 7,590 real pyRofex instruments):
- Add "MERV - XMEV - " prefix ONLY to MERV market securities (93% of symbols)
- Do NOT add prefix to: ROS options (295), ROS futures (52), DLR futures/options (84), most indices (4), international markets (~60)
- Exception: "I.MERVAL" DOES get MERV prefix (special case)
- Replace " - spot" suffix with " - CI"
- Add " - 24hs" as default suffix ONLY for MERV securities without suffix
- Do NOT add default suffix for: cauciones (PESOS - XD), indices, options, futures
- Preserve existing suffixes (" - 24hs", " - 48hs", " - 72hs", " - CI", " - T0", " - T1", " - T2", etc.)

**Validation Rules**:
- raw_symbol: required, must exist in Tickers sheet
- pyrofex_symbol: auto-generated, follows transformation rules

### Excel Data Range  
**Purpose**: Worksheet ranges for different instrument types

**Attributes**:
- range_name: string (A1:A500, C1:C500, etc.)
- instrument_type: string (options, stocks, bonds, etc.)
- worksheet: string (HomeBroker, Tickers)
- start_row: int (starting row number)
- end_row: int (ending row number)

**Validation Rules**:
- range_name: required, valid Excel range format
- instrument_type: required, must match known types
- row numbers: positive integers

### Broker Connection
**Purpose**: Authenticated session with pyRofex API

**Attributes**:
- user: string (username credential)
- password: string (password credential) 
- account: string (account identifier)
- environment: string (LIVE environment)
- connection_status: string (connected, disconnected, error)
- last_error: string (last error message if any)

**State Transitions**:
- disconnected → connecting → connected
- connected → disconnected (on error)
- error → connecting (on retry)

**Validation Rules**:
- credentials: required, non-empty strings
- environment: must be valid pyRofex Environment value

### Market Data Handler
**Purpose**: Processing logic for format transformation

**Attributes**:
- source_format: object (pyRofex message structure)
- target_format: DataFrame (pandas structure for Excel)
- validation_errors: list (validation issues found)
- processing_status: string (success, failed, partial)

**Processing Rules**:
- Validate critical fields before transformation
- Map pyRofex field names to expected Excel columns
- Handle missing or invalid data gracefully
- Preserve data types for Excel compatibility

## Data Flow

### Input → Processing → Output
1. **WebSocket Message** (pyRofex format)
2. **Validation** (critical fields check)
3. **Transformation** (pyRofex → pandas DataFrame)
4. **Excel Update** (xlwings integration)

### Error Data Flow
1. **Invalid Data** → Log error, skip record
2. **Connection Error** → Exponential backoff reconnection
3. **Authentication Error** → Stop execution
4. **Excel Error** → Skip update, continue collection

## Relationships

### Symbol Management
- Tickers Sheet **contains** Raw Symbols
- Raw Symbols **transform to** PyRofex Symbols
- PyRofex Symbols **subscribe to** Market Data Stream

### Data Processing
- Market Data Stream **validates through** Data Validation
- Validated Data **transforms via** Market Data Handler
- Transformed Data **updates** Excel Data Ranges

### Connection Management
- Broker Connection **establishes** WebSocket Session
- WebSocket Session **receives** Market Data Stream
- Connection Errors **trigger** Reconnection Strategy

## Data Volume Estimates

### Symbol Counts (per instrument type)
- Options: ~100-200 symbols
- Stocks: ~50-100 symbols  
- Bonds: ~50-100 symbols
- Other instruments: ~50-150 symbols
- **Total**: ~500 symbols maximum

### Update Frequency
- WebSocket: Real-time as market changes
- Excel refresh: Every 2 seconds
- Connection retry: Exponential backoff (1s, 2s, 4s, 8s)

### Memory Considerations
- DataFrame size: ~500 rows × 15 columns × 8 bytes ≈ 60KB per update
- Historical data: Not persisted beyond current session
- Error logs: Minimal memory footprint