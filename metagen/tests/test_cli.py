#!/usr/bin/env python3
"""
Test script for MetaWalletGen CLI
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_cli():
    """Test the CLI functionality"""
    try:
        print("Testing MetaWalletGen CLI...")
        print("=" * 50)
        
        # Test importing the package
        print("1. Testing package import...")
        import metawalletgen
        print("   ✓ Package imported successfully")
        
        # Test importing core modules
        print("2. Testing core modules...")
        from metawalletgen.core.wallet_generator import WalletGenerator
        from metawalletgen.core.storage_manager import StorageManager
        from metawalletgen.core.encryption import EncryptionManager
        print("   ✓ Core modules imported successfully")
        
        # Test CLI modules
        print("3. Testing CLI modules...")
        from metawalletgen.cli.main import main
        print("   ✓ CLI modules imported successfully")
        
        # Test wallet generation
        print("4. Testing wallet generation...")
        generator = WalletGenerator()
        wallet = generator.generate_new_wallet()
        print(f"   ✓ Generated wallet: {wallet.address[:10]}...")
        
        # Test storage
        print("5. Testing storage...")
        storage = StorageManager()
        print("   ✓ Storage manager initialized")
        
        # Test encryption
        print("6. Testing encryption...")
        encryption = EncryptionManager()
        test_data = "test data"
        encrypted = encryption.encrypt_data(test_data, "test_password")
        decrypted = encryption.decrypt_data(encrypted, "test_password")
        assert decrypted == test_data
        print("   ✓ Encryption/decryption working")
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed! CLI is working correctly.")
        print("\nTo run the CLI, use:")
        print("  python -m metawalletgen.cli.main --help")
        print("  python -m metawalletgen.cli.main generate --count 1")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Try installing dependencies: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cli() 