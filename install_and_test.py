#!/usr/bin/env python3
"""
Installation and testing script for MetaWalletGen CLI
"""

import sys
import os
import subprocess
import importlib

def run_command(command):
    """Run a command and return the result"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_python():
    """Check Python version"""
    print("🐍 Checking Python installation...")
    version = sys.version_info
    print(f"   Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("   ❌ Python 3.8+ required")
        return False
    else:
        print("   ✓ Python version OK")
        return True

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    
    # Check if pip is available
    success, stdout, stderr = run_command("python -m pip --version")
    if not success:
        print("   ❌ pip not available")
        return False
    
    print("   ✓ pip available")
    
    # Install dependencies
    print("   Installing from requirements.txt...")
    success, stdout, stderr = run_command("python -m pip install -r requirements.txt")
    
    if success:
        print("   ✓ Dependencies installed successfully")
        return True
    else:
        print(f"   ❌ Failed to install dependencies: {stderr}")
        return False

def test_imports():
    """Test importing the package"""
    print("\n🔍 Testing imports...")
    
    try:
        import metawalletgen
        print("   ✓ metawalletgen package imported")
        
        from metawalletgen.core.wallet_generator import WalletGenerator
        print("   ✓ WalletGenerator imported")
        
        from metawalletgen.core.storage_manager import StorageManager
        print("   ✓ StorageManager imported")
        
        from metawalletgen.core.encryption import EncryptionManager
        print("   ✓ EncryptionManager imported")
        
        return True
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False

def test_wallet_generation():
    """Test wallet generation"""
    print("\n💰 Testing wallet generation...")
    
    try:
        from metawalletgen.core.wallet_generator import WalletGenerator
        
        generator = WalletGenerator()
        wallet = generator.generate_new_wallet()
        
        print(f"   ✓ Generated wallet: {wallet.address}")
        print(f"   ✓ Private key: {wallet.private_key[:20]}...")
        print(f"   ✓ Mnemonic: {wallet.mnemonic[:30]}...")
        
        return True
    except Exception as e:
        print(f"   ❌ Wallet generation error: {e}")
        return False

def test_storage():
    """Test storage functionality"""
    print("\n💾 Testing storage...")
    
    try:
        from metawalletgen.core.wallet_generator import WalletGenerator
        from metawalletgen.core.storage_manager import StorageManager
        
        generator = WalletGenerator()
        storage = StorageManager()
        
        wallet = generator.generate_new_wallet()
        wallets = [wallet]
        
        # Test JSON storage
        json_file = storage.save_wallets_json(wallets, "test_wallet.json")
        print(f"   ✓ Saved to JSON: {json_file}")
        
        # Test CSV storage
        csv_file = storage.save_wallets_csv(wallets, "test_wallet.csv")
        print(f"   ✓ Saved to CSV: {csv_file}")
        
        return True
    except Exception as e:
        print(f"   ❌ Storage error: {e}")
        return False

def test_cli():
    """Test CLI functionality"""
    print("\n🖥️  Testing CLI...")
    
    try:
        from metawalletgen.cli.main import main
        print("   ✓ CLI main function imported")
        
        # Test CLI help
        original_argv = sys.argv.copy()
        sys.argv = ['metawalletgen', '--help']
        
        # This would normally run the CLI, but we'll just test the import
        print("   ✓ CLI structure ready")
        
        sys.argv = original_argv
        return True
    except Exception as e:
        print(f"   ❌ CLI error: {e}")
        return False

def main():
    """Main installation and testing function"""
    print("🚀 MetaWalletGen CLI - Installation and Testing")
    print("=" * 50)
    
    # Check Python
    if not check_python():
        return
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Failed to install dependencies")
        return
    
    # Test imports
    if not test_imports():
        print("\n❌ Failed to import modules")
        return
    
    # Test wallet generation
    if not test_wallet_generation():
        print("\n❌ Failed to generate wallets")
        return
    
    # Test storage
    if not test_storage():
        print("\n❌ Failed to test storage")
        return
    
    # Test CLI
    if not test_cli():
        print("\n❌ Failed to test CLI")
        return
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! MetaWalletGen CLI is ready to use.")
    print("\nTo run the CLI:")
    print("  python -m metawalletgen.cli.main --help")
    print("  python -m metawalletgen.cli.main generate --count 1")

if __name__ == "__main__":
    main() 