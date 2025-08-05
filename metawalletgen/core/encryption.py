"""
Encryption Module

This module provides secure encryption and decryption functionality
for storing sensitive wallet data using AES-256 encryption.
"""

import os
import base64
import hashlib
from typing import Optional, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


class EncryptionManager:
    """
    Manages encryption and decryption of sensitive wallet data
    using AES-256 encryption with PBKDF2 key derivation.
    """
    
    def __init__(self, salt: Optional[bytes] = None):
        """
        Initialize the encryption manager.
        
        Args:
            salt: Optional salt for key derivation (generated if not provided)
        """
        self.salt = salt or os.urandom(16)
        self.backend = default_backend()
    
    def derive_key(self, password: str, iterations: int = 100000) -> bytes:
        """
        Derive encryption key from password using PBKDF2.
        
        Args:
            password: User password
            iterations: Number of PBKDF2 iterations
            
        Returns:
            Derived encryption key
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=iterations,
            backend=self.backend
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def encrypt_data(self, data: str, password: str) -> str:
        """
        Encrypt data using AES-256.
        
        Args:
            data: Data to encrypt
            password: Encryption password
            
        Returns:
            Base64 encoded encrypted data
        """
        key = self.derive_key(password)
        f = Fernet(key)
        
        encrypted_data = f.encrypt(data.encode())
        return base64.b64encode(encrypted_data).decode()
    
    def decrypt_data(self, encrypted_data: str, password: str) -> str:
        """
        Decrypt data using AES-256.
        
        Args:
            encrypted_data: Base64 encoded encrypted data
            password: Decryption password
            
        Returns:
            Decrypted data
        """
        key = self.derive_key(password)
        f = Fernet(key)
        
        encrypted_bytes = base64.b64decode(encrypted_data.encode())
        decrypted_data = f.decrypt(encrypted_bytes)
        return decrypted_data.decode()
    
    def encrypt_file(self, input_file: str, output_file: str, password: str) -> None:
        """
        Encrypt a file and save to output file.
        
        Args:
            input_file: Path to input file
            output_file: Path to output encrypted file
            password: Encryption password
        """
        with open(input_file, 'r', encoding='utf-8') as f:
            data = f.read()
        
        encrypted_data = self.encrypt_data(data, password)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(encrypted_data)
    
    def decrypt_file(self, input_file: str, output_file: str, password: str) -> None:
        """
        Decrypt a file and save to output file.
        
        Args:
            input_file: Path to encrypted input file
            output_file: Path to output decrypted file
            password: Decryption password
        """
        with open(input_file, 'r', encoding='utf-8') as f:
            encrypted_data = f.read()
        
        decrypted_data = self.decrypt_data(encrypted_data, password)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(decrypted_data)
    
    def encrypt_wallet_data(self, wallet_data: dict, password: str) -> str:
        """
        Encrypt wallet data dictionary.
        
        Args:
            wallet_data: Dictionary containing wallet information
            password: Encryption password
            
        Returns:
            Base64 encoded encrypted wallet data
        """
        import json
        data_json = json.dumps(wallet_data, indent=2)
        return self.encrypt_data(data_json, password)
    
    def decrypt_wallet_data(self, encrypted_data: str, password: str) -> dict:
        """
        Decrypt wallet data dictionary.
        
        Args:
            encrypted_data: Base64 encoded encrypted wallet data
            password: Decryption password
            
        Returns:
            Decrypted wallet data dictionary
        """
        import json
        decrypted_json = self.decrypt_data(encrypted_data, password)
        return json.loads(decrypted_json)
    
    def generate_secure_password(self, length: int = 32) -> str:
        """
        Generate a cryptographically secure password.
        
        Args:
            length: Password length
            
        Returns:
            Secure password string
        """
        import secrets
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using SHA-256.
        
        Args:
            password: Password to hash
            
        Returns:
            Hashed password
        """
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: Password to verify
            hashed_password: Hashed password to compare against
            
        Returns:
            True if password matches, False otherwise
        """
        return self.hash_password(password) == hashed_password
    
    def get_salt(self) -> str:
        """
        Get the current salt as base64 string.
        
        Returns:
            Base64 encoded salt
        """
        return base64.b64encode(self.salt).decode()
    
    def set_salt(self, salt: str) -> None:
        """
        Set the salt from base64 string.
        
        Args:
            salt: Base64 encoded salt
        """
        self.salt = base64.b64decode(salt.encode())
    
    def create_encrypted_vault(self, data: dict, password: str) -> dict:
        """
        Create an encrypted vault with metadata.
        
        Args:
            data: Data to encrypt
            password: Encryption password
            
        Returns:
            Dictionary containing encrypted data and metadata
        """
        encrypted_data = self.encrypt_wallet_data(data, password)
        
        vault = {
            "version": "1.0",
            "encrypted": True,
            "salt": self.get_salt(),
            "data": encrypted_data,
            "created_at": str(datetime.datetime.now()),
            "algorithm": "AES-256",
            "key_derivation": "PBKDF2-HMAC-SHA256"
        }
        
        return vault
    
    def decrypt_vault(self, vault: dict, password: str) -> dict:
        """
        Decrypt a vault and return the data.
        
        Args:
            vault: Vault dictionary
            password: Decryption password
            
        Returns:
            Decrypted data dictionary
        """
        if not vault.get("encrypted", False):
            raise ValueError("Vault is not encrypted")
        
        # Set salt from vault
        self.set_salt(vault["salt"])
        
        # Decrypt data
        return self.decrypt_wallet_data(vault["data"], password) 