.PHONY: help install install-dev test lint format type-check clean all ci

help:
	@echo "ContextRefactor development commands:"
	@echo ""
	@echo "Installation:"
	@echo "  make install        Install the package in production mode"
	@echo "  make install-dev    Install with dev + MCP dependencies"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test          Run pytest"
	@echo "  make test-cov      Run pytest with coverage"
	@echo "  make lint          Run ruff linter"
	@echo "  make format        Check code formatting"
	@echo "  make type-check    Run mypy type checking"
	@echo "  make ci            Run all CI checks (lint, type-check, test)"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean         Remove build artifacts and cache"
	@echo "  make all           Install dev dependencies, lint, type-check, and test"
	@echo ""

install:
	pip install -e .

install-dev:
	pip install -e ".[dev,mcp]"

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=context_refactor --cov=mcp_server --cov=cli --cov-report=term-missing

lint:
	ruff check context_refactor tests cli mcp_server token_report.py

format:
	ruff format --check context_refactor tests cli mcp_server token_report.py

format-fix:
	ruff format context_refactor tests cli mcp_server token_report.py

type-check:
	mypy context_refactor mcp_server cli --ignore-missing-imports

ci: lint type-check test
	@echo "✓ All CI checks passed!"

clean:
	rm -rf build dist *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .mypy_cache .ruff_cache .pytest_cache
	rm -rf htmlcov .coverage coverage.xml

all: install-dev format-fix lint type-check test
	@echo "✓ All checks completed successfully!"
