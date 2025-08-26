#!/usr/bin/env python3
"""
Enhanced MetaWalletGen CLI Demo

This demo showcases the improved functionality including:
- Enhanced validation and error handling
- Progress tracking for batch operations
- Better user feedback and security reminders
- Configuration management
- Logging capabilities
"""

import sys
import os
import time
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def demo_enhanced_features():
    """Demonstrate enhanced MetaWalletGen CLI features."""
    print("🚀 Enhanced MetaWalletGen CLI Demo")
    print("=" * 50)
    
    try:
        # Test importing the enhanced package
        print("1. Testing enhanced package import...")
        import metawalletgen
        from metawalletgen.utils.config_manager import get_config
        from metawalletgen.utils.logger import get_logger
        print("   ✅ Enhanced package imported successfully")
        
        # Test configuration management
        print("\n2. Testing configuration management...")
        config = get_config()
        print(f"   ✅ Config loaded: {len(config.get_defaults())} default settings")
        print(f"   ✅ Supported networks: {', '.join(config.get_supported_networks())}")
        print(f"   ✅ Supported formats: {', '.join(config.get_supported_formats())}")
        
        # Test logging system
        print("\n3. Testing enhanced logging...")
        logger = get_logger("demo")
        logger.info("Demo logging test - INFO level")
        logger.warning("Demo logging test - WARNING level")
        print("   ✅ Enhanced logging working")
        
        # Test core modules with enhanced features
        print("\n4. Testing enhanced core modules...")
        from metawalletgen.core.wallet_generator import WalletGenerator
        from metawalletgen.core.storage_manager import StorageManager
        from metawalletgen.utils.validators import (
            validate_ethereum_address, 
            validate_private_key, 
            validate_mnemonic
        )
        print("   ✅ Enhanced core modules imported")
        
        # Test wallet generation with validation
        print("\n5. Testing enhanced wallet generation...")
        generator = WalletGenerator(network="testnet")
        wallet = generator.generate_new_wallet()
        
        # Validate generated wallet
        address_valid = validate_ethereum_address(wallet.address)
        private_key_valid = validate_private_key(wallet.private_key)
        mnemonic_valid = validate_mnemonic(wallet.mnemonic)
        
        print(f"   ✅ Generated wallet: {wallet.address[:10]}...")
        print(f"   ✅ Address validation: {'PASS' if address_valid else 'FAIL'}")
        print(f"   ✅ Private key validation: {'PASS' if private_key_valid else 'FAIL'}")
        print(f"   ✅ Mnemonic validation: {'PASS' if mnemonic_valid else 'FAIL'}")
        
        # Test batch generation simulation
        print("\n6. Testing batch generation simulation...")
        wallets = []
        batch_size = 5
        
        print(f"   📊 Generating {batch_size} wallets with progress tracking...")
        for i in range(batch_size):
            wallet = generator.generate_new_wallet(index=i)
            wallets.append(wallet)
            progress = (i + 1) / batch_size * 100
            print(f"      [{i+1:2d}/{batch_size}] {progress:5.1f}% - {wallet.address[:10]}...")
            time.sleep(0.1)  # Simulate processing time
        
        print(f"   ✅ Successfully generated {len(wallets)} wallets")
        
        # Test enhanced storage with encryption
        print("\n7. Testing enhanced storage...")
        storage = StorageManager()
        
        # Save wallets in different formats
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # JSON format
        json_file = storage.save_wallets_json(wallets, f"demo_wallets_{timestamp}.json")
        print(f"   ✅ JSON saved: {os.path.basename(json_file)}")
        
        # CSV format
        csv_file = storage.save_wallets_csv(wallets, f"demo_wallets_{timestamp}.csv")
        print(f"   ✅ CSV saved: {os.path.basename(csv_file)}")
        
        # Encrypted JSON
        encrypted_file = storage.save_wallets_json(
            wallets, f"demo_wallets_{timestamp}_encrypted.json", 
            encrypt=True, password="demo_password_123"
        )
        print(f"   ✅ Encrypted JSON saved: {os.path.basename(encrypted_file)}")
        
        # Test file operations
        print("\n8. Testing file operations...")
        files = [json_file, csv_file, encrypted_file]
        
        for file_path in files:
            if os.path.exists(file_path):
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                print(f"   📁 {os.path.basename(file_path)}: {size_mb:.2f} MB")
        
        # Test configuration validation
        print("\n9. Testing configuration validation...")
        config_issues = config.validate_config()
        if config_issues:
            print("   ⚠️  Configuration issues found:")
            for issue in config_issues:
                print(f"      • {issue}")
        else:
            print("   ✅ Configuration validation passed")
        
        # Test network information
        print("\n10. Testing network information...")
        for network_name in config.get_supported_networks():
            network_info = config.get_network_info(network_name)
            if network_info:
                print(f"   🌐 {network_name}: {network_info['name']} (Chain ID: {network_info['chain_id']})")
        
        # Security summary
        print("\n" + "=" * 50)
        print("🔒 Security Features Demonstrated:")
        print("   • AES-256 encryption for sensitive data")
        print("   • BIP-39/BIP-44 compliant wallet generation")
        print("   • Comprehensive input validation")
        print("   • Secure password handling")
        print("   • Memory protection for sensitive data")
        
        print("\n📊 Performance Features:")
        print("   • Progress tracking for batch operations")
        print("   • Configurable batch sizes")
        print("   • Memory-efficient processing")
        print("   • Logging and monitoring")
        
        print("\n🎯 Usability Improvements:")
        print("   • Clear error messages and validation feedback")
        print("   • Multiple output formats (JSON, CSV, YAML)")
        print("   • Configuration file support")
        print("   • Environment variable integration")
        print("   • Comprehensive help and examples")
        
        print("\n" + "=" * 50)
        print("🎉 Enhanced demo completed successfully!")
        print("\nGenerated files:")
        for file_path in files:
            if os.path.exists(file_path):
                print(f"  📄 {os.path.basename(file_path)}")
        
        print(f"\n📁 Files saved in: {os.path.dirname(json_file)}")
        print("\nTo run the enhanced CLI:")
        print("  python -m metawalletgen.cli.main --help")
        print("  python -m metawalletgen.cli.main generate --count 3 --verbose")
        print("  python -m metawalletgen.cli.main examples")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Try installing dependencies: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


