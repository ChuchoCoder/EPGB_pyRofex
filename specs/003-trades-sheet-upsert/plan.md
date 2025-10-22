# Implementation Plan: Trades Sheet Upsert

**Branch**: `003-trades-sheet-upsert` | **Date**: 2025-10-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-trades-sheet-upsert/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implement automatic ingestion of filled and partially-filled operations from the Broker API (pyRofex) into a configurable "Trades" Excel sheet. The solution must support idempotent upserts using a canonical key (Execution ID + Order ID + Broker Account), preserve historical execution context through in-place updates with audit markers, handle partial-to-final transitions and cancellations, and perform incremental batched processing for large datasets. The implementation will use the existing pyRofex WebSocket subscription mechanism with bulk Excel range updates for optimal performance, completing normal syncs within 10 seconds for typical volumes up to 50,000 rows.

## Technical Context

**Language/Version**: Python 3.9+ (matching existing codebase requirements)  
**Primary Dependencies**: pyRofex>=0.5.0 (broker API), xlwings>=0.31.0 (Excel integration), pandas>=2.0.0 (data processing), python-dotenv>=1.0.0 (configuration)  
**Storage**: Excel .xlsb workbook with dedicated "Trades" sheet; execution state persisted in-sheet; no external database  
**Testing**: pytest (optional per constitution - focus on operational reliability through logging and error handling)  
**Target Platform**: Windows workstation with Excel installed (xlwings requirement)  
**Project Type**: Single project (utility script for Excel integration)  
**Performance Goals**: <10 seconds for normal sync (hundreds of executions); <30 seconds ingestion latency (95th percentile); support up to 50,000 rows  
**Constraints**: Bulk Excel range updates mandatory (per Constitution II); idempotent operations; memory-bounded batching (default 500 rows); real-time WebSocket integration; Excel file remains open during updates  
**Scale/Scope**: ~5 new source files (trades ingestion, upsert logic, configuration); ~1,500 LOC; reuse existing api_client, sheet_operations, config modules

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Simplicity First ✅ PASS

- **Status**: Compliant
- **Assessment**: Implementation reuses existing pyRofex integration and Excel sheet_operations modules. New code focuses solely on trades-specific logic (fetching executions, upsert key matching, audit column updates). Minimal new dependencies required (all already in pyproject.toml).
- **Justification**: Clear separation between broker API layer (existing api_client.py), Excel updates (existing sheet_operations.py), and new trades ingestion logic keeps complexity contained.

### II. Excel Live Integration ✅ PASS

- **Status**: Compliant with CRITICAL requirement
- **Assessment**: All Excel writes will use bulk range updates via xlwings (e.g., `sheet.range('B3:P502').value = bulk_data`), following the same pattern already implemented in `update_market_data_to_prices_sheet()`. No individual cell loops permitted.
- **Justification**: Constitution explicitly mandates bulk writes for performance. Implementation will collect all upsert operations into a 2D array and write in a single xlwings operation per batch, ensuring minimal COM overhead.

### III. Real-time Data Updates ✅ PASS

- **Status**: Compliant
- **Assessment**: Feature uses existing pyRofex WebSocket subscription infrastructure (via `api_client.py`). Trades ingestion will subscribe to order status updates and execution reports, processing them asynchronously. Error handling via existing logging framework and retry logic.
- **Justification**: Leverages proven WebSocket handler pattern already operational for market data subscriptions. Proper error handling and logging in place per existing codebase standards.

### IV. Configuration Transparency ✅ PASS

- **Status**: Compliant
- **Assessment**: All configuration (Trades sheet name, column mapping, batch size, sync schedule) will be exposed via `config/excel_config.py` and environment variables (.env support). Clear documentation in config module with validation functions.
- **Justification**: Follows existing configuration pattern (pyrofex_config.py, excel_config.py) with .env override support. No hardcoded credentials or sheet names.

### V. No Testing Overhead ✅ PASS

- **Status**: Compliant
- **Assessment**: Testing is optional per constitution. Focus on operational reliability through comprehensive logging (using existing `utils/logging.py`), structured error handling, and validation functions. Any tests added will be for material reliability improvements only (e.g., upsert key deduplication logic).
- **Justification**: Constitution explicitly exempts utility scripts from mandatory TDD. Error logging, retry mechanisms, and validation provide operational reliability without formal test harness overhead.

**Gate Decision**: ✅ **PROCEED TO PHASE 0** — All constitution principles satisfied. No violations requiring complexity justification.

## Project Structure

### Documentation (this feature)

