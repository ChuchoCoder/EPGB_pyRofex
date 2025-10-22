# Quickstart: Trades Sheet Upsert

**Feature**: `003-trades-sheet-upsert`  
**Date**: 2025-10-22  
**Audience**: Developers implementing the trades ingestion feature

---

## Overview

This quickstart guides you through implementing the Trades Sheet Upsert feature, which automatically fetches filled/partially-filled executions from the pyRofex API and persists them to an Excel "Trades" sheet with idempotent upserts.

**Time to complete**: ~4 hours (implementation) + 2 hours (testing/validation)

---

## Prerequisites

- Python 3.9+ installed
- Existing EPGB Options codebase at `c:\git\EPGB_pyRofex`
- pyRofex API credentials configured (`.env` or `config/pyrofex_config.py`)
- Excel workbook open (`.xlsb` format) with xlwings
- Familiarity with pandas, xlwings, and pyRofex

---

## Phase 1: Configuration (15 min)

### Step 1.1: Add Trades Sheet Configuration

**File**: `src/epgb_options/config/excel_config.py`

Add the following configuration section:

```python
# Trades Sheet Configuration
EXCEL_SHEET_TRADES = os.getenv('EXCEL_SHEET_TRADES', 'Trades')
TRADES_HEADER_ROW = int(os.getenv('TRADES_HEADER_ROW', '1'))
TRADES_BATCH_SIZE = int(os.getenv('TRADES_BATCH_SIZE', '500'))
TRADES_SYNC_ENABLED = os.getenv('TRADES_SYNC_ENABLED', 'true').lower() == 'true'
TRADES_SYNC_INTERVAL_SECONDS = int(os.getenv('TRADES_SYNC_INTERVAL_SECONDS', '300'))  # 5 min

# Column mapping (Excel column letters)
TRADES_COLUMNS = {
    'ExecutionID': 'A',
    'OrderID': 'B',
    'Account': 'C',
    'Symbol': 'D',
    'Side': 'E',
    'Quantity': 'F',
    'Price': 'G',
    'FilledQty': 'H',
    'TimestampUTC': 'I',
    'Status': 'J',
    'ExecutionType': 'K',
    'Source': 'L',
    'PreviousFilledQty': 'M',
    'PreviousTimestampUTC': 'N',
    'Superseded': 'O',
    'CancelReason': 'P',
    'UpdateCount': 'Q',
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

Update `validate_excel_config()` to call `validate_trades_config()`:

```python
def validate_excel_config():
    """Validate all Excel configuration."""
    errors = []
    
    # Existing validations...
    
    # Add trades validation
    errors.extend(validate_trades_config())
    
    return errors
