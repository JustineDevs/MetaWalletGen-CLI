@echo off
REM MetaWalletGen CLI - Windows Build Script
REM Equivalent to Makefile for Windows users

setlocal enabledelayedexpansion

REM Set variables
set PYTHON=python
set PIP=pip
set PACKAGE_NAME=metawalletgen-cli
set BUILD_DIR=build
set DIST_DIR=dist

REM Default target
if "%1"=="" goto help

REM Parse command
if "%1"=="help" goto help
if "%1"=="install" goto install
if "%1"=="install-dev" goto install-dev
if "%1"=="clean" goto clean
if "%1"=="clean-all" goto clean-all
if "%1"=="format" goto format
if "%1"=="test" goto test
if "%1"=="test-cov" goto test-cov
if "%1"=="lint" goto lint
if "%1"=="security-check" goto security-check
if "%1"=="build" goto build
if "%1"=="package" goto package
if "%1"=="docker-build" goto docker-build
if "%1"=="deploy-test" goto deploy-test
if "%1"=="deploy-prod" goto deploy-prod
if "%1"=="docs" goto docs
if "%1"=="setup-dev" goto setup-dev
if "%1"=="pre-commit" goto pre-commit
if "%1"=="benchmark" goto benchmark
if "%1"=="dev" goto dev
if "%1"=="quick" goto quick
if "%1"=="info" goto info
if "%1"=="ci-test" goto ci-test
if "%1"=="ci-build" goto ci-build

echo Unknown command: %1
goto help

:help
echo MetaWalletGen CLI - Available Commands
echo ======================================
echo.
echo 📦 Installation:
echo   install          Install package in development mode
echo   install-dev      Install with development dependencies
echo.
echo 🧹 Maintenance:
echo   clean            Clean build artifacts
echo   clean-all        Clean all generated files
echo   format           Format code with black and isort
echo.
echo 🧪 Testing ^& Quality:
echo   test             Run test suite
echo   test-cov         Run tests with coverage
echo   lint             Run linting checks
echo   security-check   Run security audits
echo.
echo 🔨 Building:
echo   build            Build source and wheel distributions
echo   package          Build and check package quality
echo.
echo 🐳 Docker:
echo   docker-build     Build Docker image
echo.
echo 🚀 Deployment:
echo   deploy-test      Deploy to TestPyPI
echo   deploy-prod      Deploy to PyPI ^(production^)
echo.
echo 📚 Documentation:
echo   docs             Build documentation
echo.
echo 🔧 Development:
echo   setup-dev        Set up development environment
echo   pre-commit       Install pre-commit hooks
echo   benchmark        Run performance benchmarks
echo   dev              Complete development workflow
echo   quick            Quick check
echo.
echo 📋 Information:
echo   info             Show package information
echo.
echo 🚀 CI/CD:
echo   ci-test          Run CI tests
echo   ci-build         CI build
echo.
echo Examples:
echo   build.bat install-dev
echo   build.bat test
echo   build.bat build
echo   build.bat clean
goto end

:install
echo 📦 Installing MetaWalletGen CLI...
%PIP% install -e .
goto end

:install-dev
echo 🔧 Installing with development dependencies...
%PIP% install -e ".[dev]"
goto end

:clean
echo 🧹 Cleaning build artifacts...
if exist %BUILD_DIR% rmdir /s /q %BUILD_DIR%
if exist %DIST_DIR% rmdir /s /q %DIST_DIR%
if exist *.egg-info rmdir /s /q *.egg-info
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
for /r . %%f in (*.pyc) do @if exist "%%f" del "%%f"
goto end

:clean-all
call :clean
echo 🧹 Deep cleaning...
if exist .pytest_cache rmdir /s /q .pytest_cache
if exist .coverage del .coverage
if exist htmlcov rmdir /s /q htmlcov
if exist .mypy_cache rmdir /s /q .mypy_cache
if exist .tox rmdir /s /q .tox
if exist .venv rmdir /s /q .venv
if exist venv rmdir /s /q venv
if exist env rmdir /s /q env
goto end

:format
echo 🎨 Formatting code...
%PIP% install black isort
black metawalletgen tests
isort metawalletgen tests
goto end

:test
echo 🧪 Running test suite...
%PIP% install pytest pytest-cov
pytest tests/ -v
goto end

:test-cov
echo 📊 Running tests with coverage...
%PIP% install pytest pytest-cov
pytest tests/ --cov=metawalletgen --cov-report=html --cov-report=term-missing
goto end

:lint
echo 🔍 Running linting checks...
%PIP% install flake8 black isort mypy
flake8 metawalletgen tests
black --check metawalletgen tests
isort --check-only metawalletgen tests
mypy metawalletgen
goto end

:security-check
echo 🔒 Running security checks...
%PIP% install bandit safety pip-audit
bandit -r metawalletgen -f json -o bandit-report.json
safety check --json --output safety-report.json
pip-audit --format json --output pip-audit-report.json
goto end

:build
echo 🔨 Building package...
%PIP% install build wheel
%PYTHON% -m build --sdist --wheel
goto end

:package
call :build
echo 🔍 Checking package quality...
%PIP% install twine check-wheel-contents
twine check dist/*
check-wheel-contents dist/*.whl
goto end

:docker-build
echo 🐳 Building Docker image...
docker build -t metawalletgen/cli:latest .
goto end

:deploy-test
echo 🚀 Deploying to TestPyPI...
%PIP% install twine
twine upload --repository testpypi dist/*
goto end

:deploy-prod
echo 🚀 Deploying to PyPI...
%PIP% install twine
twine upload dist/*
goto end

:docs
echo 📚 Building documentation...
%PIP% install sphinx sphinx-rtd-theme myst-parser
cd docs
make html
cd ..
goto end

:setup-dev
echo 🔧 Setting up development environment...
%PIP% install -e ".[dev]"
pre-commit install
goto end

:pre-commit
echo 🔧 Installing pre-commit hooks...
%PIP% install pre-commit
pre-commit install
goto end

:benchmark
echo 🏃 Running performance benchmarks...
%PIP% install pytest-benchmark
pytest --benchmark-only --benchmark-sort=mean
goto end

:dev
call :clean
call :format
call :lint
call :test
echo ✅ Development workflow completed!
goto end

:quick
call :format
call :lint
call :test
echo ⚡ Quick check completed!
goto end

:info
echo 📋 Package Information:
echo   Name: %PACKAGE_NAME%
echo   Python: %PYTHON%
echo   Location: %CD%
goto end

:ci-test
echo 🧪 Running CI tests...
%PIP% install -e ".[dev]"
pytest tests/ --cov=metawalletgen --cov-report=xml --cov-report=html --cov-report=term-missing
flake8 metawalletgen tests
black --check metawalletgen tests
mypy metawalletgen
goto end

:ci-build
echo 🔨 CI build...
%PIP% install build wheel twine
%PYTHON% -m build --sdist --wheel
twine check dist/*
goto end

:end
echo.
echo Build script completed.
pause