```text
specs/003-trades-sheet-upsert/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── pyrofex-trades-api.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/epgb_options/
├── __init__.py
├── main.py                          # Updated: integrate trades ingestion
├── config/
│   ├── __init__.py
│   ├── excel_config.py              # Updated: add Trades sheet configuration
│   └── pyrofex_config.py            # Existing (reused)
├── excel/
│   ├── __init__.py
│   ├── sheet_operations.py          # Updated: add trades-specific bulk upsert methods
│   ├── symbol_loader.py             # Existing (reused)
│   └── workbook_manager.py          # Existing (reused)
├── market_data/
│   ├── __init__.py
│   ├── api_client.py                # Updated: add order/execution subscription methods
│   ├── data_processor.py            # Existing (reused)
│   ├── instrument_cache.py          # Existing (reused)
│   └── websocket_handler.py         # Existing (reused)
├── trades/                          # NEW MODULE
│   ├── __init__.py                  # NEW: trades module exports
│   ├── execution_fetcher.py         # NEW: fetch filled/partial executions from API
│   ├── trades_processor.py          # NEW: process executions → DataFrame with audit columns
│   └── trades_upsert.py             # NEW: upsert logic with deduplication and batching
└── utils/
    ├── __init__.py
    ├── helpers.py                   # Existing (reused)
    ├── logging.py                   # Existing (reused)
    └── validation.py                # Existing (reused)

tests/
├── __init__.py
├── conftest.py                      # Existing
├── test_trades_upsert.py            # NEW (optional per constitution)
└── test_trades_processor.py         # NEW (optional per constitution)
```

**Structure Decision**: Single project structure maintained. New `trades/` module added under `src/epgb_options/` to encapsulate trades-specific logic (execution fetching, processing, upsert). Existing modules (`config/`, `excel/`, `market_data/`, `utils/`) extended where necessary to support trades ingestion. This structure maintains separation of concerns while reusing proven infrastructure (xlwings integration, pyRofex API client, logging, configuration).

## Complexity Tracking

*No complexity violations identified. This section remains empty per template guidance.*

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

[Gates determined based on constitution file]

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

*No complexity violations identified. This section remains empty per template guidance.*

---

## Phase Completion Status

### Phase 0: Outline & Research ✅ COMPLETE

**Deliverable**: `research.md`

**Research Questions Resolved**:
1. ✅ pyRofex API execution exposure (WebSocket + REST)
2. ✅ Idempotent upsert pattern (pandas merge + bulk xlwings)
3. ✅ Partial→final historical preservation (in-place update + audit columns)
4. ✅ Batched processing with resume tokens (cursor-based pagination)
5. ✅ Configuration exposure (extend excel_config.py with .env support)

**Key Decisions**:
- WebSocket subscriptions for real-time order updates
- pandas merge with indicator for efficient deduplication
- Bulk range updates per Constitution II
- Cursor-based backfill with Excel metadata checkpoint

---

### Phase 1: Design & Contracts ✅ COMPLETE

**Deliverables**:
- ✅ `data-model.md` — Execution entity, state transitions, Excel schema
- ✅ `contracts/pyrofex-trades-api.md` — WebSocket/REST API contract
- ✅ `quickstart.md` — Developer implementation guide
- ✅ Updated GitHub Copilot context (`.github/copilot-instructions.md`)

**Data Model Highlights**:
- Primary entity: Execution (17 fields including audit columns)
- Composite key: (ExecutionID, OrderID, Account)
- State transitions: NEW → PARTIALLY_FILLED → FILLED (with cancellation paths)
- Excel layout: Columns A-Q (17 columns), metadata in hidden column Z

**API Contract Highlights**:
- WebSocket: `pyRofex.order_report_subscription()` for real-time
- REST: `pyRofex.get_all_orders()` for historical backfill
- Error handling: Exponential backoff, fallback composite keys
- Validation: All required fields, enum values, state transition logic

---

### Phase 2: Implementation Planning — PENDING

**Next Command**: `/speckit.tasks`

This command will generate `tasks.md` with:
- Granular implementation tasks (checklist format)
- Estimated hours per task
- Dependencies and ordering
- Testing/validation steps

**Not included in `/speckit.plan` scope** — Phase 2 planning is separate.

---

## Summary

**Feature**: Trades Sheet Upsert (003-trades-sheet-upsert)

**Status**: ✅ Planning Complete (Phases 0-1) | ⏳ Implementation Pending (Phase 2)

**Branch**: `003-trades-sheet-upsert`

**Generated Artifacts**:
1. `plan.md` — This file (implementation plan, technical context, constitution check)
2. `research.md` — Technical decisions, best practices, open questions resolved
3. `data-model.md` — Entities, relationships, state transitions, Excel schema
4. `contracts/pyrofex-trades-api.md` — API integration contract (WebSocket + REST)
5. `quickstart.md` — Step-by-step developer implementation guide

**Agent Context Updated**: ✅ `.github/copilot-instructions.md` updated with Python 3.9+, pyRofex>=0.5.0, xlwings>=0.31.0, pandas>=2.0.0

**Next Steps**:
1. Run `/speckit.tasks` to generate implementation task breakdown
2. Begin implementation following `quickstart.md` guide
3. Test with mock executions before production deployment
4. Monitor upsert performance (target: <10s for normal sync)

**Constitution Compliance**: ✅ All principles satisfied (Simplicity First, Excel Live Integration with bulk writes, Real-time Data Updates, Configuration Transparency, No Testing Overhead)

---

**Plan Complete** | **Date**: 2025-10-22 | **Planner**: GitHub Copilot (speckit.plan command)
