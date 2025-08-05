#!/usr/bin/env python3
"""
MetaWalletGen CLI Installation Script

This script helps install and set up the MetaWalletGen CLI tool.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible."""
    print("Checking Python version...")
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} is compatible")
    return True


def check_pip():
    """Check if pip is available."""
    print("\nChecking pip...")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      check=True, capture_output=True)
        print("✅ pip is available")
        return True
    except subprocess.CalledProcessError:
        print("❌ pip is not available")
        return False


def install_dependencies():
    """Install required dependencies."""
    print("\nInstalling dependencies...")
    
    try:
        # Install from requirements.txt
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def install_package():
    """Install the package in development mode."""
    print("\nInstalling MetaWalletGen CLI...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-e", "."
        ], check=True)
        print("✅ MetaWalletGen CLI installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install package: {e}")
        return False


def run_tests():
    """Run installation tests."""
    print("\nRunning installation tests...")
    
    try:
        subprocess.run([sys.executable, "test_installation.py"], check=True)
        print("✅ All tests passed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Some tests failed")
        return False


def create_directories():
    """Create necessary directories."""
    print("\nCreating directories...")
    
    directories = ["wallets", "examples", "tests"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")


def show_usage_examples():
    """Show usage examples."""
    print("\n" + "="*50)
    print("MetaWalletGen CLI Installation Complete!")
    print("="*50)
    
    print("\nUsage Examples:")
    print("1. Generate a single wallet:")
    print("   python -m metawalletgen.cli.main generate")
    
    print("\n2. Generate multiple wallets:")
    print("   python -m metawalletgen.cli.main generate --count 5")
    
    print("\n3. Generate encrypted wallets:")
    print("   python -m metawalletgen.cli.main generate --count 3 --encrypt")
    
    print("\n4. Import wallet from mnemonic:")
    print("   python -m metawalletgen.cli.main import-wallet --mnemonic 'your phrase here'")
    
    print("\n5. List wallet files:")
    print("   python -m metawalletgen.cli.main list")
    
    print("\n6. Validate mnemonic:")
    print("   python -m metawalletgen.cli.main validate 'your mnemonic phrase'")
    
    print("\n7. Run examples:")
    print("   python examples/basic_usage.py")
    
    print("\nFor more information, see README.md")


def main():
    """Main installation function."""
    print("MetaWalletGen CLI - Installation Script")
    print("="*40)
    
    # Check system requirements
    if not check_python_version():
        sys.exit(1)
    
    if not check_pip():
        print("Please install pip first")
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Install dependencies
    if not install_dependencies():
        print("Failed to install dependencies")
        sys.exit(1)
    
    # Install package
    if not install_package():
        print("Failed to install package")
        sys.exit(1)
    
    # Run tests
    if not run_tests():
        print("Installation tests failed")
        sys.exit(1)
    
    # Show usage examples
    show_usage_examples()
    
    print("\n🎉 Installation completed successfully!")
    print("You can now use the MetaWalletGen CLI tool.")


if __name__ == "__main__":
    main() 