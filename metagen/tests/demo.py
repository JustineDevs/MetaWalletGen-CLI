#!/usr/bin/env python3
"""
MetaWalletGen CLI Demo

A simple demo showing the basic concepts.
"""

import hashlib
import secrets
import json
from datetime import datetime


def generate_demo_wallet():
    """Generate a demo wallet."""
    # Generate private key
    private_key = secrets.token_hex(32)
    
    # Generate address (simplified)
    address = "0x" + hashlib.sha256(private_key.encode()).hexdigest()[:40]
    
    # Generate mnemonic (simplified)
    words = ["abandon", "ability", "able", "about", "above", "absent", "absorb", "abstract", "absurd", "abuse"]
    mnemonic = " ".join(secrets.choice(words) for _ in range(12))
    
    return {
        "address": address,
        "private_key": "0x" + private_key,
        "mnemonic": mnemonic,
        "derivation_path": "m/44'/60'/0'/0/0",
        "network": "mainnet"
    }


def main():
    """Run the demo."""
    print("MetaWalletGen CLI - Demo")
    print("=" * 30)
    
    # Generate wallets
    wallets = []
    for i in range(3):
        wallet = generate_demo_wallet()
        wallets.append(wallet)
        
        print(f"Wallet {i+1}:")
        print(f"  Address: {wallet['address']}")
        print(f"  Private Key: {wallet['private_key'][:10]}...")
        print(f"  Mnemonic: {wallet['mnemonic'][:30]}...")
        print()
    
    # Save to JSON
    data = {
        "wallets": wallets,
        "count": len(wallets),
        "generated_at": datetime.now().isoformat()
    }
    
    with open("demo_wallets.json", "w") as f:
        json.dump(data, f, indent=2)
    
    print("✅ Demo completed! Check demo_wallets.json")


if __name__ == "__main__":
    main() 