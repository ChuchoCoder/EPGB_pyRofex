# Feature Specification: Replace PyHomeBroker with PyRofex

**Feature Branch**: `001-replace-pyhomebroker-dependency`  
**Created**: 2025-09-27  
**Status**: Draft  
**Input**: User description: "Replace pyhomebroker dependency with pyRofex. Use websocket to obtain market data following sample found in https://raw.githubusercontent.com/matbarofex/pyRofex/refs/heads/master/samples/4_websocket_market_data.py. Before initializing and setting credentials, set env url and ws parameters for specific broker pyRofex._set_environment_parameter('url', 'https://api.cocos.xoms.com.ar/', Environment.LIVE) pyRofex._set_environment_parameter('ws', 'wss://api.cocos.xoms.com.ar/', Environment.LIVE). Then do initialize pyRofex.initialize(user='username', password='password', account='account', environment=pyRofex.Environment.LIVE). Instruments from pyRofex contain a Market Prefix: Assume 'MERV - XMEV - ' prefix for any Ticker. e.g.: Symbol is 'MERV - XMEV - YPFD - 24hs' for 'YPFD - 24hs' ticker. Also, ' - spot' suffix should be replaced with ' - CI'. e.g.: 'GGAL - spot' replaced with 'GGAL - CI'. MarketData structure that comes from the websocket may have different structure or property names. Analyze the object data/contract to adapt it. Investigate any other change that may be required to fully switch the pyhombroker dependency for pyRofex"

## Clarifications

### Session 2025-09-27
- Q: What should the system do when the websocket connection fails during market hours? → A: Immediately attempt reconnection with exponential backoff
- Q: How should the system handle persistent authentication failures with pyRofex? → A: Stop execution and require manual intervention
- Q: Should the system validate market data before updating Excel? → A: Validate critical fields only (price, symbol)
- Q: How should the system handle symbols that don't exist in pyRofex? → A: Mark as unavailable in Excel and continue
- Q: What should happen if the Excel file becomes locked or unavailable during updates? → A: Skip updates and continue collecting data

---

## User Scenarios & Testing

### Primary User Story
As a market data analyst, I need the EPGB Options system to continue providing real-time financial data updates to my Excel workbook, but using the pyRofex API instead of pyhomebroker to ensure better reliability and access to market data from the COCOS broker environment.

### Acceptance Scenarios
1. **Given** the system is configured with pyRofex credentials, **When** the market data script runs, **Then** real-time quotes for stocks, bonds, options, and other instruments are successfully received via websocket
2. **Given** market data is received from pyRofex websocket, **When** data processing occurs, **Then** the Excel workbook is updated with the same format and structure as before
3. **Given** instrument symbols are configured in the Tickers sheet, **When** pyRofex requests market data, **Then** symbols are correctly prefixed with "MERV - XMEV - " and "spot" suffixes are replaced with "CI"
4. **Given** the websocket connection is established, **When** market data updates arrive, **Then** the data is processed continuously without blocking Excel operations

### Edge Cases
- What happens when websocket connection fails or drops unexpectedly?
- How does the system handle invalid or unavailable instrument symbols?
- What occurs if the Excel file is closed while market data updates are running?
- How are authentication errors with pyRofex handled?

## Requirements

### Functional Requirements
- **FR-001**: System MUST replace pyhomebroker library with pyRofex for market data access
- **FR-002**: System MUST configure pyRofex environment parameters for COCOS broker (URL and WebSocket endpoints)
- **FR-003**: System MUST authenticate with pyRofex using provided user credentials and account information, and MUST stop execution if authentication fails to require manual intervention
- **FR-004**: System MUST establish websocket connection for real-time market data streaming
- **FR-005**: System MUST subscribe to market data for all instrument types (stocks, bonds, options, cedears, cauciones)
- **FR-006**: System MUST transform instrument symbols by adding "MERV - XMEV - " prefix to all tickers
- **FR-007**: System MUST replace " - spot" suffix with " - CI" in all instrument symbols
- **FR-008**: System MUST adapt incoming market data structure to match expected Excel data format and MUST validate critical fields (price, symbol) before processing
- **FR-009**: System MUST maintain continuous Excel updates without interrupting user interaction
- **FR-010**: System MUST handle websocket disconnections by immediately attempting reconnection with exponential backoff (1s, 2s, 4s, 8s intervals) and appropriate error logging
- **FR-011**: System MUST preserve existing Excel workbook structure and data organization
- **FR-012**: System MUST maintain the same 2-second update frequency for Excel data refresh
- **FR-013**: System MUST handle invalid or unavailable instrument symbols by marking them as "unavailable" in Excel and continuing with valid symbols
- **FR-014**: System MUST handle Excel file access errors by skipping updates and continuing to collect market data until file becomes available

### Key Entities
- **Market Data Stream**: Real-time financial data received via pyRofex websocket, containing bid/ask prices, volumes, and trading information
- **Instrument Symbol**: Financial instrument identifier requiring transformation from internal format to pyRofex format with market prefix
- **Excel Data Range**: Specific worksheet ranges where different instrument types are updated (options, stocks, bonds, etc.)
- **Broker Connection**: Authenticated session with pyRofex API using COCOS broker endpoints
- **Market Data Handler**: Processing logic that transforms pyRofex data format to Excel-compatible structure

---

## Review & Acceptance Checklist

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous  
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

---

## Execution Status

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [x] Review checklist passed
