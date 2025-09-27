# Research: PyRofex Integration

## Research Questions and Findings

### pyRofex Library Integration
**Decision**: Use pyRofex library as direct replacement for pyhomebroker  
**Rationale**: Official library from MATBA ROFEX provides native websocket support and better API stability  
**Alternatives considered**: Direct REST API calls (rejected due to complexity), maintain pyhomebroker (rejected due to reliability issues)

### COCOS Broker Environment Configuration  
**Decision**: Use COCOS-specific endpoints with Environment.LIVE  
**Rationale**: User specified COCOS broker requirements with specific URLs  
**Configuration**:
- URL: `https://api.cocos.xoms.com.ar/`
- WebSocket: `wss://api.cocos.xoms.com.ar/`
- Environment: `pyRofex.Environment.LIVE`

### Symbol Transformation Requirements
**Decision**: Implement prefix/suffix transformation as specified  
**Rationale**: pyRofex uses different naming convention than pyhomebroker  
**Transformation Rules**:
- Add "MERV - XMEV - " prefix to all tickers
- Replace " - spot" suffix with " - CI"
- Example: "YPFD - 24hs" → "MERV - XMEV - YPFD - 24hs"
- Example: "GGAL - spot" → "MERV - XMEV - GGAL - CI"

### WebSocket Market Data Handling
**Decision**: Use pyRofex websocket API following sample pattern  
**Rationale**: Provides real-time streaming without polling overhead  
**Pattern**: Initialize handlers → establish connection → subscribe to instruments → process updates

### Error Handling Strategy  
**Decision**: Implement specific error handling per clarifications  
**Rationale**: Based on user clarifications for different failure scenarios  
**Approaches**:
- Connection failures: Exponential backoff reconnection
- Authentication failures: Stop execution, manual intervention required
- Invalid symbols: Mark unavailable, continue with valid ones  
- Excel file locks: Skip updates, continue data collection

### Data Validation Requirements
**Decision**: Validate critical fields only (price, symbol)  
**Rationale**: Balance between data integrity and performance per user clarification  
**Implementation**: Check for required fields before Excel updates

### Excel Integration Preservation
**Decision**: Maintain existing xlwings integration approach  
**Rationale**: Constitutional requirement for Excel Live Integration  
**Approach**: Update data processing to adapt pyRofex format to existing Excel structure

## Technology Stack Decisions

### Dependencies
- **pyRofex**: Market data API integration
- **xlwings**: Excel integration (unchanged)
- **pandas**: Data manipulation (unchanged)  
- **time**: Update timing (unchanged)

### Architecture Pattern
- **Event-driven**: WebSocket message handlers
- **Data transformation**: pyRofex format → pandas DataFrame → Excel
- **Error recovery**: Automated reconnection with fallback strategies

## Implementation Considerations

### Performance
- WebSocket reduces API call overhead vs REST polling
- DataFrame updates maintain existing Excel update performance
- 2-second refresh cycle preserved

### Compatibility  
- Python 3.x compatibility maintained
- Excel .xlsb format compatibility preserved
- Existing helper module structure maintained

### Operational Reliability
- Connection resilience via exponential backoff
- Data validation prevents corrupt Excel updates
- Error logging for troubleshooting
- Graceful handling of Excel file access issues