# CROAK Makefile
# Computer Recognition Orchestration Agent Kit
#
# Usage:
#   make install      - Install CROAK
#   make dev          - Install in development mode
#   make test         - Run tests
#   make lint         - Run linting
#   make format       - Format code
#   make clean        - Clean build artifacts
#   make help         - Show this help

.PHONY: help install dev test lint format clean docs build publish

# Default target
.DEFAULT_GOAL := help

# Python interpreter
PYTHON := python3
PIP := pip

# Directories
SRC_DIR := src/croak
TEST_DIR := tests
DOCS_DIR := docs
BUILD_DIR := dist

# Colors for output
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

#==============================================================================
# HELP
#==============================================================================

help: ## Show this help message
	@echo ""
	@echo "$(CYAN)CROAK - Computer Recognition Orchestration Agent Kit$(NC)"
	@echo ""
	@echo "$(GREEN)Available targets:$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf ""} /^[a-zA-Z_-]+:.*?##/ { printf "  $(CYAN)%-15s$(NC) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""

#==============================================================================
# INSTALLATION
#==============================================================================

install: ## Install CROAK package
	@echo "$(CYAN)Installing CROAK...$(NC)"
	$(PIP) install -e .
	@echo "$(GREEN)CROAK installed successfully!$(NC)"

dev: ## Install CROAK in development mode with all dev dependencies
	@echo "$(CYAN)Installing CROAK in development mode...$(NC)"
	$(PIP) install -e ".[dev]"
	@echo "$(GREEN)CROAK development environment ready!$(NC)"

deps: ## Install only dependencies (no package install)
	@echo "$(CYAN)Installing dependencies...$(NC)"
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)Dependencies installed!$(NC)"

venv: ## Create virtual environment
	@echo "$(CYAN)Creating virtual environment...$(NC)"
	$(PYTHON) -m venv venv
	@echo "$(GREEN)Virtual environment created!$(NC)"
	@echo "$(YELLOW)Activate with: source venv/bin/activate$(NC)"

#==============================================================================
# TESTING
#==============================================================================

test: ## Run all tests
	@echo "$(CYAN)Running tests...$(NC)"
	pytest $(TEST_DIR) -v

test-cov: ## Run tests with coverage report
	@echo "$(CYAN)Running tests with coverage...$(NC)"
	pytest $(TEST_DIR) -v --cov=$(SRC_DIR) --cov-report=html --cov-report=term
	@echo "$(GREEN)Coverage report generated in htmlcov/$(NC)"

test-fast: ## Run tests without slow tests
	@echo "$(CYAN)Running fast tests...$(NC)"
	pytest $(TEST_DIR) -v -m "not slow"

test-watch: ## Run tests in watch mode
	@echo "$(CYAN)Running tests in watch mode...$(NC)"
	ptw $(TEST_DIR) -- -v

#==============================================================================
# CODE QUALITY
#==============================================================================

lint: ## Run linting checks
	@echo "$(CYAN)Running linting...$(NC)"
	ruff check $(SRC_DIR) $(TEST_DIR)
	@echo "$(GREEN)Linting passed!$(NC)"

lint-fix: ## Run linting and auto-fix issues
	@echo "$(CYAN)Running linting with auto-fix...$(NC)"
	ruff check $(SRC_DIR) $(TEST_DIR) --fix
	@echo "$(GREEN)Linting fixes applied!$(NC)"

format: ## Format code with ruff
	@echo "$(CYAN)Formatting code...$(NC)"
	ruff format $(SRC_DIR) $(TEST_DIR)
	@echo "$(GREEN)Code formatted!$(NC)"

format-check: ## Check code formatting without changes
	@echo "$(CYAN)Checking code formatting...$(NC)"
	ruff format $(SRC_DIR) $(TEST_DIR) --check

typecheck: ## Run type checking with mypy
	@echo "$(CYAN)Running type checking...$(NC)"
	mypy $(SRC_DIR)
	@echo "$(GREEN)Type checking passed!$(NC)"

check: lint typecheck test ## Run all checks (lint, typecheck, test)
	@echo "$(GREEN)All checks passed!$(NC)"