```

### Step 1.2: Update .env (Optional)

**File**: `.env` (project root)

```bash
# Trades Sheet Configuration
EXCEL_SHEET_TRADES=Trades
TRADES_BATCH_SIZE=500
TRADES_SYNC_ENABLED=true
TRADES_SYNC_INTERVAL_SECONDS=300
```

**Verify**: Run validation

```powershell
cd src/epgb_options/config
python excel_config.py
# Expected output: "✅ La configuración de Excel es válida"
```

---

## Phase 2: Create Trades Module (1.5 hours)

### Step 2.1: Module Structure

Create new directory and files:

```powershell
cd src/epgb_options
mkdir trades
cd trades
New-Item -ItemType File __init__.py, execution_fetcher.py, trades_processor.py, trades_upsert.py
```

### Step 2.2: Execution Fetcher

**File**: `src/epgb_options/trades/execution_fetcher.py`

**Purpose**: Fetch executions from pyRofex (WebSocket + REST).

**Key implementation**:

```python
"""
Execution Fetcher Module

Fetches filled/partially-filled executions from pyRofex API.
Supports both real-time WebSocket subscriptions and REST backfill.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Callable
from queue import Queue
import pyRofex

from ..utils.logging import get_logger

logger = get_logger(__name__)


class ExecutionFetcher:
    """Fetches executions from pyRofex API."""
    
    def __init__(self, api_client):
        """
        Initialize execution fetcher.
        
        Args:
            api_client: pyRofexClient instance (from market_data.api_client)
        """
        self.api_client = api_client
        self.execution_queue = Queue()
        self._handler_registered = False
    
    def subscribe_order_reports(self, callback: Optional[Callable] = None):
        """
        Subscribe to real-time order reports via WebSocket.
        
        Args:
            callback: Optional callback function for processing executions
        """
        if not self.api_client.is_initialized:
            raise RuntimeError("API client not initialized")
        
        # Register handler
        def order_report_handler(message):
            try:
                execution = self._parse_order_report(message)
                if execution:
                    if callback:
                        callback(execution)
                    else:
                        self.execution_queue.put(execution)
            except Exception as e:
                logger.error(f"Error in order report handler: {e}", exc_info=True)
        
        pyRofex.add_websocket_order_report_handler(order_report_handler)
        self._handler_registered = True
        
        # Subscribe
        pyRofex.order_report_subscription()
        logger.info("Subscribed to order reports")
    
    def fetch_historical_executions(self, from_date: datetime, to_date: Optional[datetime] = None, 
                                   batch_size: int = 500) -> List[Dict]:
        """
        Fetch historical executions via REST API.
        
        Args:
            from_date: Start date (UTC)
            to_date: End date (UTC), defaults to now
            batch_size: Max executions per batch
            
        Returns:
            List of execution dicts
        """
        if to_date is None:
            to_date = datetime.now(timezone.utc)
        
        # Implementation: Call pyRofex.get_all_orders()
        # Filter for FILLED/PARTIALLY_FILLED, extract executions
        # See contracts/pyrofex-trades-api.md for details
        
        # Placeholder return
        return []
    
    def _parse_order_report(self, message: Dict) -> Optional[Dict]:
        """
        Parse order report message into execution dict.
        
        Args:
            message: Raw order report from pyRofex WebSocket
            
        Returns:
            Execution dict or None if invalid
        """
        if message.get('type') != 'orderReport':
            return None
        
        order_report = message.get('orderReport')
        if not order_report:
            logger.error("Missing orderReport in message")
            return None
        
        # Filter: only process filled/partially filled orders
        status = order_report.get('ordStatus')
        if status not in ['FILLED', 'PARTIALLY_FILLED']:
            logger.debug(f"Skipping order with status: {status}")
            return None
        
        # Extract execution data
        execution = {
            'ExecutionID': order_report.get('execId', ''),
            'OrderID': order_report.get('orderId'),
            'Account': order_report.get('account'),
            'Symbol': order_report.get('instrumentId', {}).get('symbol'),
            'Side': order_report.get('side'),
            'Quantity': order_report.get('orderQty'),
            'Price': order_report.get('price'),
            'FilledQty': order_report.get('cumQty'),
            'LastQty': order_report.get('lastQty'),
            'LastPx': order_report.get('lastPx'),
            'TimestampUTC': order_report.get('transactTime'),
            'Status': status,
            'ExecutionType': order_report.get('execType'),
            'Source': 'pyRofex'
        }
        
        # Validate required fields
        required = ['OrderID', 'Account', 'Symbol', 'Side', 'Quantity', 
                   'FilledQty', 'TimestampUTC']
        missing = [f for f in required if not execution.get(f)]
        if missing:
            logger.error(f"Missing required fields: {missing}")
            return None
        
        # Fallback for missing ExecutionID
        if not execution['ExecutionID']:
            execution['ExecutionID'] = f"{execution['OrderID']}_{execution['TimestampUTC']}_{execution['Account']}"
            logger.warning(f"Using fallback ExecutionID: {execution['ExecutionID']}")
        
        return execution
```

**Action**: Implement the full `fetch_historical_executions()` method using REST API (refer to `contracts/pyrofex-trades-api.md`).

### Step 2.3: Trades Processor

**File**: `src/epgb_options/trades/trades_processor.py`

**Purpose**: Convert raw executions to DataFrame, validate, sort.

**Skeleton**:

```python
"""
Trades Processor Module

