#!/usr/bin/env python3
"""
Simple demo of MetaWalletGen functionality
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def demo_wallet_generation():
    """Demo wallet generation functionality"""
    try:
        print("🎯 MetaWalletGen Demo")
        print("=" * 40)
        
        # Import core functionality
        from metawalletgen.core.wallet_generator import WalletGenerator
        from metawalletgen.core.storage_manager import StorageManager
        
        print("1. Initializing wallet generator...")
        generator = WalletGenerator()
        print("   ✓ Wallet generator ready")
        
        print("\n2. Generating a new wallet...")
        wallet = generator.generate_new_wallet()
        print(f"   ✓ Address: {wallet.address}")
        print(f"   ✓ Private Key: {wallet.private_key[:20]}...")
        print(f"   ✓ Mnemonic: {wallet.mnemonic[:30]}...")
        print(f"   ✓ Network: {wallet.network}")
        
        print("\n3. Testing storage...")
        storage = StorageManager()
        wallets = [wallet]
        
        # Save to JSON
        json_file = storage.save_wallets_json(wallets, "demo_wallet.json")
        print(f"   ✓ Saved to: {json_file}")
        
        # Save to CSV
        csv_file = storage.save_wallets_csv(wallets, "demo_wallet.csv")
        print(f"   ✓ Saved to: {csv_file}")
        
        print("\n4. Generating multiple wallets...")
        batch_wallets = generator.generate_batch_wallets(3)
        print(f"   ✓ Generated {len(batch_wallets)} wallets")
        
        for i, w in enumerate(batch_wallets, 1):
            print(f"   Wallet {i}: {w.address[:10]}...")
        
        print("\n" + "=" * 40)
        print("🎉 Demo completed successfully!")
        print("\nGenerated files:")
        print(f"  - {json_file}")
        print(f"  - {csv_file}")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please install dependencies: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    demo_wallet_generation() 