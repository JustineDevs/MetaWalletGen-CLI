# MetaWalletGen CLI - Deployment Guide

## Version: 2.0.0

### 🚀 Quick Start

#### Option 1: PyPI Installation (Recommended)
```bash
pip install metawalletgen-cli
```

#### Option 2: Local Installation
```bash
# Clone repository
git clone https://github.com/metawalletgen/cli.git
cd cli

# Install in development mode
pip install -e .

# Or install from built package
pip install dist/metawalletgen_cli-2.0.0-py3-none-any.whl
```

#### Option 3: Platform-Specific Installers

**Windows:**
```cmd
install_windows.bat
```

**Unix/Linux/macOS:**
```bash
./install_unix.sh
```

#### Option 4: Docker
```bash
# Build image
docker build -t metawalletgen/cli:2.0.0 .

# Run container
docker run -it --rm -v $(pwd)/wallets:/app/wallets metawalletgen/cli:2.0.0

# Or use docker-compose
docker-compose --profile cli run metawalletgen --help
```

### 🔧 Configuration

1. **Environment Variables:**
   ```bash
   export MWG_CONFIG_PATH=/path/to/config.yaml
   export MWG_OUTPUT_DIR=/path/to/wallets
   export MWG_ENCRYPTION_PASSWORD=your_secure_password
   ```

2. **Configuration File:**
   ```yaml
   # config.yaml
   output_dir: ./wallets
   encryption_enabled: true
   default_format: json
   batch_size: 100
   ```

### 📦 Package Contents

- **Source Distribution:** `metawalletgen_cli-2.0.0.tar.gz`
- **Wheel Distribution:** `metawalletgen_cli-2.0.0-py3-none-any.whl`
- **Installation Scripts:** Platform-specific installers
- **Docker Support:** Dockerfile and docker-compose.yml

### 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=metawalletgen --cov-report=html

# Run specific test categories
pytest -m "not slow"
pytest -m integration
```

### 🔒 Security Considerations

- Store encryption passwords securely
- Use environment variables for sensitive data
- Regularly update dependencies
- Monitor security audit logs

### 📊 Performance Tuning

- Adjust batch sizes based on system resources
- Monitor performance metrics with `mwg performance`
- Use health checks with `mwg health`

### 🆘 Troubleshooting

1. **Import Errors:** Ensure all dependencies are installed
2. **Permission Issues:** Check file/directory permissions
3. **Performance Issues:** Monitor system resources with `mwg performance`

### 📞 Support

- **Documentation:** https://metawalletgen.com/docs
- **Issues:** https://github.com/metawalletgen/cli/issues
- **Security:** https://metawalletgen.com/security

---

*Generated on: Windows 10*
*Python Version: 3.12.10 (tags/v3.12.10:0cc8128, Apr  8 2025, 12:21:36) [MSC v.1943 64 bit (AMD64)]*
