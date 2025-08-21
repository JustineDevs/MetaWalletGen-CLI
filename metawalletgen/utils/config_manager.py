"""
Configuration Manager

This module handles loading and managing configuration settings
from config.yaml and environment variables.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """
    Manages configuration settings for MetaWalletGen CLI.
    
    Loads settings from:
    1. Default values
    2. config.yaml file
    3. Environment variables
    4. Command line arguments (highest priority)
    """
    
    def __init__(self, config_file: str = "config.yaml"):
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = Path(config_file)
        self.config = self._load_default_config()
        self._load_config_file()
        self._load_environment_variables()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration values."""
        return {
            "defaults": {
                "network": "mainnet",
                "derivation_path": "m/44'/60'/0'/0/0",
                "output_format": "json",
                "encrypt_by_default": False,
                "default_count": 1,
                "default_strength": 128,
                "output_directory": "wallets",
                "backup_enabled": True,
                "backup_encrypted": True
            },
            "security": {
                "encryption_algorithm": "AES-256",
                "key_derivation_iterations": 100000,
                "salt_length": 16,
                "min_password_length": 8,
                "require_special_chars": False,
                "require_numbers": False,
                "require_uppercase": False
            },
            "networks": {
                "mainnet": {
                    "name": "Ethereum Mainnet",
                    "chain_id": 1,
                    "rpc_url": "https://mainnet.infura.io/v3/YOUR_PROJECT_ID",
                    "explorer": "https://etherscan.io"
                },
                "testnet": {
                    "name": "Ethereum Testnet",
                    "chain_id": 5,
                    "rpc_url": "https://goerli.infura.io/v3/YOUR_PROJECT_ID",
                    "explorer": "https://goerli.etherscan.io"
                },
                "sepolia": {
                    "name": "Ethereum Sepolia",
                    "chain_id": 11155111,
                    "rpc_url": "https://sepolia.infura.io/v3/YOUR_PROJECT_ID",
                    "explorer": "https://sepolia.etherscan.io"
                }
            },
            "output_formats": {
                "json": {
                    "enabled": True,
                    "pretty_print": True,
                    "include_metadata": True
                },
                "csv": {
                    "enabled": True,
                    "include_headers": True,
                    "delimiter": ","
                },
                "yaml": {
                    "enabled": True,
                    "default_flow_style": False
                }
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "metawalletgen.log",
                "console": True
            },
            "ui": {
                "show_progress": True,
                "color_output": True,
                "quiet_mode": False,
                "max_wallets_display": 5,
                "truncate_addresses": True,
                "truncate_private_keys": True,
                "truncate_mnemonics": True
            },
            "validation": {
                "validate_addresses": True,
                "validate_private_keys": True,
                "validate_mnemonics": True,
                "strict_mode": False
            },
            "advanced": {
                "batch_size": 1000,
                "max_concurrent_wallets": 100,
                "clear_sensitive_data": True,
                "memory_protection": True,
                "auto_backup": False,
                "backup_interval": 24,
                "max_backups": 10
            }
        }
    
    def _load_config_file(self) -> None:
        """Load configuration from config.yaml file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f)
                    if file_config:
                        self._merge_config(self.config, file_config)
            except Exception as e:
                print(f"Warning: Could not load config file {self.config_file}: {e}")
    
    def _load_environment_variables(self) -> None:
        """Load configuration from environment variables."""
        env_mappings = {
            "METAWALLETGEN_NETWORK": ("defaults", "network"),
            "METAWALLETGEN_DERIVATION_PATH": ("defaults", "derivation_path"),
            "METAWALLETGEN_OUTPUT_FORMAT": ("defaults", "output_format"),
            "METAWALLETGEN_ENCRYPT_BY_DEFAULT": ("defaults", "encrypt_by_default"),
            "METAWALLETGEN_DEFAULT_COUNT": ("defaults", "default_count"),
            "METAWALLETGEN_DEFAULT_STRENGTH": ("defaults", "default_strength"),
            "METAWALLETGEN_OUTPUT_DIRECTORY": ("defaults", "output_directory"),
            "METAWALLETGEN_LOG_LEVEL": ("logging", "level"),
            "METAWALLETGEN_LOG_FILE": ("logging", "file"),
            "METAWALLETGEN_BATCH_SIZE": ("advanced", "batch_size"),
            "METAWALLETGEN_MAX_CONCURRENT_WALLETS": ("advanced", "max_concurrent_wallets"),
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string values to appropriate types
                if env_var.endswith("_COUNT") or env_var.endswith("_STRENGTH") or env_var.endswith("_SIZE"):
                    try:
                        value = int(value)
                    except ValueError:
                        continue
                elif env_var.endswith("_ENABLED") or env_var.endswith("_BY_DEFAULT"):
                    value = value.lower() in ("true", "1", "yes", "on")
                
                # Set the value in the config
                section, key = config_path
                if section in self.config and key in self.config[section]:
                    self.config[section][key] = value
    
    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Recursively merge configuration dictionaries."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value by dot-separated key path.
        
        Args:
            key_path: Dot-separated path to configuration value (e.g., "defaults.network")
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_defaults(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return self.config.get("defaults", {})
    
    def get_security(self) -> Dict[str, Any]:
        """Get security configuration values."""
        return self.config.get("security", {})
    
    def get_networks(self) -> Dict[str, Any]:
        """Get network configuration values."""
        return self.config.get("networks", {})
    
    def get_output_formats(self) -> Dict[str, Any]:
        """Get output format configuration values."""
        return self.config.get("output_formats", {})
    
    def get_logging(self) -> Dict[str, Any]:
        """Get logging configuration values."""
        return self.config.get("logging", {})
    
    def get_ui(self) -> Dict[str, Any]:
        """Get UI configuration values."""
        return self.config.get("ui", {})
    
    def get_validation(self) -> Dict[str, Any]:
        """Get validation configuration values."""
        return self.config.get("validation", {})
    
    def get_advanced(self) -> Dict[str, Any]:
        """Get advanced configuration values."""
        return self.config.get("advanced", {})
    
    def set(self, key_path: str, value: Any) -> None:
        """
        Set a configuration value by dot-separated key path.
        
        Args:
            key_path: Dot-separated path to configuration value
            value: Value to set
        """
        keys = key_path.split('.')
        config = self.config
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # Set the value
        config[keys[-1]] = value
    
    def save_config(self, filepath: Optional[str] = None) -> None:
        """
        Save current configuration to file.
        
        Args:
            filepath: Optional custom filepath (defaults to self.config_file)
        """
        if filepath is None:
            filepath = self.config_file
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
        except Exception as e:
            raise Exception(f"Could not save config file {filepath}: {e}")
    
    def validate_config(self) -> list:
        """
        Validate configuration values and return list of issues.
        
        Returns:
            List of validation issues (empty if valid)
        """
        issues = []
        
        # Validate network configuration
        networks = self.get("networks", {})
        for network_name, network_config in networks.items():
            if "chain_id" not in network_config:
                issues.append(f"Network {network_name} missing chain_id")
            if "rpc_url" not in network_config:
                issues.append(f"Network {network_name} missing rpc_url")
        
        # Validate security settings
        security = self.get("security", {})
        if security.get("key_derivation_iterations", 0) < 10000:
            issues.append("Key derivation iterations should be at least 10,000")
        if security.get("salt_length", 0) < 16:
            issues.append("Salt length should be at least 16 bytes")
        
        # Validate output formats
        output_formats = self.get("output_formats", {})
        for format_name, format_config in output_formats.items():
            if not format_config.get("enabled", False):
                issues.append(f"Output format {format_name} is disabled")
        
        return issues
    
    def get_network_info(self, network_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific network.
        
        Args:
            network_name: Name of the network
            
        Returns:
            Network configuration or None if not found
        """
        networks = self.get("networks", {})
        return networks.get(network_name)
    
    def is_network_supported(self, network_name: str) -> bool:
        """
        Check if a network is supported.
        
        Args:
            network_name: Name of the network
            
        Returns:
            True if network is supported
        """
        return network_name in self.get("networks", {})
    
    def get_supported_networks(self) -> list:
        """
        Get list of supported network names.
        
        Returns:
            List of supported network names
        """
        return list(self.get("networks", {}).keys())
    
    def get_supported_formats(self) -> list:
        """
        Get list of supported output formats.
        
        Returns:
            List of supported output format names
        """
        formats = []
        output_formats = self.get("output_formats", {})
        for format_name, format_config in output_formats.items():
            if format_config.get("enabled", False):
                formats.append(format_name)
        return formats


# Global configuration instance
config_manager = ConfigManager()


def get_config() -> ConfigManager:
    """Get the global configuration manager instance."""
    return config_manager
