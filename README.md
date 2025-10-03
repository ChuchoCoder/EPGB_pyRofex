# EPGB Options Market Data

A Python application for fetching and managing options market data with Excel integration using pyRofex API.

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- Microsoft Excel (for xlwings integration)
- Windows OS (recommended for Excel integration)

### Installation

#### Option 1: Modern Editable Install (Recommended)

```bash
# Clone the repository
git clone https://github.com/ChuchoCoder/EPGB_pyRofex.git
cd EPGB_pyRofex

# Create & activate a virtual environment (Windows)
python -m venv .venv
.venv\\Scripts\\activate

# Install package in editable mode with optional dev extras
pip install -e .
# Or include development tooling
pip install -e ".[dev]"
```

#### Option 2: Manual Installation

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Or for development
pip install -r requirements-dev.txt
```

### Configuration Setup

1. **Copy environment template:**

   ```bash
   copy data\.env.example .env
   ```

2. **Edit `.env` file with your credentials:**

   ```env
   PYROFEX_USER=your_actual_username
   PYROFEX_PASSWORD=your_actual_password
   PYROFEX_ACCOUNT=your_actual_account
   ```

3. **(Optional) Generate missing config modules:**

   ```bash
   python tools/create_configs.py
   ```

### Running the Application

```bash
# Run via installed console script
epgb-options

# Or module form (equivalent)
python -m epgb_options.main
```

Add `--help` for future CLI flags (planned extension point).

### Debugging in VS Code

The project includes pre-configured debug configurations in `.vscode/launch.json`:

1. **Python: EPGB Options (Main)** - Debug the main application (looks for `.env` in root)
2. **Python: EPGB Options (data/.env)** - Debug using `.env` from `data/` folder
3. **Python: Validation Script** - Debug the validation tool
4. **Python: Create Configs** - Debug config generation

**Quick Start:**

1. Open the project in VS Code
2. Set breakpoints in your code (click left of line numbers)
3. Press `F5` or go to Run → Start Debugging
4. Select "Python: EPGB Options (Main)" from the dropdown

**Debug Features:**

- Step through code line by line (`F10` = step over, `F11` = step into)
- Inspect variables in the Variables pane
- Watch expressions in the Watch pane
- View call stack and breakpoints
- Use Debug Console for runtime evaluation

**Tips:**

- Set breakpoints in `src/epgb_options/main.py` initialization
- Check `api_client.py` for API connection issues
- Monitor `websocket_handler.py` for real-time data flow
- Use conditional breakpoints (right-click breakpoint) for specific scenarios

## 📦 Dependency Management

This project uses modern Python dependency management with multiple options:

### Files Overview

- **`pyproject.toml`** - Modern Python project configuration (PEP 518/621)
- **`requirements.txt`** - Core production dependencies
- **`requirements-dev.txt`** - Development dependencies
- **`setup.py`** - Automated setup script with multiple modes
- **`setup.ps1`** - PowerShell setup script for Windows users
- **`Makefile`** - Unix-style command shortcuts

### Core Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| pyRofex | ≥0.5.0 | Market data API integration |
| xlwings | ≥0.31.0 | Excel integration |
| pandas | ≥2.0.0 | Data manipulation |
| python-dotenv | ≥1.0.0 | Environment variable management |
| python-dateutil | ≥2.8.0 | Date/time utilities |

### Development Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| ruff | ≥0.1.0 | Modern linting and formatting |
| mypy | ≥1.0.0 | Static type checking |
| pre-commit | ≥3.0.0 | Git hooks for code quality |

## 🛠️ Development Commands

### Core Dev Tasks (Modern Way)

```bash
pip install -e ".[dev]"   # Install dev dependencies
ruff check .               # Lint
ruff format .              # Auto-format
mypy src/epgb_options      # Type check
pytest                     # (When tests added)
```

\n### (Legacy) setup.py helpers
Retained temporarily; will be removed in a future cleanup.

```bash
python setup.py --check
python setup.py --dev
```

\n### PowerShell Convenience (Optional)

```powershell
.# Activate environment first
.venv\Scripts\activate
ruff check .
ruff format .
mypy src/epgb_options
```

\n### Using Make (Unix/Linux/Mac)

```bash
make install-dev             # Install development dependencies
make lint                    # Run linting
make format                  # Format code
make type-check             # Run type checking
make quality                # Run all quality checks
```

## 📁 Project Structure

```text
EPGB_pyRofex/
├── pyproject.toml          # Modern project configuration
├── requirements.txt        # Core dependencies
├── requirements-dev.txt    # Development dependencies
├── setup.py.backup        # (Legacy) transitional script (avoid)
├── setup.ps1              # (Optional) legacy helper
├── Makefile               # Unix command shortcuts
│
├── src/epgb_options/      # Main application package
│   ├── __init__.py
│   ├── main.py           # Application entry point
│   ├── config/           # Configuration modules
│   │   ├── __init__.py
│   │   ├── excel_config.py
│   │   └── pyrofex_config.py
│   ├── market_data/      # Market data operations
│   │   ├── __init__.py
│   │   ├── api_client.py
│   │   ├── websocket_handler.py
│   │   └── data_processor.py
│   ├── excel/            # Excel operations
│   │   ├── __init__.py
│   │   ├── workbook_manager.py
│   │   ├── symbol_loader.py
│   │   └── sheet_operations.py
│   └── utils/            # Utility functions
│       ├── __init__.py
│       ├── logging.py
│       ├── validation.py
│       └── helpers.py
│
├── tools/                # Development tools
│   ├── create_configs.py # Configuration migration utility
│   ├── validate_system.py
│   ├── validate_quickstart.py
│   └── check_tickers.py
│
├── data/                 # Data files
│   ├── .env.example     # Environment variable template
│   └── EPGB OC-DI - Python.xlsb  # Excel workbook
│
├── tests/               # Test suite
│   ├── __init__.py
│   └── conftest.py
│
├── docs/                # Documentation
│   ├── STRUCTURE_PROPOSAL.md
│   ├── MIGRATION_STATUS.md
│   └── specs/          # Feature specifications
│
├── .gitignore          # Git ignore patterns
└── README.md           # Project documentation
```

> Legacy monolithic files (`main_HM.py`, `Options_Helper_HM.py`) were removed after migration.

\n## ⚙️ Configuration Management

The application uses a modern configuration system:

1. **Configuration Modules (generated / maintained):**
   - `src/epgb_options/config/excel_config.py`
   - `src/epgb_options/config/pyrofex_config.py`

2. **Environment Variables:**
   - `.env` file for local development
   - Environment variables override config files

3. **Security Features:**
   - Startup credential validation with descriptive failures
   - `.env` excluded via `.gitignore`
   - No plaintext password defaults retained

\n## 🔧 Environment Setup Validation

Check your setup with:

```bash
python tools/validate_system.py
```

Validates:

- ✅ Imports & package structure
- ✅ Entry point availability (`epgb-options`)
- ✅ Config modules + environment template presence

\n## 🎯 Usage Examples

### Basic Usage

```bash
# 1. Install (dev mode)
pip install -e ".[dev]"