Processes raw execution dicts into validated pandas DataFrame.
"""

import pandas as pd
from datetime import datetime
from typing import List, Dict

from ..utils.logging import get_logger
from ..utils.validation import validate_pandas_dataframe

logger = get_logger(__name__)


class TradesProcessor:
    """Processes executions into DataFrame."""
    
    def process_executions(self, executions: List[Dict]) -> pd.DataFrame:
        """
        Convert executions to DataFrame with validation.
        
        Args:
            executions: List of execution dicts
            
        Returns:
            Validated DataFrame with composite index
        """
        if not executions:
            logger.warning("No executions to process")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(executions)
        
        # Parse timestamps
        df['TimestampUTC'] = pd.to_datetime(df['TimestampUTC'], utc=True)
        
        # Sort by timestamp (handle out-of-order events)
        df.sort_values('TimestampUTC', inplace=True)
        
        # Set composite index
        df.set_index(['ExecutionID', 'OrderID', 'Account'], inplace=True)
        
        # Validate
        if not validate_pandas_dataframe(df):
            logger.error("DataFrame validation failed")
            return pd.DataFrame()
        
        logger.info(f"Processed {len(df)} executions")
        return df
```

**Action**: Extend with data type conversions, additional validations.

### Step 2.4: Trades Upsert

**File**: `src/epgb_options/trades/trades_upsert.py`

**Purpose**: Idempotent upsert to Excel Trades sheet (BULK RANGE UPDATE).

**Critical implementation** (follows Constitution II):

```python
"""
Trades Upsert Module

Idempotent upsert of executions to Excel Trades sheet.
MUST use bulk range updates per Constitution II.
"""

import pandas as pd
import xlwings as xw
from typing import Dict

from ..config.excel_config import TRADES_COLUMNS, EXCEL_SHEET_TRADES
from ..utils.logging import get_logger
from ..utils.helpers import get_excel_safe_value

logger = get_logger(__name__)


class TradesUpserter:
    """Handles upsert operations for Trades sheet."""
    
    def __init__(self, workbook: xw.Book):
        """
        Initialize upserter.
        
        Args:
            workbook: xlwings Workbook object
        """
        self.workbook = workbook
        self.sheet = self._get_or_create_trades_sheet()
    
    def upsert_executions(self, new_executions_df: pd.DataFrame) -> Dict[str, int]:
        """
        Idempotent upsert of executions to Trades sheet.
        Uses BULK RANGE UPDATE (single xlwings write operation).
        
        Args:
            new_executions_df: DataFrame with executions (composite index set)
            
        Returns:
            Stats dict: {'inserted': int, 'updated': int, 'unchanged': int}
        """
        if new_executions_df.empty:
            logger.info("No executions to upsert")
            return {'inserted': 0, 'updated': 0, 'unchanged': 0}
        
        # 1. Read existing trades (BULK READ)
        existing_df = self._read_existing_trades()
        
        # 2. Merge new with existing (pandas merge)
        merged = self._merge_executions(existing_df, new_executions_df)
        
        # 3. Build final DataFrame with audit columns
        final_df = self._build_final_with_audit(merged)
        
        # 4. CRITICAL: BULK WRITE to Excel (single operation)
        self._write_bulk_to_excel(final_df)
        
        # 5. Calculate stats
        stats = self._calculate_stats(merged)
        logger.info(f"Upsert complete: {stats}")
        return stats
    
    def _read_existing_trades(self) -> pd.DataFrame:
        """Read existing Trades sheet data (bulk read)."""
        try:
            # Read entire table starting from row 2 (skip header)
            data_range = self.sheet.range('A2').expand('table')
            if data_range.value is None:
                # Empty sheet
                return pd.DataFrame(columns=list(TRADES_COLUMNS.keys()))
            
            # Convert to DataFrame
            df = pd.DataFrame(data_range.value, columns=list(TRADES_COLUMNS.keys()))
            
            # Set composite index
            df.set_index(['ExecutionID', 'OrderID', 'Account'], inplace=True)
            
            logger.debug(f"Read {len(df)} existing trades")
            return df
            
        except Exception as e:
            logger.error(f"Error reading existing trades: {e}")
            return pd.DataFrame(columns=list(TRADES_COLUMNS.keys()))
    
    def _merge_executions(self, existing: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
        """Merge existing and new executions with indicator."""
        # Merge with indicator to identify inserts/updates
        merged = existing.merge(
            new,
            how='outer',
            left_index=True,
            right_index=True,
            indicator=True,
            suffixes=('_old', '_new')
        )
        return merged
    
    def _build_final_with_audit(self, merged: pd.DataFrame) -> pd.DataFrame:
        """Build final DataFrame with audit columns populated."""
        # Implementation: Iterate through merged rows
        # For '_merge' == 'both': populate audit columns
        # For '_merge' == 'right_only': new insert (audit = NULL)
        # Return final DataFrame with all columns
        
        # Placeholder
        return merged
    
    def _write_bulk_to_excel(self, df: pd.DataFrame):
        """
        CRITICAL: Bulk write entire DataFrame to Excel in SINGLE operation.
        Per Constitution II, individual cell writes are PROHIBITED.
        """
        try:
            # Reset index to include composite key columns
            df_reset = df.reset_index()
            
            # Ensure column order matches TRADES_COLUMNS
            column_order = list(TRADES_COLUMNS.keys())
            df_ordered = df_reset[column_order]
            
            # Convert to 2D array for xlwings
            data = df_ordered.values.tolist()
            
            # Calculate range (A2 to Q{n})
            num_rows = len(data)
            last_col = 'Q'  # 17 columns (A-Q)
            end_row = num_rows + 1  # +1 for header row
            
            # SINGLE BULK WRITE
            self.sheet.range(f'A2:{last_col}{end_row}').value = data
            
            logger.info(f"✅ Bulk write: {num_rows} rows to Excel (A2:{last_col}{end_row})")
            
        except Exception as e:
            logger.error(f"Error in bulk write: {e}", exc_info=True)
            raise
    
    def _get_or_create_trades_sheet(self) -> xw.Sheet:
        """Get or create Trades sheet in workbook."""
        try:
            sheet = self.workbook.sheets(EXCEL_SHEET_TRADES)
            logger.debug(f"Trades sheet '{EXCEL_SHEET_TRADES}' found")
        except Exception:
            # Create sheet
            sheet = self.workbook.sheets.add(EXCEL_SHEET_TRADES)
            self._create_headers(sheet)
            logger.info(f"Created new Trades sheet: '{EXCEL_SHEET_TRADES}'")
        
        return sheet
    
    def _create_headers(self, sheet: xw.Sheet):
        """Create header row in new Trades sheet."""
        headers = list(TRADES_COLUMNS.keys())
        sheet.range('A1').value = headers
        sheet.range('A1:Q1').font.bold = True
        logger.debug("Trades sheet headers created")
```

**Action**: Complete `_build_final_with_audit()` logic (populate audit columns for updated rows).

### Step 2.5: Module Exports

**File**: `src/epgb_options/trades/__init__.py`

```python
"""
Trades Module

