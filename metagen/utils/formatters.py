"""
Formatting Utilities

This module contains formatting functions for Ethereum addresses,
private keys, and mnemonic phrases.
"""

from typing import Optional
from web3 import Web3


def format_address(address: str, checksum: bool = True) -> str:
    """
    Format an Ethereum address.
    
    Args:
        address: Ethereum address to format
        checksum: Whether to apply checksum formatting
        
    Returns:
        Formatted address
    """
    try:
        if checksum:
            return Web3.to_checksum_address(address)
        else:
            return address.lower()
    except Exception:
        return address


def format_private_key(private_key: str, prefix: bool = True) -> str:
    """
    Format a private key.
    
    Args:
        private_key: Private key to format
        prefix: Whether to include 0x prefix
        
    Returns:
        Formatted private key
    """
    # Remove existing prefix if present
    if private_key.startswith('0x'):
        private_key = private_key[2:]
    
    # Add prefix if requested
    if prefix:
        return f"0x{private_key}"
    else:
        return private_key


def format_mnemonic(mnemonic: str, word_count: Optional[int] = None) -> str:
    """
    Format a mnemonic phrase.
    
    Args:
        mnemonic: Mnemonic phrase to format
        word_count: Number of words to show (None for all)
        
    Returns:
        Formatted mnemonic phrase
    """
    words = mnemonic.strip().split()
    
    if word_count and len(words) > word_count:
        return " ".join(words[:word_count]) + "..."
    else:
        return " ".join(words)


def format_derivation_path(path: str) -> str:
    """
    Format a derivation path.
    
    Args:
        path: Derivation path to format
        
    Returns:
        Formatted derivation path
    """
    return path.strip()


def format_balance(balance_wei: int, decimals: int = 18) -> str:
    """
    Format a balance from wei to ether.
    
    Args:
        balance_wei: Balance in wei
        decimals: Number of decimal places
        
    Returns:
        Formatted balance string
    """
    try:
        balance_eth = balance_wei / (10 ** decimals)
        return f"{balance_eth:.{decimals}f}"
    except Exception:
        return str(balance_wei)


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def format_timestamp(timestamp: str) -> str:
    """
    Format a timestamp for display.
    
    Args:
        timestamp: ISO timestamp string
        
    Returns:
        Formatted timestamp
    """
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return timestamp


def format_wallet_summary(wallet_data: dict) -> str:
    """
    Format wallet data for summary display.
    
    Args:
        wallet_data: Wallet data dictionary
        
    Returns:
        Formatted summary string
    """
    lines = []
    lines.append(f"Address: {wallet_data.get('address', 'N/A')}")
    lines.append(f"Private Key: {wallet_data.get('private_key', 'N/A')[:10]}...")
    
    if wallet_data.get('mnemonic'):
        lines.append(f"Mnemonic: {wallet_data['mnemonic'][:20]}...")
    
    lines.append(f"Derivation Path: {wallet_data.get('derivation_path', 'N/A')}")
    lines.append(f"Network: {wallet_data.get('network', 'N/A')}")
    
    return "\n".join(lines)


def format_error_message(error: Exception) -> str:
    """
    Format an error message for display.
    
    Args:
        error: Exception object
        
    Returns:
        Formatted error message
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    return f"{error_type}: {error_msg}"


def format_success_message(message: str, details: Optional[dict] = None) -> str:
    """
    Format a success message for display.
    
    Args:
        message: Success message
        details: Optional details dictionary
        
    Returns:
        Formatted success message
    """
    if details:
        detail_lines = []
        for key, value in details.items():
            detail_lines.append(f"  {key}: {value}")
        return f"{message}\n" + "\n".join(detail_lines)
    else:
        return message 