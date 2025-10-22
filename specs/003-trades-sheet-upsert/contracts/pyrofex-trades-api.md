# pyRofex Trades API Contract

**Feature**: `003-trades-sheet-upsert`  
**Date**: 2025-10-22  
**Purpose**: Define the contract between our application and the pyRofex API for fetching and subscribing to order/execution data.

---

## Overview

This document specifies the pyRofex API methods used for trades ingestion, including:

1. **WebSocket Subscriptions** — Real-time order status updates
2. **REST API Methods** — Historical backfill and reconciliation
3. **Message Formats** — Expected request/response structures
4. **Error Handling** — API failure modes and retry strategies

**pyRofex Version**: >= 0.5.0

---

## 1. WebSocket: Real-time Order Updates

### 1.1 Subscribe to Order Reports

**Purpose**: Receive real-time notifications of order status changes and execution events.

**Method**: `pyRofex.order_report_subscription()`

**Parameters**:
- None (subscribes to all orders for configured account)

**Return**: None (asynchronous subscription)

**Handler Registration**:

```python
import pyRofex

def order_report_handler(message):
    """
    Handle incoming order report messages.
    
    Args:
        message (dict): Order report message from pyRofex WebSocket
    """
    # Process message (see Message Format below)
    pass

# Register handler
pyRofex.add_websocket_order_report_handler(order_report_handler)

# Subscribe
pyRofex.order_report_subscription()
```

**Message Format** (WebSocket incoming):

```json
{
  "type": "orderReport",
  "orderReport": {
    "clOrdId": "user_generated_order_id",
    "orderId": "broker_order_12345",
    "account": "ACCOUNT123",
    "instrumentId": {
      "marketId": "MERV",
      "symbol": "GGAL - 24hs"
    },
    "side": "BUY",
    "orderQty": 100,
    "ordType": "LIMIT",
    "price": 1500.0,
    "ordStatus": "PARTIALLY_FILLED",
    "cumQty": 50,
    "leavesQty": 50,
    "lastQty": 25,
    "lastPx": 1499.0,
    "avgPx": 1499.5,
    "transactTime": "2025-10-22T14:30:45.123Z",
    "execType": "TRADE",
    "execId": "exec_789",
    "text": "Execution details"
  }
}
```

**Field Mapping** (pyRofex → Our Execution Entity):