# 2. Copy & edit environment
copy data\.env.example .env
notepad .env

# 3. (Optional) generate config stubs
python tools/create_configs.py

# 4. Run
epgb-options
```

### Development Workflow

```bash
pip install -e ".[dev]"
ruff check .
ruff format .
mypy src/epgb_options
epgb-options
```

\n## 🔒 Security Considerations

- **Never commit `.env` files** - Contains sensitive credentials
- **Set appropriate file permissions** on configuration files
- **Use environment variables** in production deployments
- **Regularly rotate API credentials**

\n## 📋 Troubleshooting

### Common Issues

1. **Import errors:**

   ```bash
   pip install -e .
   pip install -e ".[dev]"
   ```

2. **Excel connection issues:**
   - Ensure Excel is installed and accessible
   - Check file permissions on Excel workbook
   - Verify xlwings installation

3. **API authentication errors:**
   - Verify credentials in `.env` file
   - Check pyRofex API status
   - Validate account permissions

### Getting Help

1. **Run validation suite:**

   ```bash
   python tools/validate_system.py
   ```

2. **Run configuration migration:**

   ```bash
   python tools/create_configs.py
   ```

3. **Upgrade dependencies:**

   ```bash
   python setup.py --upgrade
   ```

\n## 🤝 Contributing

1. **Setup development environment:**

   ```bash
   pip install -e ".[dev]"
   ```

2. **Install pre-commit hooks:**

   ```bash
   pre-commit install
   ```

3. **Run quality checks:**

   ```bash
   ruff check .
   ruff format .
   mypy src/epgb_options
   ```

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:

- Run `python tools/validate_system.py` to validate setup
- Review `src/epgb_options/config/` modules
- Ensure `.env` is present with populated credentials
- Confirm virtual environment is active
