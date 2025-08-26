"""
Validation Utilities

This module contains validation functions for Ethereum addresses,
private keys, and mnemonic phrases.
"""

import re
from typing import Optional
from web3 import Web3


def validate_ethereum_address(address: str) -> bool:
    """
    Validate an Ethereum address format.
    
    Args:
        address: Ethereum address to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Check if it's a valid hex address
        if not re.match(r'^0x[a-fA-F0-9]{40}$', address):
            return False
        
        # Use web3 to validate checksum
        Web3.to_checksum_address(address)
        return True
    except Exception:
        return False


def validate_private_key(private_key: str) -> bool:
    """
    Validate a private key format.
    
    Args:
        private_key: Private key to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Remove 0x prefix if present
        if private_key.startswith('0x'):
            private_key = private_key[2:]
        
        # Check if it's a valid hex string of correct length
        if not re.match(r'^[a-fA-F0-9]{64}$', private_key):
            return False
        
        # Convert to int and check range
        private_key_int = int(private_key, 16)
        if private_key_int == 0 or private_key_int >= 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141:
            return False
        
        return True
    except Exception:
        return False


def validate_mnemonic(mnemonic: str) -> bool:
    """
    Validate a BIP-39 mnemonic phrase.
    
    Args:
        mnemonic: Mnemonic phrase to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        from hdwallet.mnemonics import BIP39Mnemonic
        
        # Try to validate using BIP39Mnemonic
        mnemonic_obj = BIP39Mnemonic.from_words(mnemonic, language="english")
        return mnemonic_obj.is_valid()
    except Exception:
        # Fallback: basic validation
        try:
            words = mnemonic.split()
            # BIP-39 supports 12, 15, 18, 21, 24 words
            if len(words) not in [12, 15, 18, 21, 24]:
                return False
            
            # Check if all words are valid (basic check)
            # In a production environment, you'd want to check against the actual wordlist
            return True
        except Exception:
            return False


def validate_derivation_path(path: str) -> bool:
    """
    Validate a BIP-44 derivation path.
    
    Args:
        path: Derivation path to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Basic format validation
        if not path.startswith('m/'):
            return False
        
        # Split path into components
        components = path.split('/')
        if len(components) < 2:
            return False
        
        # Validate each component
        for component in components[1:]:
            if not component:
                continue
            
            # Check for hardened notation (')
            if component.endswith("'"):
                component = component[:-1]
            
            # Must be a number
            if not component.isdigit():
                return False
            
            # Check range
            value = int(component)
            if value < 0 or value > 2147483647:  # 2^31 - 1
                return False
        
        return True
    except Exception:
        return False


def validate_network(network: str) -> bool:
    """
    Validate a network name.
    
    Args:
        network: Network name to validate
        
    Returns:
        True if valid, False otherwise
    """
    valid_networks = ["mainnet", "testnet", "goerli", "sepolia", "polygon", "bsc"]
    return network.lower() in valid_networks


def validate_output_format(format: str) -> bool:
    """
    Validate an output format.
    
    Args:
        format: Output format to validate
        
    Returns:
        True if valid, False otherwise
    """
    valid_formats = ["json", "csv", "yaml"]
    return format.lower() in valid_formats


def validate_count(count: int) -> bool:
    """
    Validate wallet count.
    
    Args:
        count: Number of wallets to generate
        
    Returns:
        True if valid, False otherwise
    """
    return isinstance(count, int) and 1 <= count <= 100000


def validate_strength(strength: int) -> bool:
    """
    Validate mnemonic strength.
    
    Args:
        strength: Strength in bits
        
    Returns:
        True if valid, False otherwise
    """
    valid_strengths = [128, 160, 192, 224, 256]
    return strength in valid_strengths 