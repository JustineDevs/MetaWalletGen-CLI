"""
MetaWalletGen CLI - Core Module

This module contains the core functionality for wallet generation,
encryption, and storage management.
"""

__version__ = "2.0.0"
__author__ = "MetaWalletGen Team"
__email__ = "team@metawalletgen.com"

from .wallet_generator import WalletGenerator
from .encryption import EncryptionManager
from .storage_manager import StorageManager
from .commands import *
from .main import main

__all__ = [
    'WalletGenerator',
    'EncryptionManager', 
    'StorageManager',
    'main'
] 