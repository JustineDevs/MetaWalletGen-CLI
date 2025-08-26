#!/bin/bash
# MetaWalletGen CLI - Unix Installer
# Version: 2.0.0

set -e

echo
echo "========================================"
echo "  MetaWalletGen CLI Installer"
echo "  Version: 2.0.0"
echo "========================================"
echo

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ first"
    exit 1
fi

echo "Python found:"
python3 --version
echo

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "WARNING: Running as root. This is not recommended."
   read -p "Continue anyway? (y/N): " -n 1 -r
   echo
   if [[ ! $REPLY =~ ^[Yy]$ ]]; then
       exit 1
   fi
fi

# Upgrade pip
echo "Upgrading pip..."
python3 -m pip install --upgrade pip --user

# Install package
echo "Installing MetaWalletGen CLI..."
python3 -m pip install --user dist/metawalletgen_cli-2.0.0-py3-none-any.whl

echo
echo "========================================"
echo "  Installation Complete!"
echo "========================================"
echo
echo "You can now use:"
echo "  metawalletgen --help"
echo "  mwg --help"
echo
echo "For more information, visit:"
echo "  https://github.com/metawalletgen/cli"
echo

# Add to PATH if not already there
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "Adding ~/.local/bin to PATH..."
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    echo "Please restart your terminal or run: source ~/.bashrc"
fi
