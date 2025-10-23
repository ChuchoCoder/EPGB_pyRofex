# Feature Specification: Trades sheet upsert

**Feature Branch**: `003-trades-sheet-upsert`
**Created**: 2025-10-22
**Status**: Draft
**Input**: User description: "Obtain filled/partially-filled operations from API and persist them to an Excel \"Trades\" sheet (configurable). Provide a new, configurable Trades sheet in the Excel workbook and a stable routine that automatically obtains operations (orders) from the Broker API that are filled or partially filled and upserts them into that sheet. The behaviour must be idempotent (safe to run repeatedly), must avoid duplicates, and must preserve historical trade data while updating partial-fills to final state."

## Clarifications

### Session 2025-10-22

- Q: What is the target completion time for a normal sync (in seconds)? → A: 10 seconds
- Q: What is the maximum expected number of rows in the Trades sheet? → A: 50000 rows
- Q: How should broker API failures be handled? → A: Log and skip the failed operation
- Q: Are there any security requirements for accessing the broker API? → A: Authentication is already covered with the existing pyRofex implementation
- Q: Are there any regulatory compliance requirements for trade data retention? → A: No specific requirements
- Q: When preserving historical executions, should we append a new row for each execution event (partial + final) or update the original partial row and add an audit marker? → A: B (Update original row + audit marker)
 - Q: What is the canonical upsert key for deduplication? → A: B (Execution ID + Order ID + Broker Account)
- Q: When a partial execution is later canceled, how should it be represented? → A: B (Update original partial row to 'Canceled' and populate audit columns)
- Q: Should the upsert key be configurable by administrators? → A: A (No — keep fixed as Execution ID + Order ID + Broker Account)
- Q: What backfill / large-sheet batching strategy should be used? → A: B (Incremental batched upserts with resume tokens; default batch size 500)

## User Scenarios & Testing

### User Story 1 - Persist completed trades to Excel (Priority: P1)

As a user running the options workbook, I want the system to automatically subscribe to or poll the broker for filled and partially-filled operations and persist them into a configured "Trades" sheet, so I can review historical executed trades and reconcile positions in Excel without manual intervention.

**Why this priority**: This delivers immediate operational value — users need accurate trade records for P&L, reconciliation and downstream workflows.

**Acceptance Scenarios**:

1. **Given** a new Trades sheet is configured and the broker account has filled orders, **When** new executions occur at the broker or are discovered by the subscription/poller, **Then** the Trades sheet is automatically updated with one row per filled execution including timestamps and identifiers (no manual action required).
2. **Given** an order has a partial fill and later completes, **When** the subscription/poller observes both events, **Then** the Trades sheet reflects updated quantities/status for that order without creating duplicates and preserves original partial-fill rows per the preservation model.
3. **Given** the ingestion runs continuously or on a schedule, **When** no new executions exist, **Then** the Trades sheet is unchanged (idempotent behavior) and repeated ingestion attempts do not create duplicate rows.
4. **Given** a new execution arrives, **When** the ingestion mechanism observes it, **Then** the execution appears in the Trades sheet within the timeliness bounds defined in Success Criteria (see SC-006).

---

### User Story 2 - Configure sheet and mapping (Priority: P2)

As an administrator, I want to configure the workbook with the Trades sheet name and column mapping so the routine can write into the correct sheet and columns used by our internal templates.

**Why this priority**: Flexibility to integrate with different workbook layouts and naming conventions.

**Independent Test**: Change configuration values to point at a different sheet name and column layout; simulate executions on the broker or replay recorded events and verify the subscription/poller automatically writes data into the configured cells without manual triggering.

**Acceptance Scenarios**:

1. **Given** a configured sheet name and column mapping, **When** the routine runs, **Then** trades are written to the configured sheet and columns match the mapping.

---

### User Story 3 - Preserve historical executions (Priority: P3)

As an auditor, I want historical execution events preserved so I can trace the lifecycle of an order (partial fills then final) without losing the original events.

**Why this priority**: Historical auditability is required for accurate reconciliation and compliance.

**Independent Test**: Introduce a partial-fill event and then a final-fill event. Verify the sheet contains the historical partial-fill row (marked as partial) and a final row or an updated row per the chosen preservation model.

**Acceptance Scenarios**:

1. **Given** a partial-fill execution row exists, **When** a final-fill is observed, **Then** the partial row is updated to final (see Assumptions).

---

### Edge Cases

- Partial fills that arrive out-of-order (timestamp skew or delayed events).
- Orders canceled between partial and final fills: update the original partial row to status "Canceled" and populate audit columns; do not append duplicate cancellation rows by default.
- Duplicate events from the broker API (same execution id) — routine must deduplicate.
- Very large backfills — performance considerations when sheet is large.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide an Excel Trades sheet (configurable name) and create it when absent in the workbook.
- **FR-002**: The system MUST fetch operations (orders/executions) from the Broker API that are in states representing partial or full fills.
- **FR-003**: The system MUST upsert fetched executions into the Trades sheet using Execution ID + Order ID + Broker Account as the canonical upsert key to avoid duplicates.
- **FR-013**: The canonical upsert key (Execution ID + Order ID + Broker Account) is fixed and MUST NOT be configurable via workbook settings by default; changing it requires code changes or an explicit feature extension.
- **FR-004**: The upsert operation MUST be idempotent: repeated runs with no new data must not create duplicate rows.