Provides execution fetching, processing, and upsert for Trades sheet.
"""

from .execution_fetcher import ExecutionFetcher
from .trades_processor import TradesProcessor
from .trades_upsert import TradesUpserter

__all__ = [
    'ExecutionFetcher',
    'TradesProcessor',
    'TradesUpserter',
]
```

---

## Phase 3: Integration (1 hour)

### Step 3.1: Update API Client

**File**: `src/epgb_options/market_data/api_client.py`

Add method to enable order report subscriptions:

```python
def subscribe_order_reports(self):
    """Subscribe to order reports via WebSocket."""
    if not self.is_initialized:
        raise RuntimeError("Client not initialized")
    
    pyRofex.order_report_subscription()
    logger.info("Subscribed to order reports")
```

### Step 3.2: Update Main Script

**File**: `src/epgb_options/main.py`

Integrate trades ingestion:

```python
from .trades import ExecutionFetcher, TradesProcessor, TradesUpserter
from .config.excel_config import TRADES_SYNC_ENABLED, TRADES_SYNC_INTERVAL_SECONDS

# In main() function, after market data subscription:

if TRADES_SYNC_ENABLED:
    logger.info("Trades sync enabled, initializing...")
    
    # Initialize trades components
    execution_fetcher = ExecutionFetcher(api_client)
    trades_processor = TradesProcessor()
    trades_upserter = TradesUpserter(workbook)
    
    # Subscribe to order reports
    def on_execution(execution):
        """Callback for new executions."""
        # Process and upsert
        df = trades_processor.process_executions([execution])
        if not df.empty:
            trades_upserter.upsert_executions(df)
    
    execution_fetcher.subscribe_order_reports(callback=on_execution)
    logger.info("Trades ingestion active")
```

---

## Phase 4: Testing (2 hours)

### Step 4.1: Unit Tests (Optional per Constitution)

**File**: `tests/test_trades_processor.py`

```python
import pytest
from src.epgb_options.trades import TradesProcessor

def test_process_executions_empty():
    processor = TradesProcessor()
    df = processor.process_executions([])
    assert df.empty

def test_process_executions_valid():
    processor = TradesProcessor()
    executions = [
        {
            'ExecutionID': 'exec_1',
            'OrderID': 'order_1',
            'Account': 'ACC123',
            'Symbol': 'GGAL - 24hs',
            'Side': 'BUY',
            'Quantity': 100,
            'Price': 1500.0,
            'FilledQty': 50,
            'TimestampUTC': '2025-10-22T10:00:00Z',
            'Status': 'PARTIALLY_FILLED',
            'ExecutionType': 'TRADE',
            'Source': 'pyRofex'
        }
    ]
    df = processor.process_executions(executions)
    assert len(df) == 1
    assert df.index.names == ['ExecutionID', 'OrderID', 'Account']
```

**Run tests**:

```powershell
cd c:\git\EPGB_pyRofex
pytest tests/test_trades_processor.py -v
```

### Step 4.2: Manual Integration Test

1. **Start application** with trades sync enabled
2. **Place test order** via broker (if in test environment)
3. **Verify Trades sheet** updates automatically
4. **Check logs** for upsert stats

**Expected logs**:

```
INFO: Subscribed to order reports
INFO: Processed 1 executions
INFO: ✅ Bulk write: 1 rows to Excel (A2:Q2)
INFO: Upsert complete: {'inserted': 1, 'updated': 0, 'unchanged': 0}
```

---

## Phase 5: Validation (30 min)

### Validation Checklist

- [ ] Configuration validates successfully (`python config/excel_config.py`)
- [ ] Trades sheet auto-created on first run
- [ ] Headers present in row 1 (columns A-Q)
- [ ] New executions inserted correctly
- [ ] Partial→final transitions update existing row with audit columns
- [ ] Duplicate events result in no-op (unchanged count increments)
- [ ] Excel updates use bulk range writes (check logs for "Bulk write")
- [ ] No individual cell loops (verify via code review)
- [ ] Sync completes within 10 seconds for normal volumes
- [ ] Application logs summary stats after each upsert

---

## Troubleshooting

### Issue: "Trades sheet not found"

**Solution**: Ensure `EXCEL_SHEET_TRADES` config matches sheet name in workbook. Auto-creation logic will create if missing.

### Issue: "Bulk write fails with COM error"

**Solution**: Check Excel workbook is open and not locked. Verify xlwings connection. Restart Excel if necessary.

### Issue: "No executions received from WebSocket"

**Solution**: Verify pyRofex credentials, check WebSocket connection status, review error logs. Use REST API as fallback.

### Issue: "Duplicate rows in Excel"

**Solution**: Check composite key logic in merge. Ensure index is set correctly before upsert. Review deduplication in `_merge_executions()`.

---

## Next Steps

After successful implementation:

1. **Deploy to production** — Update `.env` with production credentials
2. **Monitor performance** — Track upsert times, log stats
3. **Backfill historical trades** — Run manual backfill for past 30 days
4. **Document for users** — Create user guide for Trades sheet usage

---

## Resources

- **Feature Spec**: [spec.md](./spec.md)
- **Data Model**: [data-model.md](./data-model.md)
- **API Contract**: [contracts/pyrofex-trades-api.md](./contracts/pyrofex-trades-api.md)
- **Research**: [research.md](./research.md)
- **Constitution**: [.specify/memory/constitution.md](../../.specify/memory/constitution.md)

---

**Quickstart Version**: 1.0  
**Last Updated**: 2025-10-22  
**Estimated Implementation Time**: 4-6 hours
