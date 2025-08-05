"""
MetaWalletGen CLI - A secure command-line tool for generating Ethereum-compatible wallets.

This package provides functionality for:
- Generating Ethereum wallets using BIP-39/BIP-44 standards
- Batch wallet creation and management
- Encrypted storage of wallet data
- Multiple output formats (JSON, CSV, encrypted)
- MetaMask compatibility
"""

__version__ = "1.0.0"
__author__ = "JustineDevs"
__email__ = "contact@justinedevs.com"

from .core.wallet_generator import WalletGenerator
from .core.storage_manager import StorageManager
from .core.encryption import EncryptionManager

__all__ = [
    "WalletGenerator",
    "StorageManager", 
    "EncryptionManager",
] 