- **FR-014**: For large sheets and backfills the system MUST perform incremental, batched upserts using a resume token (cursor) and a configurable batch size (default: 500 rows) to bound memory and allow resumable operations.
- **FR-005**: When an execution is partial and later updated to final, the system MUST update the existing row(s) or append a new row per the preservation model while preserving historical context (see Assumptions).
- **FR-006**: The system MUST store the following fields per execution where available: Execution ID, Order ID, Instrument Symbol, Side (buy/sell), Quantity, Price, Filled Quantity, Execution Timestamp (UTC), Broker Account, Order Status, Trade/Execution Type (partial/final), and Source.
- **FR-007**: The system MUST allow column mapping through configuration so column order and headers in the workbook can vary.
- **FR-008**: The system MUST automatically ingest operations either by maintaining a live subscription to the broker feed or by running a configurable polling/sync schedule. Manual invocation (for on-demand reconciliation) may be supported as an optional secondary mechanism but automatic ingestion is required.
- **FR-009**: The system MUST log summary results of each run (number of new rows added, rows updated, duplicates ignored, errors) to the application log accessible to operators.
- **FR-010**: The system MUST handle and deduplicate identical events from the Broker API based on the stable unique execution key.
- **FR-011**: Preservation model chosen: update the original partial row to final and add an audit marker on that row. When a partial execution later becomes final the routine MUST update the existing Trades sheet row to reflect final quantities/status and populate audit columns (PreviousFilledQty, PreviousTimestampUTC, Superseded, CancelReason) to retain sufficient historical context. A separate full-event audit sheet will not be created by default.
**FR-012**: When a partial execution is later canceled, the system MUST update the existing partial row to status = "Canceled", populate audit columns (PreviousFilledQty, PreviousTimestampUTC, Superseded, CancelReason), and must NOT append an additional cancellation row by default.

### Key Entities *(include if feature involves data)*

- **Execution / Trade**: Represents a single execution event. Attributes: Execution ID, Order ID, Instrument, Side, Quantity, Price, Filled Quantity, Timestamp (UTC), Broker Account, Status, Execution Type, Source.
- **Trades Sheet Configuration**: Represents workbook-level configuration: Sheet name, Header row index, Column mapping (field -> column letter/index), Upsert key definition (Execution ID + Order ID + Broker Account) — fixed (not configurable), Preserve-historical boolean.
## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Idempotency — Running the upsert routine 5 times with the same dataset produces no more than 0 additional rows (0 duplicates) and identical sheet state after the first run.
- **SC-002**: Deduplication accuracy — 100% of duplicate execution events (same execution id + account) are detected and not duplicated in the Trades sheet during test runs.
- **SC-003**: Partial-to-final update correctness — Given a partial execution followed by a final execution for the same order, the sheet reflects the final state and historical context according to the chosen preservation model in at least 95% of test cases (accounting for edge-case ordering issues).
- **SC-004**: Configurability — Workbook administrators can change sheet name and column mapping and observe correct writes within one configuration change.
- **SC-005**: Observability — Each routine run logs a summary with counts (added/updated/ignored/errors) and any run failures are surfaced to the operator logs.
- **SC-006**: Ingestion timeliness — 95% of new executions are reflected in the Trades sheet within 30 seconds of being observable by the broker API under normal network conditions.
- **SC-007**: Ingestion reliability — Over a rolling 24-hour window, scheduled or subscription-based ingestion attempts succeed without data loss in at least 99% of runs (excluding maintenance windows).

## Assumptions

- The canonical upsert key is Execution ID + Order ID + Broker Account; if an execution id is missing from the broker event, a fallback composite (Order ID + Execution Timestamp + Broker Account) will be used.
- Broker API failures will be logged and the failed operation skipped to avoid blocking the entire sync.
- Cancellations of partially-filled orders will be represented by updating the original partial execution row to status "Canceled" and adding audit metadata in-place (see FR-012). Audit columns: PreviousFilledQty, PreviousTimestampUTC, Superseded, CancelReason.
- Upsert key is fixed as Execution ID + Order ID + Broker Account and is not configurable via workbook settings.
- Authentication for the broker API is handled by the existing pyRofex implementation.
- For large-sheet backfills the implementation will use incremental batched upserts with resume tokens and a configurable batch size (default 500) to support resumable and memory-bounded operations.
- No specific regulatory compliance requirements for trade data retention beyond standard data management practices.
- The Excel workbook is writable by the process and has a predictable header row location; if headers are missing the routine will create them using configured mapping.
- Update the original partial row to final and add audit marker columns on that same row to preserve historical context while keeping the primary Trades sheet compact.
- Time values will be stored and compared in UTC to avoid timezone ambiguity.
- For performance, very large sheets may require batching or incremental sync; initial implementation will work up to 50000 rows with further optimization later.
- The application environment supports maintaining a persistent subscription or a scheduled background process capable of polling the broker API on a configurable cadence; the process has write access to the workbook.

## Non-functional requirements

- The routine SHOULD complete a normal sync within 10 seconds for typical daily volumes (hundreds of executions). (Non-mandatory target.)
- The routine MUST not corrupt the workbook; writes must be atomic per run where possible (use workbook-level save after batch writes.).

