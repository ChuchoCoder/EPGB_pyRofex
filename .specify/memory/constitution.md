<!--
SYNC IMPACT REPORT
==================
Version change: Initial creation → 1.0.0
Project: EPGB Options Market Data - Simple Python market data fetcher with Excel integration
Date: 2025-09-27

Modified Principles:
- NEW: I. Simplicity First - Emphasizes vanilla Python, minimal dependencies
- NEW: II. Excel Live Integration - xlwings integration with open Excel files
- UPDATED: II. Excel Live Integration - Added CRITICAL requirement for bulk range updates
- NEW: III. Real-time Data Updates - Continuous market data without blocking
- NEW: IV. Configuration Transparency - Clear symbol lists and credentials
- NEW: V. No Testing Overhead - Explicitly excludes unit testing requirements

Added Sections:
- Technical Constraints: Technology stack, performance standards
- UPDATED: Performance Standards - Added bulk update requirement
- Development Workflow: Code organization principles

Removed Sections:
- N/A (initial creation)

Templates Requiring Updates:
⚠ plan-template.md - Contains TDD/testing references that conflict with Principle V
⚠ spec-template.md - Generally compatible, no testing conflicts
⚠ tasks-template.md - Heavy emphasis on TDD/testing phases conflicts with Principle V

Follow-up TODOs:
- Consider creating simplified task template for utility scripts
- Update plan template Constitution Check section to reference actual principles
- Document Excel integration patterns for future reference
-->

# EPGB Options Market Data Constitution

## Core Principles

### I. Simplicity First

Keep the script straightforward and maintainable. Use vanilla Python with minimal dependencies beyond essential libraries (xlwings, pyhomebroker, pandas). Avoid over-engineering solutions for this utility script. Clear, readable code is preferred over complex optimizations.

### II. Excel Live Integration

Excel files MUST remain updatable while open. Use xlwings for seamless integration with existing Excel workbooks. Maintain compatibility with .xlsb format. Preserve existing Excel structure and formatting when updating data.

**CRITICAL: All Excel updates MUST use bulk range updates for performance.** Instead of updating individual cells or rows in a loop, collect all changes and write them in a single operation using xlwings range assignments (e.g., `sheet.range('B3:O34').value = bulk_data`). This minimizes COM calls to Excel and dramatically improves update speed, especially for real-time market data streaming. Individual cell updates in loops are prohibited due to severe performance degradation.

### III. Real-time Data Updates

Market data updates MUST occur continuously without blocking the main execution thread. Handle API responses asynchronously where possible. Implement proper error handling for network failures and API rate limits.

### IV. Configuration Transparency

All symbol lists, broker credentials, and data ranges MUST be clearly defined and easily modifiable. Use the Tickers sheet for symbol configuration. Keep sensitive credentials clearly marked but separate from core logic.

### V. No Testing Overhead

This utility script does NOT require unit tests or TDD practices. Focus on operational reliability through clear error handling and logging rather than formal testing frameworks. Simplicity over test coverage for this specific use case.

## Technical Constraints

### Technology Stack

- Python 3.x with essential libraries: xlwings, pyhomebroker, pandas
- Excel integration via xlwings (supports .xlsb format)
- HomeBroker API for market data
- Direct Excel file manipulation while files remain open

### Performance Standards

- Market data updates should complete within reasonable timeframes (typically under 30 seconds)
- Excel updates must not interfere with user interaction
- **All Excel writes MUST use bulk range updates** - Single operation for entire data range instead of per-row/per-cell loops
- Memory usage should remain reasonable for continuous operation

## Development Workflow

### Code Organization

- Main script (main_HM.py) handles execution flow and data orchestration
- Helper module (Options_Helper_HM.py) manages Excel data extraction and symbol lists
- Clear separation between data fetching, processing, and Excel updating

## Governance

This constitution supersedes all other development practices for the EPGB Options Market Data project. Changes to core principles require documentation and justification.

All modifications must maintain compatibility with existing Excel workbooks and preserve the simplicity principle. Script reliability takes priority over feature completeness.

For development guidance, refer to existing code comments and inline documentation rather than external testing frameworks.

**Version**: 1.0.1 | **Ratified**: 2025-09-27 | **Last Amended**: 2025-10-03