#==============================================================================
# DOCUMENTATION
#==============================================================================

docs: ## Build documentation
	@echo "$(CYAN)Building documentation...$(NC)"
	cd $(DOCS_DIR) && make html
	@echo "$(GREEN)Documentation built in $(DOCS_DIR)/_build/html/$(NC)"

docs-serve: ## Serve documentation locally
	@echo "$(CYAN)Serving documentation...$(NC)"
	cd $(DOCS_DIR)/_build/html && $(PYTHON) -m http.server 8000

#==============================================================================
# BUILD & PUBLISH
#==============================================================================

build: clean ## Build distribution packages
	@echo "$(CYAN)Building distribution packages...$(NC)"
	$(PYTHON) -m build
	@echo "$(GREEN)Build complete! Packages in $(BUILD_DIR)/$(NC)"

publish-test: build ## Publish to TestPyPI
	@echo "$(CYAN)Publishing to TestPyPI...$(NC)"
	$(PYTHON) -m twine upload --repository testpypi $(BUILD_DIR)/*
	@echo "$(GREEN)Published to TestPyPI!$(NC)"

publish: build ## Publish to PyPI (requires authentication)
	@echo "$(CYAN)Publishing to PyPI...$(NC)"
	$(PYTHON) -m twine upload $(BUILD_DIR)/*
	@echo "$(GREEN)Published to PyPI!$(NC)"

#==============================================================================
# CLEANUP
#==============================================================================

clean: ## Clean build artifacts
	@echo "$(CYAN)Cleaning build artifacts...$(NC)"
	rm -rf $(BUILD_DIR)
	rm -rf *.egg-info
	rm -rf $(SRC_DIR)/*.egg-info
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov
	rm -rf .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)Clean complete!$(NC)"

clean-all: clean ## Clean everything including venv
	@echo "$(CYAN)Cleaning everything...$(NC)"
	rm -rf venv
	@echo "$(GREEN)Full clean complete!$(NC)"

#==============================================================================
# CROAK-SPECIFIC
#==============================================================================

validate-agents: ## Validate all agent YAML files
	@echo "$(CYAN)Validating agent definitions...$(NC)"
	$(PYTHON) -m croak.core.validate_agents agents/
	@echo "$(GREEN)All agents valid!$(NC)"

validate-workflows: ## Validate all workflow YAML files
	@echo "$(CYAN)Validating workflow definitions...$(NC)"
	$(PYTHON) -m croak.core.validate_workflows workflows/
	@echo "$(GREEN)All workflows valid!$(NC)"

validate: validate-agents validate-workflows ## Validate all YAML files
	@echo "$(GREEN)All validations passed!$(NC)"

demo: ## Run demo with sample data
	@echo "$(CYAN)Running CROAK demo...$(NC)"
	cd examples/retail-detection && croak status
	@echo "$(GREEN)Demo complete!$(NC)"

#==============================================================================
# DEVELOPMENT
#==============================================================================

setup-hooks: ## Setup git pre-commit hooks
	@echo "$(CYAN)Setting up pre-commit hooks...$(NC)"
	pre-commit install
	@echo "$(GREEN)Pre-commit hooks installed!$(NC)"

run-hooks: ## Run pre-commit hooks on all files
	@echo "$(CYAN)Running pre-commit hooks...$(NC)"
	pre-commit run --all-files

update-deps: ## Update dependencies to latest versions
	@echo "$(CYAN)Updating dependencies...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) install --upgrade -e ".[dev]"
	@echo "$(GREEN)Dependencies updated!$(NC)"

#==============================================================================
# CI/CD HELPERS
#==============================================================================

ci-test: ## Run tests for CI (with JUnit output)
	@echo "$(CYAN)Running CI tests...$(NC)"
	pytest $(TEST_DIR) -v --junitxml=test-results.xml --cov=$(SRC_DIR) --cov-report=xml

ci-lint: ## Run linting for CI
	@echo "$(CYAN)Running CI linting...$(NC)"
	ruff check $(SRC_DIR) $(TEST_DIR) --output-format=github

ci: ci-lint ci-test ## Run all CI checks
	@echo "$(GREEN)CI checks complete!$(NC)"
