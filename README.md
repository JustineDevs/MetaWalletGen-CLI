<div align="center">

[![MetaGen Wallet Banner](public/img/Banner%20V1%20METAGEN%20WALLET.png)](public/img/Banner%20V1%20METAGEN%20WALLET.png)

</div>

A secure, professional command-line tool for generating Ethereum-compatible wallets using BIP-39 mnemonics and EIP-55 addresses. Features comprehensive validation, progress tracking, encrypted storage, and flexible exports for blockchain development and automation.

<div align="center">

[![GitHub stars](https://img.shields.io/github/stars/JustineDevs/MetaWalletGen-CLI?style=social&label=Stars)](https://github.com/JustineDevs/MetaWalletGen-CLI/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/JustineDevs/MetaWalletGen-CLI?style=social&label=Forks)](https://github.com/JustineDevs/MetaWalletGen-CLI/network/members)
[![GitHub followers](https://img.shields.io/github/followers/JustineDevs?style=social&label=Follow)](https://github.com/JustineDevs?tab=followers)
[![GitHub issues](https://img.shields.io/github/issues/JustineDevs/MetaWalletGen-CLI)](https://github.com/JustineDevs/MetaWalletGen-CLI/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/JustineDevs/MetaWalletGen-CLI)](https://github.com/JustineDevs/MetaWalletGen-CLI/pulls)
[![GitHub license](https://img.shields.io/github/license/JustineDevs/MetaWalletGen-CLI)](https://github.com/JustineDevs/MetaWalletGen-CLI/blob/fe/LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/JustineDevs/MetaWalletGen-CLI/actions)
[![Code Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen.svg)](https://github.com/JustineDevs/MetaWalletGen-CLI)
[![Security](https://img.shields.io/badge/security-A%2B-brightgreen.svg)](https://github.com/JustineDevs/MetaWalletGen-CLI/security)

## 💰 **Support This Project**

If you find this project helpful, please consider supporting its development:

[![Open Collective](https://img.shields.io/badge/Open%20Collective-MetaWalletGen-blue?style=for-the-badge&logo=opencollective)](https://opencollective.com/metawalletgen)
[![Thanks.dev](https://img.shields.io/badge/Thanks.dev-JustineDevs-green?style=for-the-badge&logo=github)](https://thanks.dev/JustineDevs)
[![Email Support](https://img.shields.io/badge/Email%20Support-TraderGOfficial%40gmail.com-blue?style=for-the-badge&logo=gmail)](mailto:TraderGOfficial@gmail.com)

</div>

## 🚀 Enhanced Features

- **Secure Wallet Generation**: Generate Ethereum wallets using BIP-39/BIP-44 standards
- **Batch Processing**: Create multiple wallets with real-time progress tracking
- **Encrypted Storage**: Secure wallet data with AES-256 encryption and PBKDF2 key derivation
- **Multiple Output Formats**: JSON, CSV, YAML with optional encryption
- **MetaMask Compatibility**: Follows MetaMask wallet standards
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Developer Friendly**: Easy integration with automation scripts
- **Configuration Management**: YAML config files and environment variable support
- **Enhanced Validation**: Comprehensive input validation with detailed error messages
- **Rich CLI Interface**: Beautiful terminal output with progress bars and tables
- **Comprehensive Logging**: Configurable logging with multiple output destinations

## 🆕 What's New in Enhanced Version

### Enhanced CLI Commands
- **`generate`** - Generate wallets with progress tracking and validation
- **`import`** - Import wallets from existing files with format conversion
- **`list`** - List wallet files with detailed information and encryption status
- **`validate`** - Validate wallet data with comprehensive reporting
- **`info`** - Display system information and dependency status
- **`examples`** - Show common usage examples

### Enhanced Security Features
- **AES-256 Encryption** with PBKDF2 key derivation
- **Environment Variable Support** for secure password injection
- **Memory Protection** - sensitive data cleared after use
- **Password Strength Validation** with configurable requirements

### Enhanced User Experience
- **Progress Bars** for batch operations
- **Rich Tables** for data display
- **Detailed Error Messages** with actionable feedback
- **File Size Reporting** and security reminders
- **Verbose Output** for debugging and monitoring

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Development Installation

```bash
pip install -e .
```

## 🎯 Usage

### 🚀 Quick Start (From Scratch)

#### Step 1: Install the Tool
```bash
# Clone or download the project
git clone https://github.com/JustineDevs/MetaWalletGen-CLI
cd MetaWalletGen-CLI

# Install dependencies
pip install -r requirements.txt

# Install the package in development mode
pip install -e .
```

#### Step 2: Verify Installation
```bash
# Check if the tool is working
python -m metawalletgen.cli.main info

# View available commands
python -m metawalletgen.cli.main --help
```

#### Step 3: Generate Your First Wallet
```bash
# Generate a single wallet (interactive mode)
python -m metawalletgen.cli.main generate

# The tool will prompt you for:
# - Network (mainnet, testnet, sepolia)
# - Encryption (yes/no)
# - Password (if encryption is enabled)
# - Output format (json, csv, yaml)
```

#### Step 4: View Your Generated Wallet
```bash
# List generated wallet files
python -m metawalletgen.cli.main list

# View wallet contents (if not encrypted)
python -m metawalletgen.cli.main list --show-contents
```

### 📚 Basic Usage Examples

#### Generate a Single Wallet
```bash
python -m metawalletgen.cli.main generate
```

#### Generate Multiple Wallets
```bash
# Generate 5 wallets with progress tracking
python -m metawalletgen.cli.main generate --count 5 --verbose

# Generate 10 wallets in CSV format
python -m metawalletgen.cli.main generate --count 10 --format csv
```
- "csv or json"

#### Generate Encrypted Wallets
```bash
# Generate encrypted wallet (will prompt for password)
python -m metawalletgen.cli.main generate --encrypt

# Generate encrypted wallet with password from environment
export WALLET_PASSWORD="your_secure_password"
python -m metawalletgen.cli.main generate --encrypt --password $WALLET_PASSWORD
```

### 🔄 Import Existing Wallets

#### Import from Different Formats
```bash
# Import from JSON file
python -m metawalletgen.cli.main import existing_wallets.json

# Import and convert to CSV format
python -m metawalletgen.cli.main import wallets.json --format csv

# Import with encryption
python -m metawalletgen.cli.main import wallets.json --encrypt
```

### 📁 File Management

#### List and Manage Wallet Files
```bash
# List all wallet files in current directory
python -m metawalletgen.cli.main list

# List files in specific directory
python -m metawalletgen.cli.main list --directory wallets/

# Show detailed information including file sizes
python -m metawalletgen.cli.main list --verbose
```

#### Validate Wallet Data
```bash
# Validate wallet file integrity
python -m metawalletgen.cli.main validate wallets.json

# Detailed validation with verbose output
python -m metawalletgen.cli.main validate wallets.json --verbose
```

### 🛠️ System Information and Help

#### Get System Information
```bash
# Show system info and dependency status
python -m metawalletgen.cli.main info

# Display usage examples
python -m metawalletgen.cli.main examples

# Get help for specific command
python -m metawalletgen.cli.main generate --help
```

### 🎯 Advanced Usage

#### Custom Wallet Generation
```bash
# Generate wallets with custom parameters
python -m metawalletgen.cli.main generate \
  --count 100 \
  --network testnet \
  --strength 256 \
  --format yaml \
  --encrypt \
  --password $WALLET_PASSWORD \
  --summary \
  --verbose
```

#### Batch Processing with Progress
```bash
# Generate 1000 wallets with progress tracking
python -m metawalletgen.cli.main generate \
  --count 1000 \
  --format csv \
  --encrypt \
  --verbose \
  --summary
```

### 🔐 Security Best Practices

#### Password Management
```bash
# Use environment variables for passwords (recommended)
export WALLET_PASSWORD="your_very_secure_password_here"
python -m metawalletgen.cli.main generate --encrypt --password $WALLET_PASSWORD

# Clear password from environment after use
unset WALLET_PASSWORD
```

#### Network Selection
```bash
# Use testnet for development
python -m metawalletgen.cli.main generate --network testnet

# Use mainnet for production (be extra careful!)
python -m metawalletgen.cli.main generate --network mainnet
```

### 📋 Common Workflows

#### Development Workflow
```bash
# 1. Generate test wallets
python -m metawalletgen.cli.main generate --count 5 --network testnet --format json

# 2. Validate generated wallets
python -m metawalletgen.cli.main validate wallets.json --verbose

# 3. List and review
python -m metawalletgen.cli.main list --verbose
```

#### Production Workflow
```bash
# 1. Set secure password
export PROD_PASSWORD="very_long_random_password_here"

# 2. Generate encrypted wallets
python -m metawalletgen.cli.main generate \
  --count 10 \
  --network mainnet \
  --encrypt \
  --password $PROD_PASSWORD \
  --format json \
  --summary

# 3. Clear password
unset PROD_PASSWORD

# 4. Verify encryption
python -m metawalletgen.cli.main list --verbose
```

### ❓ Troubleshooting

#### Common Issues and Solutions
```bash
# If you get "command not found"
pip install -e .

# If you get import errors
pip install -r requirements.txt

# If you forget your password
# Unfortunately, encrypted wallets cannot be recovered without the password
# Always keep your passwords safe and backed up!

# If you want to test without encryption first
python -m metawalletgen.cli.main generate --count 1 --format json
```

## ⚙️ Configuration

### Configuration File

Create a `config.yaml` file for default settings:

```yaml
defaults:
  network: mainnet
  derivation_path: "m/44'/60'/0'/0/0"
  output_format: json
  encrypt_by_default: false
  default_count: 1
  default_strength: 128
  output_directory: wallets

security:
  encryption_algorithm: AES-256
  key_derivation_iterations: 100000
  min_password_length: 8

logging:
  level: INFO
  file: metawalletgen.log
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

networks:
  mainnet:
    name: Ethereum Mainnet
    chain_id: 1
    rpc_url: https://mainnet.infura.io/v3/YOUR_PROJECT_ID
  testnet:
    name: Goerli Testnet
    chain_id: 5
    rpc_url: https://goerli.infura.io/v3/YOUR_PROJECT_ID
  sepolia:
    name: Sepolia Testnet
    chain_id: 11155111
    rpc_url: https://sepolia.infura.io/v3/YOUR_PROJECT_ID
```

### Environment Variables

Set configuration via environment variables:

```bash
# Network and defaults
export METAWALLETGEN_NETWORK="sepolia"
export METAWALLETGEN_DEFAULT_COUNT="5"
export METAWALLETGEN_OUTPUT_FORMAT="csv"

# Security
export METAWALLETGEN_PASSWORD="your_secure_password"

# Logging
export METAWALLETGEN_LOG_LEVEL="DEBUG"
export METAWALLETGEN_LOG_FILE="custom.log"
```

## 🔒 Security Features

- **Encrypted Storage**: All sensitive data encrypted using AES-256
- **Secure Random Generation**: Uses cryptographically secure random number generation
- **No Logging of Secrets**: Private keys and mnemonics are never logged
- **Password Protection**: Encrypted files require password for access
- **Memory Safety**: Sensitive data is cleared from memory after use
- **Environment Variable Support**: Secure password injection for automation
- **Input Validation**: Comprehensive validation of all user inputs

## 📊 Output Formats

### JSON Format
```json
{
  "wallets": [
    {
      "address": "0x1234567890abcdef...",
      "private_key": "0xabcdef1234567890...",
      "mnemonic": "word1 word2 word3...",
      "derivation_path": "m/44'/60'/0'/0/0",
      "network": "mainnet",
      "public_key": "0x..."
    }
  ],
  "count": 1
}
```

### CSV Format
```csv
address,private_key,mnemonic,derivation_path,network,public_key
0x1234567890abcdef...,0xabcdef1234567890...,word1 word2 word3...,m/44'/60'/0'/0/0,mainnet,0x...
```

### Encrypted Vault Format
```json
{
  "version": "1.0",
  "encrypted": true,
  "salt": "base64_encoded_salt",
  "data": "encrypted_wallet_data",
  "created_at": "2025-01-21 16:30:00",
  "algorithm": "AES-256",
  "key_derivation": "PBKDF2-HMAC-SHA256"
}
```

## 🧪 Testing

### Run Enhanced Demo
```bash
python enhanced_demo.py
```

### Run Test Suite
```bash
python test_enhanced_functionality.py
```

### Test CLI Commands
```bash
# Test wallet generation
python -m metawalletgen.cli.main generate --count 2 --verbose

# Test validation
python -m metawalletgen.cli.main validate wallets.json --verbose

# Test listing
python -m metawalletgen.cli.main list
```

## 🏗️ Project Structure

```
MetaWalletGen-CLI/
├── metawalletgen/                 # Main package
│   ├── __init__.py               # Package initialization
│   ├── core/                     # Core functionality
│   │   ├── __init__.py
│   │   ├── wallet_generator.py   # Enhanced wallet generation
│   │   ├── storage_manager.py    # Enhanced file I/O and storage
│   │   └── encryption.py         # AES-256 encryption with PBKDF2
│   ├── cli/                      # Enhanced command-line interface
│   │   ├── __init__.py
│   │   ├── main.py              # CLI entry point with new commands
│   │   └── commands.py          # Enhanced command implementations
│   └── utils/                    # Enhanced utility functions
│       ├── __init__.py
│       ├── validators.py        # Enhanced input validation
│       ├── formatters.py        # Data formatting
│       ├── config_manager.py    # Configuration management
│       └── logger.py            # Enhanced logging system
├── examples/                     # Usage examples
├── tests/                       # Test files
├── docs/                        # Documentation
├── requirements.txt             # Dependencies
├── setup.py                    # Package setup
├── config.yaml                 # Configuration
├── enhanced_demo.py            # Enhanced demo script
├── test_enhanced_functionality.py # Comprehensive test suite
├── README.md                   # This documentation
├── LICENSE                     # MIT License
└── SECURITY.md                 # Security policy
```

## 🔧 Development

### Code Quality
```bash
# Format code
black metawalletgen/

# Lint code
flake8 metawalletgen/

# Type checking
mypy metawalletgen/
```

### Running Tests
```bash
# Run installation tests
python test_installation.py

# Run enhanced functionality tests
python test_enhanced_functionality.py

# Run examples
python examples/basic_usage.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 🔒 Security Considerations

- **Never share private keys or mnemonics**
- **Use encrypted storage for production environments**
- **Regularly backup wallet data securely**
- **Keep dependencies updated**
- **Use strong passwords for encrypted files**
- **Use environment variables for automation**

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🆘 Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation in the `docs/` folder
- Review the example scripts in `examples/`
- Run `metawalletgen examples` for usage examples

## ⚠️ Disclaimer

This tool is for educational and development purposes. Always follow security best practices when handling cryptocurrency wallets and private keys. The authors are not responsible for any loss of funds due to improper use of this tool.

## 🎉 Acknowledgments

- **hdwallet-io**: For the excellent HD wallet library
- **Ethereum Foundation**: For BIP standards
- **MetaMask Team**: For wallet compatibility standards
- **Open Source Community**: For the amazing tools and libraries

---

**MetaWalletGen CLI** - Secure, professional, and production-ready Ethereum wallet generation tool with enhanced features and user experience. 