| Our Field | pyRofex Field | Transform |
|-----------|---------------|-----------|
| `ExecutionID` | `execId` | Direct copy |
| `OrderID` | `orderId` | Direct copy |
| `Account` | `account` | Direct copy |
| `Symbol` | `instrumentId.symbol` | Direct copy |
| `Side` | `side` | Direct copy (BUY/SELL) |
| `Quantity` | `orderQty` | Direct copy |
| `Price` | `price` | Direct copy |
| `FilledQty` | `cumQty` | Direct copy (cumulative filled) |
| `LastQty` | `lastQty` | Direct copy (this execution's qty) |
| `LastPx` | `lastPx` | Direct copy (this execution's price) |
| `TimestampUTC` | `transactTime` | Parse ISO 8601 → datetime UTC |
| `Status` | `ordStatus` | Direct copy (enum value) |
| `ExecutionType` | `execType` | Direct copy (enum value) |
| `Source` | — | Constant "pyRofex" |

**Order Status Values** (from `ordStatus`):

- `NEW` — Order accepted, not yet filled
- `PARTIALLY_FILLED` — Order partially executed
- `FILLED` — Order fully executed
- `CANCELED` — Order canceled
- `REJECTED` — Order rejected
- `EXPIRED` — Order expired

**Execution Type Values** (from `execType`):

- `NEW` — Order acceptance
- `TRADE` — Execution occurred (fill)
- `CANCELED` — Order cancellation
- `REJECTED` — Order rejection
- `EXPIRED` — Order expiration

**Error Handling**:

1. **WebSocket disconnection**:
   - pyRofex automatically attempts reconnection
   - Application should register error handler to log disconnections
   - Use REST API for reconciliation after reconnection

2. **Malformed messages**:
   - Log warning with full message payload
   - Skip message (do not crash handler)
   - Increment error counter for monitoring

3. **Missing fields**:
   - If `execId` missing → use fallback composite key `(orderId, transactTime, account)`
   - If other required fields missing → log error and skip message

**Example Handler Implementation**:

```python
import pyRofex
from ..utils.logging import get_logger

logger = get_logger(__name__)

def order_report_handler(message):
    """Process incoming order report from pyRofex WebSocket."""
    try:
        if message.get('type') != 'orderReport':
            logger.warning(f"Unexpected message type: {message.get('type')}")
            return
        
        order_report = message.get('orderReport')
        if not order_report:
            logger.error("Missing orderReport in message")
            return
        
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
            'Status': order_report.get('ordStatus'),
            'ExecutionType': order_report.get('execType'),
            'Source': 'pyRofex'
        }
        
        # Validate required fields
        required_fields = ['OrderID', 'Account', 'Symbol', 'Side', 'Quantity', 
                          'FilledQty', 'TimestampUTC', 'Status']
        missing = [f for f in required_fields if not execution.get(f)]
        if missing:
            logger.error(f"Missing required fields in order report: {missing}")
            return
        
        # Queue for processing (decoupled from WebSocket thread)
        execution_queue.put(execution)
        
    except Exception as e:
        logger.error(f"Error processing order report: {e}", exc_info=True)
```

---

## 2. REST API: Historical Backfill

### 2.1 Get Order Status

**Purpose**: Fetch historical order status and executions for backfill/reconciliation.

**Method**: `pyRofex.get_order_status(account, order_id)`

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `account` | string | Yes | Broker account identifier |
| `order_id` | string | Yes | Specific order ID to fetch |

**Return**: Dict with order details and executions

**Response Format**:

```json
{
  "status": "OK",
  "order": {
    "clOrdId": "user_order_123",
    "orderId": "broker_order_456",
    "account": "ACCOUNT123",
    "instrumentId": {
      "marketId": "MERV",
      "symbol": "GGAL - 24hs"
    },
    "side": "BUY",
    "orderQty": 100,
    "ordType": "LIMIT",
    "price": 1500.0,
    "ordStatus": "FILLED",
    "cumQty": 100,
    "leavesQty": 0,
    "avgPx": 1499.25,
    "transactTime": "2025-10-22T15:00:00.000Z",
    "executions": [
      {
        "execId": "exec_789",
        "lastQty": 25,
        "lastPx": 1499.0,
        "transactTime": "2025-10-22T14:30:45.123Z"
      },
      {
        "execId": "exec_790",
        "lastQty": 75,
        "lastPx": 1499.33,
        "transactTime": "2025-10-22T14:35:12.456Z"
      }
    ]
  }
}
```

**Usage Example**:

```python
import pyRofex

# Fetch specific order
response = pyRofex.get_order_status(account="ACCOUNT123", order_id="broker_order_456")

if response['status'] == 'OK':
    order = response['order']
    # Process order executions
    for execution in order.get('executions', []):
        # Build execution entity
        pass
else:
    logger.error(f"Failed to fetch order: {response}")
```

**Error Handling**:

- **Status != "OK"**: Log error, skip order
- **Network errors**: Retry with exponential backoff (max 3 retries)
- **Order not found**: Log warning, continue (order may be too old)

---

### 2.2 Get All Orders (Backfill)

**Purpose**: Fetch all orders for an account within a date range for bulk backfill.

**Method**: `pyRofex.get_all_orders(account, from_date, to_date)`

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `account` | string | Yes | Broker account identifier |
| `from_date` | string | No | Start date (ISO 8601) | Default: 30 days ago |
| `to_date` | string | No | End date (ISO 8601) | Default: now |

**Return**: List of orders with executions

**Response Format**:

```json
{
  "status": "OK",
  "orders": [
    {
      "orderId": "order_1",
      "ordStatus": "FILLED",
      "cumQty": 50,
      "transactTime": "2025-10-20T10:00:00.000Z",
      "executions": [...]
    },
    {
      "orderId": "order_2",
      "ordStatus": "PARTIALLY_FILLED",
      "cumQty": 25,
      "transactTime": "2025-10-21T11:30:00.000Z",
      "executions": [...]
    }
  ]
}
```

**Pagination** (if supported by pyRofex):

- **Note**: As of pyRofex 0.5.0, pagination may not be supported for `get_all_orders()`
- **Workaround**: Batch by date ranges (1 day at a time) to limit response size
- **Alternative**: Use `get_order_status()` per order if order IDs are known

**Usage Example**:

```python
from datetime import datetime, timedelta, timezone

# Backfill last 30 days
from_date = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
to_date = datetime.now(timezone.utc).isoformat()

response = pyRofex.get_all_orders(
    account="ACCOUNT123",
    from_date=from_date,
    to_date=to_date
)

if response['status'] == 'OK':
    for order in response['orders']:
        # Filter for filled/partially filled orders
        if order['ordStatus'] in ['FILLED', 'PARTIALLY_FILLED']:
            # Process executions
            for execution in order.get('executions', []):
                # Build execution entity
                pass
```

**Batching Strategy** (for large backfills):

1. Split date range into daily chunks
2. Process each chunk sequentially
3. Update checkpoint after each successful chunk
4. If error, retry current chunk (resume from checkpoint)

**Error Handling**:

- **API rate limits**: Implement retry with exponential backoff (start: 1s, max: 60s)
- **Timeout**: Set request timeout to 30s, retry on timeout
- **Large responses**: Process in batches if response > 10MB

---

## 3. Error Handler Registration

### 3.1 WebSocket Error Handler

**Purpose**: Handle WebSocket errors and disconnections.

**Method**: `pyRofex.add_websocket_error_handler(handler)`

**Handler Signature**:

```python
def websocket_error_handler(error):
    """
    Handle WebSocket errors.
    
    Args:
        error (Exception): Error object from pyRofex WebSocket
    """
    logger.error(f"WebSocket error: {error}", exc_info=True)
    # Trigger reconciliation via REST API
```

**Registration**:

```python
pyRofex.add_websocket_error_handler(websocket_error_handler)
```

---

### 3.2 WebSocket Exception Handler

**Purpose**: Handle exceptions during WebSocket message processing.

**Method**: `pyRofex.set_websocket_exception_handler(handler)`

**Handler Signature**:

```python
def websocket_exception_handler(exception):
    """
    Handle exceptions in WebSocket handlers.
    
    Args:
        exception (Exception): Exception raised in handler
    """
    logger.critical(f"WebSocket handler exception: {exception}", exc_info=True)
    # Alert operations team
```

**Registration**:

```python
pyRofex.set_websocket_exception_handler(websocket_exception_handler)
```

---

## 4. Integration Workflow

### Real-time Subscription Flow

```
1. Application starts
   ↓
2. Initialize pyRofex client (existing api_client.py)
   ↓
3. Register order report handler
   pyRofex.add_websocket_order_report_handler(handler)
   ↓
4. Register error handlers
   pyRofex.add_websocket_error_handler(error_handler)
   pyRofex.set_websocket_exception_handler(exception_handler)
   ↓
5. Subscribe to order reports
   pyRofex.order_report_subscription()
   ↓
6. Handler receives messages asynchronously
   ↓
7. Queue executions for batch processing
   ↓
8. Periodic batch upsert to Excel (every 5 min or N executions)
```

### Historical Backfill Flow

```
1. Check last checkpoint (Excel cell Z1)
   ↓
2. If checkpoint missing → set to 30 days ago
   ↓
3. Call pyRofex.get_all_orders(from_date=checkpoint)
   ↓
4. Filter for FILLED/PARTIALLY_FILLED orders
   ↓
5. Extract executions
   ↓
6. Batch upsert to Excel (500 rows at a time)
   ↓
7. Update checkpoint after each batch
   ↓
8. Repeat until all orders processed
```

### Reconciliation Flow (after WebSocket disconnect)

```
1. WebSocket disconnect detected
   ↓
2. Log error, mark last known timestamp
   ↓
3. pyRofex auto-reconnects (library behavior)
   ↓
4. After reconnection, fetch orders via REST API
   from_date = last_known_timestamp
   to_date = now
   ↓
5. Process missed executions
   ↓
6. Resume normal WebSocket subscription
```

---

## 5. API Limitations & Workarounds

### 5.1 Missing Execution IDs

**Problem**: Some broker events may not include `execId` field.

**Workaround**: Use fallback composite key `(orderId, transactTime, account)`.

**Implementation**:

```python
exec_id = order_report.get('execId')
if not exec_id:
    # Fallback: hash of order details
    exec_id = f"{order_report['orderId']}_{order_report['transactTime']}_{order_report['account']}"
    logger.warning(f"Missing execId, using fallback: {exec_id}")
```

---

### 5.2 Rate Limits

**Problem**: pyRofex API may have undocumented rate limits.

**Mitigation**:

- Implement exponential backoff for REST calls
- Batch operations (avoid rapid-fire individual order queries)
- Use WebSocket for real-time (no rate limits on subscriptions)

**Rate Limit Detection**:

```python
if response.get('status') == 'RATE_LIMIT_EXCEEDED':
    sleep_time = 2 ** retry_count  # Exponential backoff
    logger.warning(f"Rate limit hit, sleeping {sleep_time}s")
    time.sleep(sleep_time)
    retry_count += 1
```

---

### 5.3 Execution Details Not Included

**Problem**: Some order status responses may not include detailed `executions` array.

**Workaround**: Derive execution from order-level fields (`cumQty`, `lastQty`, `lastPx`).

**Implementation**:

```python
executions = order.get('executions', [])
if not executions and order['ordStatus'] in ['FILLED', 'PARTIALLY_FILLED']:
    # Synthesize execution from order-level data
    synthetic_execution = {
        'execId': f"{order['orderId']}_synthetic",
        'lastQty': order.get('lastQty', order.get('cumQty')),
        'lastPx': order.get('lastPx', order.get('avgPx')),
        'transactTime': order['transactTime']
    }
    executions = [synthetic_execution]
    logger.info(f"Synthesized execution for order {order['orderId']}")
```

---

## 6. Testing & Validation

### Contract Validation Checklist

- [ ] WebSocket handler receives order reports for filled orders
- [ ] All required fields present in order report messages
- [ ] REST API returns historical orders within date range
- [ ] Error handler invoked on WebSocket disconnect
- [ ] Execution IDs are unique (or fallback key used)
- [ ] Timestamps are in UTC ISO 8601 format
- [ ] Order status values match documented enums
- [ ] Partial fills update `cumQty` correctly

### Mock Data for Testing

**Sample Order Report** (for unit tests):

```json
{
  "type": "orderReport",
  "orderReport": {
    "clOrdId": "test_order_001",
    "orderId": "MOCK_ORDER_123",
    "account": "TEST_ACCOUNT",
    "instrumentId": {"symbol": "TEST - 24hs"},
    "side": "BUY",
    "orderQty": 100,
    "ordType": "LIMIT",
    "price": 1000.0,
    "ordStatus": "PARTIALLY_FILLED",
    "cumQty": 50,
    "leavesQty": 50,
    "lastQty": 50,
    "lastPx": 999.0,
    "avgPx": 999.0,
    "transactTime": "2025-10-22T12:00:00.000Z",
    "execType": "TRADE",
    "execId": "MOCK_EXEC_001",
    "text": "Test execution"
  }
}
```

---

## 7. API Reference

**pyRofex Documentation**: [https://github.com/MatbaRofex/pyRofex](https://github.com/MatbaRofex/pyRofex)

**Methods Used**:

| Method | Purpose | Type |
|--------|---------|------|
| `pyRofex.order_report_subscription()` | Subscribe to order updates | WebSocket |
| `pyRofex.add_websocket_order_report_handler(handler)` | Register order handler | WebSocket |
| `pyRofex.add_websocket_error_handler(handler)` | Register error handler | WebSocket |
| `pyRofex.set_websocket_exception_handler(handler)` | Register exception handler | WebSocket |
| `pyRofex.get_order_status(account, order_id)` | Fetch single order | REST |
| `pyRofex.get_all_orders(account, from_date, to_date)` | Fetch orders in date range | REST |

---

**Contract Version**: 1.0  
**Last Updated**: 2025-10-22  
**Status**: Draft — pending validation against pyRofex 0.5.0+ in production
