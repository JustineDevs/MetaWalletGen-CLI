@echo off
REM MetaWalletGen CLI - Windows Installer
REM Version: 2.0.0

echo.
echo ========================================
echo   MetaWalletGen CLI Installer
echo   Version: 2.0.0
echo ========================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo Python found: 
python --version
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install package
echo Installing MetaWalletGen CLI...
python -m pip install --user dist/metawalletgen_cli-2.0.0-py3-none-any.whl

if errorlevel 1 (
    echo ERROR: Installation failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo You can now use:
echo   metawalletgen --help
echo   mwg --help
echo.
echo For more information, visit:
echo   https://github.com/metawalletgen/cli
echo.
pause
