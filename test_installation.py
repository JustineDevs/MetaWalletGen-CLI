#!/usr/bin/env python3
"""
Test Installation Script

This script tests the basic functionality of the MetaWalletGen CLI
to ensure everything is working correctly.
"""

import sys
import os

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        from metawalletgen.core.wallet_generator import WalletGenerator
        from metawalletgen.core.storage_manager import StorageManager
        from metawalletgen.core.encryption import EncryptionManager
        print("✓ Core modules imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import core modules: {e}")
        return False
    
    try:
        from metawalletgen.utils.validators import validate_ethereum_address
        from metawalletgen.utils.formatters import format_address
        print("✓ Utility modules imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import utility modules: {e}")
        return False
    
    return True


def test_wallet_generation():
    """Test basic wallet generation."""
    print("\nTesting wallet generation...")
    
    try:
        from metawalletgen.core.wallet_generator import WalletGenerator
        
        generator = WalletGenerator()
        
        # Test mnemonic generation
        mnemonic = generator.generate_mnemonic()
        print(f"✓ Generated mnemonic: {mnemonic[:20]}...")
        
        # Test wallet creation
        wallet = generator.generate_new_wallet()
        print(f"✓ Generated wallet address: {wallet.address}")
        print(f"✓ Generated private key: {wallet.private_key[:10]}...")
        
        # Test validation
        is_valid_mnemonic = generator.validate_mnemonic(mnemonic)
        print(f"✓ Mnemonic validation: {is_valid_mnemonic}")
        
        is_valid_private_key = generator.validate_private_key(wallet.private_key)
        print(f"✓ Private key validation: {is_valid_private_key}")
        
        return True
    except Exception as e:
        print(f"✗ Wallet generation failed: {e}")
        return False


def test_encryption():
    """Test encryption functionality."""
    print("\nTesting encryption...")
    
    try:
        from metawalletgen.core.encryption import EncryptionManager
        
        encryption = EncryptionManager()
        
        # Test data encryption/decryption
        test_data = "Hello, World!"
        password = "test_password"
        
        encrypted = encryption.encrypt_data(test_data, password)
        decrypted = encryption.decrypt_data(encrypted, password)
        
        if decrypted == test_data:
            print("✓ Encryption/decryption working correctly")
        else:
            print("✗ Encryption/decryption failed")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Encryption test failed: {e}")
        return False


def test_storage():
    """Test storage functionality."""
    print("\nTesting storage...")
    
    try:
        from metawalletgen.core.storage_manager import StorageManager
        from metawalletgen.core.wallet_generator import WalletGenerator
        
        storage = StorageManager()
        generator = WalletGenerator()
        
        # Generate test wallet
        wallet = generator.generate_new_wallet()
        wallets = [wallet]
        
        # Test JSON storage
        filepath = storage.save_wallets_json(wallets, "test_wallets.json")
        print(f"✓ Saved wallets to: {filepath}")
        
        # Test loading
        loaded_wallets = storage.load_wallets_json("test_wallets.json")
        print(f"✓ Loaded {len(loaded_wallets)} wallets")
        
        # Clean up
        if os.path.exists("test_wallets.json"):
            os.remove("test_wallets.json")
        
        return True
    except Exception as e:
        print(f"✗ Storage test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("MetaWalletGen CLI - Installation Test")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_wallet_generation,
        test_encryption,
        test_storage
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed! Installation is successful.")
        return 0
    else:
        print("✗ Some tests failed. Please check the installation.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 