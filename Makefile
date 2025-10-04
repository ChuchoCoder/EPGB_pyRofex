# EPGB Options Project Makefile
# Provides convenient commands for common development tasks

.PHONY: help install install-dev check upgrade clean lint format type-check run test

# Default target
help:
	@echo "EPGB Options Project Commands"
	@echo "============================="
	@echo ""
	@echo "Setup Commands:"
	@echo "  make install     - Install production dependencies"
	@echo "  make install-dev - Install development dependencies"
	@echo "  make check       - Check current environment"
	@echo "  make upgrade     - Upgrade all dependencies"
	@echo "  make clean       - Clean virtual environment"
	@echo ""
	@echo "Development Commands:"
	@echo "  make lint        - Run linting (ruff)"
	@echo "  make format      - Format code (ruff)"
	@echo "  make type-check  - Run type checking (mypy)"
	@echo "  make run         - Run the main application"
	@echo ""
	@echo "Utility Commands:"
	@echo "  make config      - Run configuration migration"
	@echo "  make validate    - Validate system setup"

# Setup commands
install:
	@python setup.py

install-dev:
	@python setup.py --dev

check:
	@python setup.py --check

upgrade:
	@python setup.py --upgrade

clean:
	@python setup.py --clean

# Development commands  
lint:
	@echo "🔍 Running linter..."
	@ruff check .

format:
	@echo "🎨 Formatting code..."
	@ruff format .

type-check:
	@echo "🔍 Running type checker..."
	@mypy .

# Application commands
run:
	@echo "🚀 Running EPGB Options..."
	@python main_HM.py

config:
	@echo "⚙️ Running configuration migration..."
	@python tools/create_configs.py

validate:
	@echo "✅ Validating system setup..."
	@python validate_system.py

# Combined quality checks
quality: lint type-check
	@echo "✅ All quality checks passed"

# Development setup with quality tools
dev-setup: install-dev
	@echo "🔧 Setting up pre-commit hooks..."
	@pre-commit install || echo "⚠️ pre-commit not available - install with: pip install pre-commit"
	@echo "✅ Development setup complete"