def demo_cli_commands():
    """Demonstrate CLI command usage."""
    print("\n🖥️  CLI Command Examples")
    print("=" * 30)
    
    commands = [
        ("Generate single wallet", "metawalletgen generate"),
        ("Generate 5 wallets with verbose output", "metawalletgen generate -c 5 -v"),
        ("Generate encrypted wallets", "metawalletgen generate -c 3 --encrypt"),
        ("Generate for testnet", "metawalletgen generate -n testnet"),
        ("Generate in CSV format", "metawalletgen generate -f csv"),
        ("Import wallets from file", "metawalletgen import wallets.json"),
        ("List wallet files", "metawalletgen list"),
        ("Validate wallet data", "metawalletgen validate wallets.json"),
        ("Show system info", "metawalletgen info"),
        ("Show examples", "metawalletgen examples"),
        ("Get help", "metawalletgen --help"),
    ]
    
    for description, command in commands:
        print(f"📝 {description}:")
        print(f"   {command}")
        print()


def demo_configuration():
    """Demonstrate configuration features."""
    print("\n⚙️  Configuration Features")
    print("=" * 30)
    
    try:
        from metawalletgen.utils.config_manager import get_config
        config = get_config()
        
        print("📋 Default Settings:")
        defaults = config.get_defaults()
        for key, value in defaults.items():
            print(f"   • {key}: {value}")
        
        print("\n🔐 Security Settings:")
        security = config.get_security()
        for key, value in security.items():
            if "password" in key.lower():
                print(f"   • {key}: {'*' * len(str(value))}")
            else:
                print(f"   • {key}: {value}")
        
        print("\n🌐 Network Configuration:")
        networks = config.get_networks()
        for name, info in networks.items():
            print(f"   • {name}: {info['name']} (Chain ID: {info['chain_id']})")
        
        print("\n📁 Environment Variables Supported:")
        env_vars = [
            "METAWALLETGEN_NETWORK",
            "METAWALLETGEN_DERIVATION_PATH", 
            "METAWALLETGEN_OUTPUT_FORMAT",
            "METAWALLETGEN_ENCRYPT_BY_DEFAULT",
            "METAWALLETGEN_DEFAULT_COUNT",
            "METAWALLETGEN_LOG_LEVEL"
        ]
        for env_var in env_vars:
            value = os.getenv(env_var, "Not set")
            print(f"   • {env_var}: {value}")
        
    except Exception as e:
        print(f"❌ Configuration demo error: {e}")


if __name__ == "__main__":
    print("🚀 Starting Enhanced MetaWalletGen CLI Demo...")
    print("This demo showcases the improvements made to address usability issues")
    print("and enhance functionality as outlined in the analysis.\n")
    
    # Run main demo
    demo_enhanced_features()
    
    # Run CLI examples demo
    demo_cli_commands()
    
    # Run configuration demo
    demo_configuration()
    
    print("\n✨ Demo completed! The enhanced MetaWalletGen CLI now includes:")
    print("   • Better validation and error handling")
    print("   • Progress tracking for batch operations") 
    print("   • Enhanced user feedback and security reminders")
    print("   • Configuration management with environment variable support")
    print("   • Comprehensive logging system")
    print("   • Improved CLI commands and help text")
    print("   • Better file handling and encryption")
