"""
Storage Manager Module

This module handles file I/O operations, data persistence, and
format conversion for wallet data storage.
"""

import os
import json
import csv
import yaml
from typing import List, Dict, Optional, Union
from pathlib import Path
from .wallet_generator import WalletData
from .encryption import EncryptionManager
import datetime


class StorageManager:
    """
    Manages storage and retrieval of wallet data in various formats
    with optional encryption support.
    """
    
    def __init__(self, output_dir: str = "wallets"):
        """
        Initialize the storage manager.
        
        Args:
            output_dir: Directory for storing wallet files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.encryption_manager = EncryptionManager()
    
    def save_wallets_json(
        self, 
        wallets: List[WalletData], 
        filename: str,
        encrypt: bool = False,
        password: Optional[str] = None
    ) -> str:
        """
        Save wallets to JSON file.
        
        Args:
            wallets: List of WalletData objects
            filename: Output filename
            encrypt: Whether to encrypt the file
            password: Encryption password (required if encrypt=True)
            
        Returns:
            Path to saved file
        """
        filepath = self.output_dir / filename
        
        # Convert wallets to dictionaries
        wallet_dicts = [wallet.to_dict() for wallet in wallets]
        data = {"wallets": wallet_dicts, "count": len(wallets)}
        
        if encrypt:
            if not password:
                raise ValueError("Password required for encryption")
            
            # Create encrypted vault
            vault = self.encryption_manager.create_encrypted_vault(data, password)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(vault, f, indent=2)
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        
        return str(filepath)
    
    def save_wallets_csv(
        self, 
        wallets: List[WalletData], 
        filename: str,
        encrypt: bool = False,
        password: Optional[str] = None
    ) -> str:
        """
        Save wallets to CSV file.
        
        Args:
            wallets: List of WalletData objects
            filename: Output filename
            encrypt: Whether to encrypt the file
            password: Encryption password (required if encrypt=True)
            
        Returns:
            Path to saved file
        """
        filepath = self.output_dir / filename
        
        # Convert wallets to list of dictionaries
        wallet_dicts = [wallet.to_dict() for wallet in wallets]
        
        if encrypt:
            if not password:
                raise ValueError("Password required for encryption")
            
            # Create encrypted vault
            vault = self.encryption_manager.create_encrypted_vault(
                {"wallets": wallet_dicts}, password
            )
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(vault, f, indent=2)
        else:
            # Write CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                if wallet_dicts:
                    fieldnames = wallet_dicts[0].keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(wallet_dicts)
        
        return str(filepath)
    
    def save_wallets_yaml(
        self, 
        wallets: List[WalletData], 
        filename: str,
        encrypt: bool = False,
        password: Optional[str] = None
    ) -> str:
        """
        Save wallets to YAML file.
        
        Args:
            wallets: List of WalletData objects
            filename: Output filename
            encrypt: Whether to encrypt the file
            password: Encryption password (required if encrypt=True)
            
        Returns:
            Path to saved file
        """
        filepath = self.output_dir / filename
        
        # Convert wallets to dictionaries
        wallet_dicts = [wallet.to_dict() for wallet in wallets]
        data = {"wallets": wallet_dicts, "count": len(wallets)}
        
        if encrypt:
            if not password:
                raise ValueError("Password required for encryption")
            
            # Create encrypted vault
            vault = self.encryption_manager.create_encrypted_vault(data, password)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(vault, f, default_flow_style=False)
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False)
        
        return str(filepath)
    
    def load_wallets_json(
        self, 
        filename: str,
        decrypt: bool = False,
        password: Optional[str] = None
    ) -> List[WalletData]:
        """
        Load wallets from JSON file.
        
        Args:
            filename: Input filename
            decrypt: Whether the file is encrypted
            password: Decryption password (required if decrypt=True)
            
        Returns:
            List of WalletData objects
        """
        filepath = self.output_dir / filename
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if decrypt:
            if not password:
                raise ValueError("Password required for decryption")
            
            # Decrypt vault
            decrypted_data = self.encryption_manager.decrypt_vault(data, password)
            wallets_data = decrypted_data["wallets"]
        else:
            wallets_data = data["wallets"]
        
        # Convert dictionaries back to WalletData objects
        wallets = []
        for wallet_dict in wallets_data:
            wallet = WalletData(
                address=wallet_dict["address"],
                private_key=wallet_dict["private_key"],
                mnemonic=wallet_dict["mnemonic"],
                derivation_path=wallet_dict["derivation_path"],
                network=wallet_dict["network"],
                public_key=wallet_dict.get("public_key", "")
            )
            wallets.append(wallet)
        
        return wallets
    
    def load_wallets_csv(
        self, 
        filename: str,
        decrypt: bool = False,
        password: Optional[str] = None
    ) -> List[WalletData]:
        """
        Load wallets from CSV file.
        
        Args:
            filename: Input filename
            decrypt: Whether the file is encrypted
            password: Decryption password (required if decrypt=True)
            
        Returns:
            List of WalletData objects
        """
        filepath = self.output_dir / filename
        
        if decrypt:
            if not password:
                raise ValueError("Password required for decryption")
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Decrypt vault
            decrypted_data = self.encryption_manager.decrypt_vault(data, password)
            wallets_data = decrypted_data["wallets"]
        else:
            # Read CSV
            wallets_data = []
            with open(filepath, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    wallets_data.append(row)
        
        # Convert dictionaries back to WalletData objects
        wallets = []
        for wallet_dict in wallets_data:
            wallet = WalletData(
                address=wallet_dict["address"],
                private_key=wallet_dict["private_key"],
                mnemonic=wallet_dict["mnemonic"],
                derivation_path=wallet_dict["derivation_path"],
                network=wallet_dict["network"],
                public_key=wallet_dict.get("public_key", "")
            )
            wallets.append(wallet)
        
        return wallets
    
    def save_wallet_summary(
        self, 
        wallets: List[WalletData], 
        filename: str = "wallet_summary.txt"
    ) -> str:
        """
        Save a human-readable summary of wallets.
        
        Args:
            wallets: List of WalletData objects
            filename: Output filename
            
        Returns:
            Path to saved file
        """
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("MetaWalletGen CLI - Wallet Summary\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Total Wallets Generated: {len(wallets)}\n")
            f.write(f"Network: {wallets[0].network if wallets else 'Unknown'}\n")
            f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for i, wallet in enumerate(wallets, 1):
                f.write(f"Wallet #{i}\n")
                f.write("-" * 20 + "\n")
                f.write(f"Address: {wallet.address}\n")
                f.write(f"Derivation Path: {wallet.derivation_path}\n")
                if wallet.mnemonic:
                    f.write(f"Mnemonic: {wallet.mnemonic}\n")
                f.write(f"Private Key: {wallet.private_key}\n")
                f.write("\n")
        
        return str(filepath)
    
    def get_file_info(self, filename: str) -> Dict[str, Union[str, int]]:
        """
        Get information about a wallet file.
        
        Args:
            filename: Name of the file
            
        Returns:
            Dictionary with file information
        """
        filepath = self.output_dir / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        stat = filepath.stat()
        
        info = {
            "filename": filename,
            "size_bytes": stat.st_size,
            "created": datetime.datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "path": str(filepath)
        }
        
        # Try to determine if it's encrypted
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                info["encrypted"] = data.get("encrypted", False)
                if "wallets" in data:
                    info["wallet_count"] = len(data["wallets"])
        except (json.JSONDecodeError, KeyError):
            info["encrypted"] = False
            info["wallet_count"] = "Unknown"
        
        return info
    
    def list_wallet_files(self) -> List[Dict[str, Union[str, int]]]:
        """
        List all wallet files in the output directory.
        
        Returns:
            List of file information dictionaries
        """
        files = []
        
        for filepath in self.output_dir.glob("*"):
            if filepath.is_file():
                try:
                    info = self.get_file_info(filepath.name)
                    files.append(info)
                except Exception:
                    # Skip files that can't be read
                    continue
        
        return files
    
    def backup_wallets(
        self, 
        wallets: List[WalletData], 
        backup_name: str,
        password: Optional[str] = None
    ) -> str:
        """
        Create a secure backup of wallets.
        
        Args:
            wallets: List of WalletData objects
            backup_name: Name for the backup
            password: Optional encryption password
            
        Returns:
            Path to backup file
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{backup_name}_{timestamp}.json"
        
        if password:
            return self.save_wallets_json(wallets, filename, encrypt=True, password=password)
        else:
            return self.save_wallets_json(wallets, filename, encrypt=False)
    
    def export_for_metamask(self, wallets: List[WalletData], filename: str) -> str:
        """
        Export wallets in MetaMask-compatible format.
        
        Args:
            wallets: List of WalletData objects
            filename: Output filename
            
        Returns:
            Path to exported file
        """
        filepath = self.output_dir / filename
        
        metamask_data = []
        for wallet in wallets:
            metamask_data.append({
                "address": wallet.address,
                "privateKey": wallet.private_key,
                "mnemonic": wallet.mnemonic if wallet.mnemonic else "",
                "derivationPath": wallet.derivation_path if wallet.derivation_path else ""
            })
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metamask_data, f, indent=2)
        
        return str(filepath) 