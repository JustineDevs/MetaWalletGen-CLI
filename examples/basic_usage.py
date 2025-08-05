#!/usr/bin/env python3
"""
Basic Usage Example

This script demonstrates basic usage of the MetaWalletGen CLI
functionality programmatically.
"""

import sys
import os

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from metawalletgen.core.wallet_generator import WalletGenerator
from metawalletgen.core.storage_manager import StorageManager
from metawalletgen.core.encryption import EncryptionManager


def example_generate_wallets():
    """Example: Generate multiple wallets."""
    print("=== Generating Wallets ===")
    
    # Initialize components
    generator = WalletGenerator(network="mainnet")
    storage = StorageManager()
    
    # Generate 3 wallets
    wallets = generator.generate_batch_wallets(3)
    
    print(f"Generated {len(wallets)} wallets:")
    for i, wallet in enumerate(wallets, 1):
        print(f"  Wallet {i}:")
        print(f"    Address: {wallet.address}")
        print(f"    Private Key: {wallet.private_key[:10]}...")
        print(f"    Mnemonic: {wallet.mnemonic[:30]}...")
        print()
    
    # Save to JSON file
    filepath = storage.save_wallets_json(wallets, "example_wallets.json")
    print(f"Saved wallets to: {filepath}")
    
    return wallets


def example_import_wallet():
    """Example: Import wallet from mnemonic."""
    print("\n=== Importing Wallet ===")
    
    generator = WalletGenerator()
    
    # Example mnemonic (DO NOT USE IN PRODUCTION)
    mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    
    # Import wallet
    wallet = generator.create_wallet_from_mnemonic(mnemonic)
    
    print(f"Imported wallet:")
    print(f"  Address: {wallet.address}")
    print(f"  Private Key: {wallet.private_key}")
    print(f"  Mnemonic: {wallet.mnemonic}")
    
    return wallet


def example_encrypted_storage():
    """Example: Encrypted storage."""
    print("\n=== Encrypted Storage ===")
    
    generator = WalletGenerator()
    storage = StorageManager()
    
    # Generate a wallet
    wallet = generator.generate_new_wallet()
    wallets = [wallet]
    
    # Save with encryption
    password = "my_secure_password"
    filepath = storage.save_wallets_json(
        wallets, "encrypted_wallets.json", 
        encrypt=True, password=password
    )
    
    print(f"Saved encrypted wallet to: {filepath}")
    
    # Load encrypted wallet
    loaded_wallets = storage.load_wallets_json(
        "encrypted_wallets.json", 
        decrypt=True, password=password
    )
    
    print(f"Loaded {len(loaded_wallets)} encrypted wallet(s)")
    print(f"Address: {loaded_wallets[0].address}")
    
    return wallets


def example_validation():
    """Example: Validation functions."""
    print("\n=== Validation Examples ===")
    
    generator = WalletGenerator()
    
    # Test mnemonic validation
    valid_mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    invalid_mnemonic = "invalid mnemonic phrase"
    
    print(f"Valid mnemonic: {generator.validate_mnemonic(valid_mnemonic)}")
    print(f"Invalid mnemonic: {generator.validate_mnemonic(invalid_mnemonic)}")
    
    # Test private key validation
    valid_private_key = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    invalid_private_key = "invalid_key"
    
    print(f"Valid private key: {generator.validate_private_key(valid_private_key)}")
    print(f"Invalid private key: {generator.validate_private_key(invalid_private_key)}")
    
    # Test address validation
    valid_address = "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6"
    invalid_address = "invalid_address"
    
    print(f"Valid address: {generator.verify_address_checksum(valid_address)}")
    print(f"Invalid address: {generator.verify_address_checksum(invalid_address)}")


def example_batch_processing():
    """Example: Batch processing with progress."""
    print("\n=== Batch Processing ===")
    
    generator = WalletGenerator()
    storage = StorageManager()
    
    # Generate many wallets
    count = 10
    print(f"Generating {count} wallets...")
    
    wallets = generator.generate_batch_wallets(count)
    
    # Save in different formats
    json_file = storage.save_wallets_json(wallets, "batch_wallets.json")
    csv_file = storage.save_wallets_csv(wallets, "batch_wallets.csv")
    
    print(f"Saved to JSON: {json_file}")
    print(f"Saved to CSV: {csv_file}")
    
    # Generate summary
    summary_file = storage.save_wallet_summary(wallets, "batch_summary.txt")
    print(f"Summary: {summary_file}")
    
    return wallets


def cleanup_example_files():
    """Clean up example files."""
    files_to_remove = [
        "example_wallets.json",
        "encrypted_wallets.json",
        "batch_wallets.json",
        "batch_wallets.csv",
        "batch_summary.txt"
    ]
    
    for filename in files_to_remove:
        if os.path.exists(filename):
            os.remove(filename)
            print(f"Removed: {filename}")


def main():
    """Run all examples."""
    print("MetaWalletGen CLI - Basic Usage Examples")
    print("=" * 50)
    
    try:
        # Run examples
        example_generate_wallets()
        example_import_wallet()
        example_encrypted_storage()
        example_validation()
        example_batch_processing()
        
        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        
        # Ask if user wants to clean up
        response = input("\nClean up example files? (y/n): ")
        if response.lower() in ['y', 'yes']:
            cleanup_example_files()
            print("Cleanup completed.")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 