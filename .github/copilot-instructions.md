# EPGB Options Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-09-27

## Active Technologies
- Python 3.x + pyRofex, xlwings, pandas (replacing pyhomebroker) (001-replace-pyhomebroker-dependency)
- Python 3.x (consistent with existing codebase) + python-dotenv, xlwings, pyRofex, pandas (existing dependencies retained) (002-all-configuration-values)
- Configuration files (.py modules), environment variables via .env files (002-all-configuration-values)
- Python 3.9+ (matching existing codebase requirements) + pyRofex>=0.5.0 (broker API), xlwings>=0.31.0 (Excel integration), pandas>=2.0.0 (data processing), python-dotenv>=1.0.0 (configuration) (003-trades-sheet-upsert)
- Excel .xlsb workbook with dedicated "Trades" sheet; execution state persisted in-sheet; no external database (003-trades-sheet-upsert)

## Project Structure
```
src/
tests/
```

## Commands
cd src; pytest; ruff check .

## Code Style
Python 3.x: Follow standard conventions

## Recent Changes
- 003-trades-sheet-upsert: Added Python 3.9+ (matching existing codebase requirements) + pyRofex>=0.5.0 (broker API), xlwings>=0.31.0 (Excel integration), pandas>=2.0.0 (data processing), python-dotenv>=1.0.0 (configuration)
- 002-all-configuration-values: Added Python 3.x (consistent with existing codebase) + python-dotenv, xlwings, pyRofex, pandas (existing dependencies retained)
- 001-replace-pyhomebroker-dependency: Added Python 3.x + pyRofex, xlwings, pandas (replacing pyhomebroker)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
