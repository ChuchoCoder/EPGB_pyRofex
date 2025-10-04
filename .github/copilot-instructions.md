# EPGB Options Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-09-27

## Active Technologies
- Python 3.x + pyRofex, xlwings, pandas (replacing pyhomebroker) (001-replace-pyhomebroker-dependency)
- Python 3.x (consistent with existing codebase) + python-dotenv, xlwings, pyRofex, pandas (existing dependencies retained) (002-all-configuration-values)
- Configuration files (.py modules), environment variables via .env files (002-all-configuration-values)

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
- 002-all-configuration-values: Added Python 3.x (consistent with existing codebase) + python-dotenv, xlwings, pyRofex, pandas (existing dependencies retained)
- 001-replace-pyhomebroker-dependency: Added Python 3.x + pyRofex, xlwings, pandas (replacing pyhomebroker)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
