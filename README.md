# EPGB Options Market Data

A Python application for fetching and managing options market data with Excel integration using pyRofex API.

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- Microsoft Excel (for xlwings integration)
- Windows OS (recommended for Excel integration)

### Installation

#### Option 1: Automatic Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/ChuchoCoder/EPGB_pyRofex.git
cd EPGB_pyRofex

# Run automatic setup
python setup.py

# For development setup
python setup.py --dev
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

#### Option 3: Modern pip installation

```bash
# Install in editable mode with pyproject.toml
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"
```

### Configuration Setup

1. **Copy environment template:**

   ```bash
   copy .env.example .env
   ```

2. **Edit `.env` file with your credentials:**

   ```env
   PYROFEX_USER=your_actual_username
   PYROFEX_PASSWORD=your_actual_password
   PYROFEX_ACCOUNT=your_actual_account
   ```

3. **Run configuration migration:**

   ```bash
   python tools/create_configs.py
   ```

### Running the Application

```bash
# Run main application
python main_HM.py

# Or using setup commands
python setup.py run
# Windows PowerShell:
.\setup.ps1 run
```

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
| pyRofex | ≥1.12.0 | Market data API integration |
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

### Using setup.py

```bash
python setup.py --check      # Check environment
python setup.py --upgrade    # Upgrade dependencies
python setup.py --clean      # Clean environment
```

### Using PowerShell (Windows)

```powershell
.\setup.ps1 install-dev       # Install development dependencies
.\setup.ps1 lint             # Run linting
.\setup.ps1 format           # Format code
.\setup.ps1 type-check       # Run type checking
```

### Using Make (Unix/Linux/Mac)

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
├── setup.py               # Automated setup script
├── setup.ps1              # PowerShell setup script
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
├── main_HM.py          # Legacy main application (deprecated)
└── Options_Helper_HM.py # Legacy helper utilities (deprecated)
```

## ⚙️ Configuration Management

The application uses a modern configuration system:

1. **Configuration Files:**
   - `excel_config.py` - Excel-related settings
   - `pyRofex_config.py` - API credentials and URLs

2. **Environment Variables:**
   - `.env` file for local development
   - Environment variables override config files

3. **Security Features:**
   - Credential validation at startup
   - File permission warnings
   - Git ignore patterns for sensitive files

## 🔧 Environment Setup Validation

Check your setup with:

```bash
python setup.py --check
```

This will verify:

- ✅ Python version compatibility
- ✅ Virtual environment status
- ✅ All dependencies installed
- ✅ Configuration files present

## 🎯 Usage Examples

### Basic Usage

```bash
# 1. Setup environment
python setup.py --dev

# 2. Configure credentials
# Edit .env file with your credentials

# 3. Run application
python main_HM.py
```

### Development Workflow

```bash
# 1. Install development tools
python setup.py --dev

# 2. Format and lint code
.\setup.ps1 format
.\setup.ps1 lint

# 3. Type checking
.\setup.ps1 type-check

# 4. Run application
.\setup.ps1 run
```

## 🔒 Security Considerations

- **Never commit `.env` files** - Contains sensitive credentials
- **Set appropriate file permissions** on configuration files
- **Use environment variables** in production deployments
- **Regularly rotate API credentials**

## 📋 Troubleshooting

### Common Issues

1. **Import errors:**

   ```bash
   python setup.py --check
   pip install -r requirements.txt
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

1. **Check system validation:**

   ```bash
   python validate_system.py
   ```

2. **Run configuration migration:**

   ```bash
   python tools/create_configs.py
   ```

3. **Upgrade dependencies:**

   ```bash
   python setup.py --upgrade
   ```

## 🤝 Contributing

1. **Setup development environment:**

   ```bash
   python setup.py --dev
   ```

2. **Install pre-commit hooks:**

   ```bash
   pre-commit install
   ```

3. **Run quality checks:**

   ```bash
   .\setup.ps1 quality
   ```

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:

- Check the troubleshooting section above
- Run `python setup.py --check` to validate your setup
- Review configuration files for proper setup
- Ensure all credentials are properly configured
 
 