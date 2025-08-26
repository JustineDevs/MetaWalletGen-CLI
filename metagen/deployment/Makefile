# MetaWalletGen CLI - Makefile
# Comprehensive build automation and development tasks

.PHONY: help install install-dev clean build test test-cov lint format security-check package docker-build docker-run deploy clean-all

# Default target
help:
	@echo "MetaWalletGen CLI - Available Commands"
	@echo "======================================"
	@echo ""
	@echo "📦 Installation:"
	@echo "  install          Install package in development mode"
	@echo "  install-dev      Install with development dependencies"
	@echo "  install-user     Install for current user only"
	@echo ""
	@echo "🧹 Maintenance:"
	@echo "  clean            Clean build artifacts"
	@echo "  clean-all        Clean all generated files"
	@echo "  format           Format code with black and isort"
	@echo ""
	@echo "🧪 Testing & Quality:"
	@echo "  test             Run test suite"
	@echo "  test-cov         Run tests with coverage"
	@echo "  test-fast        Run fast tests only"
	@echo "  lint             Run linting checks"
	@echo "  security-check   Run security audits"
	@echo ""
	@echo "🔨 Building:"
	@echo "  build            Build source and wheel distributions"
	@echo "  package          Build and check package quality"
	@echo "  install-pkg      Install from built package"
	@echo ""
	@echo "🐳 Docker:"
	@echo "  docker-build     Build Docker image"
	@echo "  docker-run       Run Docker container"
	@echo "  docker-push      Push Docker image to registry"
	@echo ""
	@echo "🚀 Deployment:"
	@echo "  deploy-test      Deploy to TestPyPI"
	@echo "  deploy-prod      Deploy to PyPI (production)"
	@echo "  release          Create new release"
	@echo ""
	@echo "📚 Documentation:"
	@echo "  docs             Build documentation"
	@echo "  docs-serve       Serve documentation locally"
	@echo ""
	@echo "🔧 Development:"
	@echo "  setup-dev        Set up development environment"
	@echo "  pre-commit       Install pre-commit hooks"
	@echo "  benchmark        Run performance benchmarks"

# Variables
PYTHON := python3
PIP := pip3
PACKAGE_NAME := metawalletgen-cli
VERSION := $(shell python -c "import metawalletgen; print(metawalletgen.__version__)" 2>/dev/null || echo "2.0.0")
BUILD_DIR := build
DIST_DIR := dist
DOCKER_IMAGE := metawalletgen/cli
DOCKER_TAG := $(VERSION)

# Installation
install:
	@echo "📦 Installing MetaWalletGen CLI..."
	$(PIP) install -e .

install-dev:
	@echo "🔧 Installing with development dependencies..."
	$(PIP) install -e ".[dev]"

install-user:
	@echo "👤 Installing for current user..."
	$(PIP) install --user -e .

# Cleaning
clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf $(BUILD_DIR) $(DIST_DIR)
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete

clean-all: clean
	@echo "🧹 Deep cleaning..."
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf .mypy_cache
	rm -rf .tox
	rm -rf .venv
	rm -rf venv
	rm -rf env

# Code formatting
format:
	@echo "🎨 Formatting code..."
	$(PIP) install black isort
	black metawalletgen tests
	isort metawalletgen tests

# Testing
test:
	@echo "🧪 Running test suite..."
	$(PIP) install pytest pytest-cov
	pytest tests/ -v

test-cov:
	@echo "📊 Running tests with coverage..."
	$(PIP) install pytest pytest-cov
	pytest tests/ --cov=metawalletgen --cov-report=html --cov-report=term-missing

test-fast:
	@echo "⚡ Running fast tests..."
	$(PIP) install pytest pytest-cov
	pytest tests/ -m "not slow" -v

# Linting and quality
lint:
	@echo "🔍 Running linting checks..."
	$(PIP) install flake8 black isort mypy
	flake8 metawalletgen tests
	black --check metawalletgen tests
	isort --check-only metawalletgen tests
	mypy metawalletgen

security-check:
	@echo "🔒 Running security checks..."
	$(PIP) install bandit safety pip-audit
	bandit -r metawalletgen -f json -o bandit-report.json || true
	safety check --json --output safety-report.json || true
	pip-audit --format json --output pip-audit-report.json || true

# Building
build:
	@echo "🔨 Building package..."
	$(PIP) install build wheel
	python -m build --sdist --wheel

package: build
	@echo "🔍 Checking package quality..."
	$(PIP) install twine check-wheel-contents
	twine check dist/*
	check-wheel-contents dist/*.whl || true

install-pkg:
	@echo "📦 Installing from built package..."
	$(PIP) install dist/*.whl

# Docker
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .
	docker tag $(DOCKER_IMAGE):$(DOCKER_TAG) $(DOCKER_IMAGE):latest

docker-run:
	@echo "🐳 Running Docker container..."
	docker run -it --rm -v $(PWD)/wallets:/app/wallets $(DOCKER_IMAGE):$(DOCKER_TAG)

docker-push:
	@echo "🚀 Pushing Docker image..."
	docker push $(DOCKER_IMAGE):$(DOCKER_TAG)
	docker push $(DOCKER_IMAGE):latest

# Deployment
deploy-test:
	@echo "🚀 Deploying to TestPyPI..."
	$(PIP) install twine
	twine upload --repository testpypi dist/*

deploy-prod:
	@echo "🚀 Deploying to PyPI..."
	$(PIP) install twine
	twine upload dist/*

release:
	@echo "🏷️ Creating release..."
	@read -p "Enter version number: " version; \
	git tag -a v$$version -m "Release v$$version"; \
	git push origin v$$version

# Documentation
docs:
	@echo "📚 Building documentation..."
	$(PIP) install sphinx sphinx-rtd-theme myst-parser
	cd docs && make html

docs-serve:
	@echo "🌐 Serving documentation..."
	cd docs/_build/html && python -m http.server 8000

# Development setup
setup-dev:
	@echo "🔧 Setting up development environment..."
	$(PIP) install -e ".[dev]"
	pre-commit install

pre-commit:
	@echo "🔧 Installing pre-commit hooks..."
	$(PIP) install pre-commit
	pre-commit install

benchmark:
	@echo "🏃 Running performance benchmarks..."
	$(PIP) install pytest-benchmark
	pytest --benchmark-only --benchmark-sort=mean

# Utility targets
check-deps:
	@echo "📋 Checking dependencies..."
	$(PIP) list --outdated

update-deps:
	@echo "🔄 Updating dependencies..."
	$(PIP) install --upgrade -r requirements.txt

# CI/CD helpers
ci-test:
	@echo "🧪 Running CI tests..."
	$(PIP) install -e ".[dev]"
	pytest tests/ --cov=metawalletgen --cov-report=xml --cov-report=html --cov-report=term-missing
	flake8 metawalletgen tests
	black --check metawalletgen tests
	mypy metawalletgen

ci-build:
	@echo "🔨 CI build..."
	$(PIP) install build wheel twine
	python -m build --sdist --wheel
	twine check dist/*

# Quick development workflow
dev: clean format lint test
	@echo "✅ Development workflow completed!"

quick: format lint test-fast
	@echo "⚡ Quick check completed!"

# Show package info
info:
	@echo "📋 Package Information:"
	@echo "  Name: $(PACKAGE_NAME)"
	@echo "  Version: $(VERSION)"
	@echo "  Python: $(shell $(PYTHON) --version)"
	@echo "  Location: $(shell $(PYTHON) -c "import metawalletgen; print(metawalletgen.__file__)" 2>/dev/null || echo "Not installed")"

# Default target
.DEFAULT_GOAL := help
