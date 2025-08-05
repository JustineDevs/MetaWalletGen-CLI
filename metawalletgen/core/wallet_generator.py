"""
Wallet Generator Module

This module handles the generation of Ethereum-compatible wallets using
BIP-39 mnemonics and BIP-44 derivation paths, following MetaMask standards.
"""

import secrets
import hashlib
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from hdwallet import HDWallet
from hdwallet.cryptocurrencies import Ethereum
from hdwallet.derivations import BIP44Derivation
from hdwallet.utils import generate_mnemonic
from eth_account import Account
from web3 import Web3


@dataclass
class WalletData:
    """Data class for wallet information."""
    address: str
    private_key: str
    mnemonic: str
    derivation_path: str
    network: str
    public_key: str = ""
    
    def to_dict(self) -> Dict[str, str]:
        """Convert wallet data to dictionary."""
        return {
            "address": self.address,
            "private_key": self.private_key,
            "mnemonic": self.mnemonic,
            "derivation_path": self.derivation_path,
            "network": self.network,
            "public_key": self.public_key
        }


class WalletGenerator:
    """
    Main wallet generator class that handles Ethereum wallet creation
    using BIP-39/BIP-44 standards with MetaMask compatibility.
    """
    
    def __init__(self, network: str = "mainnet"):
        """
        Initialize the wallet generator.
        
        Args:
            network: The network to generate wallets for (mainnet/testnet)
        """
        self.network = network
        self.account = Account()
        self.w3 = Web3()
        
        # Default derivation path for Ethereum (MetaMask standard)
        self.default_derivation = "m/44'/60'/0'/0/0"
        
    def generate_mnemonic(self, strength: int = 128) -> str:
        """
        Generate a cryptographically secure mnemonic phrase.
        
        Args:
            strength: Entropy strength in bits (128, 160, 192, 224, 256)
            
        Returns:
            BIP-39 mnemonic phrase
        """
        if strength not in [128, 160, 192, 224, 256]:
            raise ValueError("Strength must be one of: 128, 160, 192, 224, 256")
        
        return generate_mnemonic(language="english", strength=strength)
    
    def create_wallet_from_mnemonic(
        self, 
        mnemonic: str, 
        derivation_path: Optional[str] = None,
        index: int = 0
    ) -> WalletData:
        """
        Create a wallet from an existing mnemonic phrase.
        
        Args:
            mnemonic: BIP-39 mnemonic phrase
            derivation_path: Custom derivation path (optional)
            index: Account index for derivation
            
        Returns:
            WalletData object containing wallet information
        """
        if derivation_path is None:
            derivation_path = self.default_derivation
            
        # Create HD wallet using hdwallet library
        hd_wallet = HDWallet(cryptocurrency=Ethereum)
        
        # Set the mnemonic
        hd_wallet.from_mnemonic(mnemonic=mnemonic)
        
        # Set derivation path
        derivation = BIP44Derivation(
            cryptocurrency=Ethereum,
            account=0,
            change=False,
            address=index
        )
        hd_wallet.from_derivation(derivation=derivation)
        
        # Get wallet data
        private_key = hd_wallet.private_key()
        address = hd_wallet.address()
        public_key = hd_wallet.public_key()
        
        return WalletData(
            address=address,
            private_key=f"0x{private_key}",
            mnemonic=mnemonic,
            derivation_path=derivation_path,
            network=self.network,
            public_key=public_key
        )
    
    def create_wallet_from_private_key(self, private_key: str) -> WalletData:
        """
        Create a wallet from an existing private key.
        
        Args:
            private_key: Private key in hex format (with or without 0x prefix)
            
        Returns:
            WalletData object containing wallet information
        """
        # Ensure private key has 0x prefix
        if not private_key.startswith("0x"):
            private_key = f"0x{private_key}"
            
        # Create account from private key
        account = self.account.from_key(private_key)
        
        return WalletData(
            address=account.address,
            private_key=private_key,
            mnemonic="",  # No mnemonic when importing from private key
            derivation_path="",  # No derivation path when importing from private key
            network=self.network,
            public_key=account.publickey.hex()
        )
    
    def generate_new_wallet(self, index: int = 0) -> WalletData:
        """
        Generate a completely new wallet with random mnemonic.
        
        Args:
            index: Account index for derivation
            
        Returns:
            WalletData object containing wallet information
        """
        # Generate new mnemonic
        mnemonic = self.generate_mnemonic()
        
        # Create wallet from mnemonic
        return self.create_wallet_from_mnemonic(mnemonic, index=index)
    
    def generate_batch_wallets(self, count: int, start_index: int = 0) -> List[WalletData]:
        """
        Generate multiple wallets in batch.
        
        Args:
            count: Number of wallets to generate
            start_index: Starting index for wallet derivation
            
        Returns:
            List of WalletData objects
        """
        wallets = []
        
        for i in range(count):
            wallet = self.generate_new_wallet(index=start_index + i)
            wallets.append(wallet)
            
        return wallets
    
    def validate_mnemonic(self, mnemonic: str) -> bool:
        """
        Validate a mnemonic phrase.
        
        Args:
            mnemonic: BIP-39 mnemonic phrase to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Try to create HD wallet from mnemonic
            hd_wallet = HDWallet(cryptocurrency=Ethereum)
            hd_wallet.from_mnemonic(mnemonic=mnemonic)
            return True
        except Exception:
            return False
    
    def validate_private_key(self, private_key: str) -> bool:
        """
        Validate a private key.
        
        Args:
            private_key: Private key in hex format
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Ensure private key has 0x prefix
            if not private_key.startswith("0x"):
                private_key = f"0x{private_key}"
                
            # Try to create account from private key
            self.account.from_key(private_key)
            return True
        except Exception:
            return False
    
    def get_wallet_balance(self, address: str, rpc_url: str) -> str:
        """
        Get wallet balance from an RPC endpoint.
        
        Args:
            address: Wallet address
            rpc_url: RPC endpoint URL
            
        Returns:
            Balance in wei as string
        """
        try:
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            balance = w3.eth.get_balance(address)
            return str(balance)
        except Exception as e:
            raise ValueError(f"Failed to get balance: {str(e)}")
    
    def verify_address_checksum(self, address: str) -> bool:
        """
        Verify if an address has valid EIP-55 checksum.
        
        Args:
            address: Ethereum address to verify
            
        Returns:
            True if checksum is valid, False otherwise
        """
        try:
            return self.w3.is_checksum_address(address)
        except Exception:
            return False
    
    def to_checksum_address(self, address: str) -> str:
        """
        Convert address to EIP-55 checksum format.
        
        Args:
            address: Ethereum address
            
        Returns:
            Checksummed address
        """
        return self.w3.to_checksum_address(address) 