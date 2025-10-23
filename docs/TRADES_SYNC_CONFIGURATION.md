# Trades Synchronization Configuration Guide

## Overview

The EPGB Options application supports automatic synchronization of filled and partially-filled orders (trades) from the broker API to an Excel sheet. This feature can operate in two modes: **Periodic Sync** (default) or **Real-time Sync**.

## Configuration Variables

### Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `TRADES_SYNC_ENABLED` | `true` | Master switch to enable/disable trades synchronization completely |
| `TRADES_REALTIME_ENABLED` | `false` | Enable real-time WebSocket updates (if false, uses periodic REST sync) |
| `TRADES_SYNC_INTERVAL_SECONDS` | `300` | Interval in seconds for periodic sync (only used when `TRADES_REALTIME_ENABLED=false`) |
| `EXCEL_SHEET_TRADES` | `Trades` | Name of the Excel sheet where trades will be written |
| `TRADES_BATCH_SIZE` | `500` | Maximum number of rows to process in a single batch |

## Operating Modes

### Mode 1: Periodic Sync (Default - Recommended)

**Configuration:**
```env
TRADES_SYNC_ENABLED=true
TRADES_REALTIME_ENABLED=false
TRADES_SYNC_INTERVAL_SECONDS=300
```

**How it works:**
- Application performs an initial sync at startup
- Every `TRADES_SYNC_INTERVAL_SECONDS` seconds (default: 5 minutes), the application fetches all filled orders from the broker API via REST
- All filled orders are upserted to the Trades sheet (idempotent operation - safe to repeat)
- Lower overhead and resource usage
- Suitable for most use cases

**Advantages:**
- Lower CPU and memory usage
- More predictable behavior
- Less API calls to broker
- Easier to debug

**Disadvantages:**
- Higher latency (trades appear with up to N seconds delay)
- May miss very short-lived execution states

### Mode 2: Real-time Sync

**Configuration:**
```env
TRADES_SYNC_ENABLED=true
TRADES_REALTIME_ENABLED=true
TRADES_SYNC_INTERVAL_SECONDS=300  # Not used in this mode, but kept for fallback
```

**How it works:**
- Application performs an initial sync at startup
- Subscribes to order report WebSocket feed from broker
- Each time an order is filled or partially filled, the execution is immediately processed and upserted to Excel
- Near-instant updates (typically < 1 second latency)

**Advantages:**
- Immediate updates when trades occur
- Captures all execution state changes
- Best for active trading scenarios

**Disadvantages:**
- Higher CPU usage (constant WebSocket processing)
- More API calls to broker
- Slightly more complex error handling

### Mode 3: Disabled

**Configuration:**
```env
TRADES_SYNC_ENABLED=false
```

**How it works:**
- No trades synchronization is performed
- Trades sheet is not created or updated
- Minimal overhead

## Implementation Details

### Startup Behavior

Regardless of mode, the application always performs an initial sync at startup:
1. Fetches all existing filled orders from broker API (REST)
2. Processes and upserts them to the Trades sheet
3. Sets up periodic timer or WebSocket subscription based on configuration

### Idempotent Upsert

All trades operations use an idempotent upsert strategy with a composite key:
- **Key**: `(ExecutionID, OrderID, Account)`
- Duplicate trades are automatically merged
- Partial fills are updated to final fills without creating duplicate rows
- Audit columns track historical changes (`PreviousFilledQty`, `UpdateCount`, `Superseded`)

### Excel Integration

All Excel writes use **bulk range updates** per Constitution II:
- Single xlwings operation per upsert batch
- Entire DataFrame written in one call
- Optimal performance for large datasets

## Timing Considerations

### Periodic Sync Interval

Choose `TRADES_SYNC_INTERVAL_SECONDS` based on your needs:

| Use Case | Recommended Interval | Trade-offs |
|----------|---------------------|------------|
| Day trading / active | 60-120 seconds | More frequent updates, higher API load |
| Position trading | 300-600 seconds (5-10 min) | Balanced approach (default) |
| End-of-day reconciliation | 1800-3600 seconds (30-60 min) | Lower overhead, higher latency |

**Minimum**: 10 seconds (enforced by validation)

### Real-time Latency

In real-time mode:
- WebSocket event → Processing → Excel write: typically < 1 second
- Network latency: depends on connection quality
- Excel write overhead: ~50-200ms for bulk operations

## Troubleshooting

### Trades not appearing

1. Check that `TRADES_SYNC_ENABLED=true`
2. Verify broker credentials are correct
3. Check logs for errors: `logger.info` messages indicate sync status
4. Ensure the Excel workbook is open and writable

### High CPU usage

1. If using real-time mode, consider switching to periodic sync
2. Increase `TRADES_SYNC_INTERVAL_SECONDS` if using periodic mode
3. Check `TRADES_BATCH_SIZE` - lower values reduce memory but increase overhead

### Duplicate trades

This should not happen due to idempotent upsert, but if it does:
1. Check that `ExecutionID`, `OrderID`, and `Account` are all populated correctly
2. Review logs for warnings about missing keys
3. Verify pyRofex API is returning consistent execution IDs

### Missing trades

1. Verify that orders are actually filled (check broker platform)
2. In periodic mode, wait for next sync cycle
3. In real-time mode, check WebSocket subscription status in logs
4. Manually trigger sync by restarting application (performs startup sync)

## Examples

### Conservative Configuration (Low Overhead)

```env
TRADES_SYNC_ENABLED=true
TRADES_REALTIME_ENABLED=false
TRADES_SYNC_INTERVAL_SECONDS=600  # 10 minutes
TRADES_BATCH_SIZE=500
```

### Aggressive Configuration (Fastest Updates)

```env
TRADES_SYNC_ENABLED=true
TRADES_REALTIME_ENABLED=true
TRADES_BATCH_SIZE=500
```

### Development/Testing Configuration

```env
TRADES_SYNC_ENABLED=true
TRADES_REALTIME_ENABLED=false
TRADES_SYNC_INTERVAL_SECONDS=30  # Fast iteration
TRADES_BATCH_SIZE=100  # Smaller batches for testing
```

## Performance Metrics

Expected performance based on testing:

| Metric | Periodic Mode | Real-time Mode |
|--------|--------------|----------------|
| Startup sync (100 trades) | ~2-3 seconds | ~2-3 seconds |
| Incremental update latency | 10-600 seconds (configurable) | <1 second |
| Excel write overhead | ~50-200ms per batch | ~50-200ms per trade |
| CPU usage (idle) | Negligible | Low (WebSocket processing) |
| CPU usage (active trading) | Low (periodic bursts) | Moderate (continuous) |

## Logging

The application logs all trades sync operations:

```
✅ Sincronización inicial completa: {'inserted': 10, 'updated': 2, 'unchanged': 88}
⏱️  Periodic trades sync triggered (305s elapsed)
⚡ Real-time execution upserted: {'inserted': 1, 'updated': 0, 'unchanged': 0}
```

Monitor logs to verify sync behavior and troubleshoot issues.

## Migration Notes

If upgrading from a version without trades sync:
1. Update `.env` file with new variables (or use defaults)
2. Trades sheet will be auto-created on first run
3. All historical filled orders will be synced at startup
4. No manual migration required

## See Also

- [Feature Specification](../specs/003-trades-sheet-upsert/spec.md)
- [Implementation Plan](../specs/003-trades-sheet-upsert/plan.md)
- [Data Model](../specs/003-trades-sheet-upsert/data-model.md)
