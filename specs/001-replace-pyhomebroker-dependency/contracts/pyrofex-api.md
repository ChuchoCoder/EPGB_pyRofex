# PyRofex WebSocket API Contract

## Authentication Contract

### Initialize Connection
```
pyRofex._set_environment_parameter("url", "https://api.cocos.xoms.com.ar/", Environment.LIVE)
pyRofex._set_environment_parameter("ws", "wss://api.cocos.xoms.com.ar/", Environment.LIVE)
pyRofex.initialize(user="username", password="password", account="account", environment=pyRofex.Environment.LIVE)
```

**Expected Response**: Success or authentication error
**Error Handling**: Stop execution on failure per FR-003

## WebSocket Connection Contract

### Initialize WebSocket
```
pyRofex.init_websocket_connection(
    market_data_handler=market_data_handler,
    error_handler=error_handler,
    exception_handler=exception_handler
)
```

**Expected Response**: Connection established or connection error
**Error Handling**: Exponential backoff reconnection per FR-010

## Market Data Subscription Contract

### Subscribe to Instruments
```
pyRofex.market_data_subscription(
    tickers=["MERV - XMEV - YPFD - 24hs", "MERV - XMEV - GGAL - CI"],
    entries=[pyRofex.MarketDataEntry.BIDS, pyRofex.MarketDataEntry.OFFERS, pyRofex.MarketDataEntry.LAST]
)
```

**Input**: 
- tickers: List of transformed instrument symbols
- entries: Market data types to subscribe to

**Expected Response**: Subscription confirmation or error
**Error Handling**: Mark invalid symbols as unavailable per FR-013

## Market Data Message Contract

### Expected Message Structure
```json
{
  "symbol": "MERV - XMEV - YPFD - 24hs",
  "bid": 150.50,
  "ask": 151.00,
  "bid_size": 1000,
  "ask_size": 500,
  "last": 150.75,
  "change": 0.025,
  "open": 150.25,
  "high": 151.50,
  "low": 149.80,
  "previous_close": 150.00,
  "turnover": 1500000.0,
  "volume": 10000,
  "operations": 45,
  "datetime": "2025-09-27T15:30:45.123Z"
}
```

**Validation Requirements** (per FR-008):
- symbol: required, non-empty string
- price fields (bid, ask, last): required, positive float
- Other fields: optional, validated if present

**Transformation**: Map to pandas DataFrame compatible with existing Excel structure

## Error Message Contract

### WebSocket Error Messages
```json
{
  "error": "Connection failed",
  "code": "WS_CONNECTION_ERROR",
  "timestamp": "2025-09-27T15:30:45.123Z"
}
```

**Handling**: Log error and trigger reconnection strategy

### Authentication Error Messages  
```json
{
  "error": "Invalid credentials",
  "code": "AUTH_FAILED", 
  "timestamp": "2025-09-27T15:30:45.123Z"
}
```

**Handling**: Stop execution per FR-003

### Invalid Symbol Error Messages
```json
{
  "error": "Symbol not found",
  "symbol": "INVALID_SYMBOL",
  "code": "SYMBOL_NOT_FOUND",
  "timestamp": "2025-09-27T15:30:45.123Z"
}
```

**Handling**: Mark as unavailable in Excel per FR-013