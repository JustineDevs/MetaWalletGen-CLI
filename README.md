# MetaWalletGen CLI

A secure command-line tool for generating Ethereum-compatible wallets using BIP-39 mnemonics and EIP-55 addresses. Supports batch creation, encrypted storage, and flexible exports for blockchain development and automation.

## Features

- **Secure Wallet Generation**: Generate Ethereum wallets using BIP-39/BIP-44 standards
- **Batch Processing**: Create multiple wallets in a single command
- **Encrypted Storage**: Secure wallet data with AES-256 encryption
- **Multiple Output Formats**: JSON, CSV, and encrypted vault files
- **MetaMask Compatibility**: Follows MetaMask wallet standards
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Developer Friendly**: Easy integration with automation scripts

## Installation

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

## Usage

### Basic Wallet Generation

Generate a single wallet:
```bash
python metawalletgen.py generate
```

Generate multiple wallets:
```bash
python metawalletgen.py generate --count 10
```

### Import Existing Wallet

Import wallet from mnemonic:
```bash
python metawalletgen.py import --mnemonic "your twelve word mnemonic phrase here"
```

Import wallet from private key:
```bash
python metawalletgen.py import --private-key "0x1234567890abcdef..."
```

### Output Options

Save to JSON file:
```bash
python metawalletgen.py generate --count 5 --output wallets.json
```

Save to CSV file:
```bash
python metawalletgen.py generate --count 10 --output wallets.csv --format csv
```

Save encrypted vault:
```bash
python metawalletgen.py generate --count 3 --output vault.enc --encrypt
```

### Advanced Options

Generate wallets with custom derivation path:
```bash
python metawalletgen.py generate --count 5 --derivation "m/44'/60'/0'/0/0"
```

Generate wallets for specific network:
```bash
python metawalletgen.py generate --count 3 --network testnet
```

## Security Features

- **Encrypted Storage**: All sensitive data is encrypted using AES-256
- **Secure Random Generation**: Uses cryptographically secure random number generation
- **No Logging of Secrets**: Private keys and mnemonics are never logged
- **Password Protection**: Encrypted files require password for access
- **Memory Safety**: Sensitive data is cleared from memory after use

## Output Formats

### JSON Format
```json
{
  "wallets": [
    {
      "address": "0x1234567890abcdef...",
      "private_key": "0xabcdef1234567890...",
      "mnemonic": "word1 word2 word3...",
      "derivation_path": "m/44'/60'/0'/0/0",
      "network": "mainnet"
    }
  ]
}
```

### CSV Format
```csv
address,private_key,mnemonic,derivation_path,network
0x1234567890abcdef...,0xabcdef1234567890...,word1 word2 word3...,m/44'/60'/0'/0/0,mainnet
```

## Configuration

Create a `config.yaml` file for default settings:

```yaml
defaults:
  network: mainnet
  derivation_path: "m/44'/60'/0'/0/0"
  output_format: json
  encrypt_by_default: false

security:
  encryption_algorithm: AES-256
  key_derivation_iterations: 100000
```

## Development

### Project Structure

```
MetaWalletGen-CLI/
├── metawalletgen/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── wallet_generator.py
│   │   ├── storage_manager.py
│   │   └── encryption.py
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── commands.py
│   │   └── utils.py
│   └── utils/
│       ├── __init__.py
│       ├── validators.py
│       └── formatters.py
├── tests/
├── requirements.txt
├── setup.py
└── README.md
```

### Running Tests

```bash
python -m pytest tests/
```

### Code Quality

```bash
# Format code
black metawalletgen/

# Lint code
flake8 metawalletgen/

# Type checking
mypy metawalletgen/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Security Considerations

- **Never share private keys or mnemonics**
- **Use encrypted storage for production environments**
- **Regularly backup wallet data securely**
- **Keep dependencies updated**
- **Use strong passwords for encrypted files**

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation in the `docs/` folder
- Review the example scripts in `examples/`

## Disclaimer

This tool is for educational and development purposes. Always follow security best practices when handling cryptocurrency wallets and private keys. The authors are not responsible for any loss of funds due to improper use of this tool. 