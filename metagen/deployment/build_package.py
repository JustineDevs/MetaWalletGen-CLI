#!/usr/bin/env python3
"""
MetaWalletGen CLI - Package Build Script
Automated build and distribution preparation
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path
from typing import List, Dict, Any

class PackageBuilder:
    """Handles building and packaging MetaWalletGen CLI"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"
        self.package_name = "metawalletgen-cli"
        self.version = self._get_version()
        
    def _get_version(self) -> str:
        """Extract version from package"""
        try:
            sys.path.insert(0, str(self.project_root))
            from metawalletgen import __version__
            return __version__
        except ImportError:
            return "2.0.0"
    
    def clean_build_dirs(self):
        """Clean build and distribution directories"""
        print("🧹 Cleaning build directories...")
        
        for dir_path in [self.dist_dir, self.build_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"   Removed: {dir_path}")
        
        # Clean Python cache
        cache_dirs = list(self.project_root.rglob("__pycache__"))
        if cache_dirs:
            for cache_dir in cache_dirs:
                try:
                    shutil.rmtree(cache_dir)
                    print(f"   Removed: {cache_dir}")
                except (PermissionError, OSError) as e:
                    print(f"   Warning: Could not remove {cache_dir}: {e}")
        
        # Clean egg info
        egg_dirs = list(self.project_root.rglob("*.egg-info"))
        if egg_dirs:
            for egg_dir in egg_dirs:
                try:
                    shutil.rmtree(egg_dir)
                    print(f"   Removed: {egg_dir}")
                except (PermissionError, OSError) as e:
                    print(f"   Warning: Could not remove {egg_dir}: {e}")
        
        return True
    
    def install_build_deps(self):
        """Install build dependencies"""
        print("📦 Installing build dependencies...")
        
        build_deps = [
            "build",
            "wheel",
            "setuptools",
            "twine",
            "check-wheel-contents"
        ]
        
        for dep in build_deps:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                             check=True, capture_output=True)
                print(f"   ✓ {dep}")
            except subprocess.CalledProcessError as e:
                print(f"   ✗ Failed to install {dep}: {e}")
                return False
        
        return True
    
    def run_tests(self):
        """Run test suite"""
        print("🧪 Running test suite...")
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "--cov=metawalletgen",
                "--cov-report=term-missing",
                "--cov-report=html:htmlcov",
                "--cov-report=xml:coverage.xml"
            ], cwd=self.project_root, check=True)
            
            print("   ✓ All tests passed")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"   ✗ Tests failed: {e}")
            return False
    
    def build_package(self):
        """Build source and wheel distributions"""
        print("🔨 Building package...")
        
        try:
            # Build source distribution
            subprocess.run([
                sys.executable, "-m", "build", "--sdist"
            ], cwd=self.project_root, check=True)
            
            # Build wheel
            subprocess.run([
                sys.executable, "-m", "build", "--wheel"
            ], cwd=self.project_root, check=True)
            
            print("   ✓ Package built successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"   ✗ Build failed: {e}")
            return False
    
    def check_package(self):
        """Check package quality"""
        print("🔍 Checking package quality...")
        
        try:
            # Check wheel contents
            wheel_files = list(self.dist_dir.glob("*.whl"))
            if wheel_files:
                subprocess.run([
                    sys.executable, "-m", "check_wheel_contents", str(wheel_files[0])
                ], cwd=self.project_root, check=True)
                print("   ✓ Wheel contents validated")
            
            # Check package with twine
            subprocess.run([
                sys.executable, "-m", "twine", "check", "dist/*"
            ], cwd=self.project_root, check=True)
            
            print("   ✓ Package validation passed")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"   ✗ Package validation failed: {e}")
            return False
    
    def create_installer_scripts(self):
        """Create platform-specific installer scripts"""
        print("📱 Creating installer scripts...")
        
        # Windows installer
        self._create_windows_installer()
        
        # Unix installer
        self._create_unix_installer()
        
        # Docker setup
        self._create_docker_setup()
        
        print("   ✓ Installer scripts created")
        return True
    
    def _create_windows_installer(self):
        """Create Windows batch installer"""
        installer_path = self.project_root / "install_windows.bat"
        
        content = f"""@echo off
REM MetaWalletGen CLI - Windows Installer
REM Version: {self.version}

echo.
echo ========================================
echo   MetaWalletGen CLI Installer
echo   Version: {self.version}
echo ========================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo Python found: 
python --version
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install package
echo Installing MetaWalletGen CLI...
python -m pip install --user dist/metawalletgen_cli-{self.version}-py3-none-any.whl

if errorlevel 1 (
    echo ERROR: Installation failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo You can now use:
echo   metawalletgen --help
echo   mwg --help
echo.
echo For more information, visit:
echo   https://github.com/metawalletgen/cli
echo.
pause
"""
        
        with open(installer_path, 'w') as f:
            f.write(content)
    
    def _create_unix_installer(self):
        """Create Unix shell installer"""
        installer_path = self.project_root / "install_unix.sh"
        
        content = f"""#!/bin/bash
# MetaWalletGen CLI - Unix Installer
# Version: {self.version}

set -e

echo
echo "========================================"
echo "  MetaWalletGen CLI Installer"
echo "  Version: {self.version}"
echo "========================================"
echo

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ first"
    exit 1
fi

echo "Python found:"
python3 --version
echo

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "WARNING: Running as root. This is not recommended."
   read -p "Continue anyway? (y/N): " -n 1 -r
   echo
   if [[ ! $REPLY =~ ^[Yy]$ ]]; then
       exit 1
   fi
fi

# Upgrade pip
echo "Upgrading pip..."
python3 -m pip install --upgrade pip --user

# Install package
echo "Installing MetaWalletGen CLI..."
python3 -m pip install --user dist/metawalletgen_cli-{self.version}-py3-none-any.whl

echo
echo "========================================"
echo "  Installation Complete!"
echo "========================================"
echo
echo "You can now use:"
echo "  metawalletgen --help"
echo "  mwg --help"
echo
echo "For more information, visit:"
echo "  https://github.com/metawalletgen/cli"
echo

# Add to PATH if not already there
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "Adding ~/.local/bin to PATH..."
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    echo "Please restart your terminal or run: source ~/.bashrc"
fi
"""
        
        with open(installer_path, 'w') as f:
            f.write(content)
        
        # Make executable
        os.chmod(installer_path, 0o755)
    
    def _create_docker_setup(self):
        """Create Docker setup files"""
        dockerfile_path = self.project_root / "Dockerfile"
        
        content = f"""# MetaWalletGen CLI Docker Image
# Version: {self.version}

FROM python:3.11-slim

LABEL maintainer="MetaWalletGen Team <maintainers@metawalletgen.com>"
LABEL version="{self.version}"
LABEL description="Professional Ethereum Wallet Generator with Advanced Security Features"

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy package files
COPY . .

# Install the package
RUN pip install --no-cache-dir .

# Create non-root user
RUN useradd --create-home --shell /bin/bash metawalletgen
USER metawalletgen

# Set entry point
ENTRYPOINT ["metawalletgen"]

# Default command
CMD ["--help"]
"""
        
        with open(dockerfile_path, 'w') as f:
            f.write(content)
        
        # Create docker-compose.yml
        compose_path = self.project_root / "docker-compose.yml"
        
        compose_content = f"""version: '3.8'

services:
  metawalletgen:
    build: .
    image: metawalletgen/cli:{self.version}
    container_name: metawalletgen-cli
    volumes:
      - ./wallets:/app/wallets
      - ./config:/app/config
    environment:
      - PYTHONUNBUFFERED=1
    command: --help
    profiles:
      - cli
      - batch
      - interactive

  # Development service
  metawalletgen-dev:
    build: .
    image: metawalletgen/cli:dev
    container_name: metawalletgen-dev
    volumes:
      - .:/app
      - ./wallets:/app/wallets
      - ./config:/app/config
    environment:
      - PYTHONUNBUFFERED=1
      - PYTHONPATH=/app
    command: --help
    profiles:
      - dev
"""
        
        with open(compose_path, 'w') as f:
            f.write(compose_content)
    
    def create_deployment_guide(self):
        """Create comprehensive deployment guide"""
        print("📚 Creating deployment guide...")
        
        guide_path = self.project_root / "DEPLOYMENT.md"
        
        content = f"""# MetaWalletGen CLI - Deployment Guide

## Version: {self.version}

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
pip install dist/metawalletgen_cli-{self.version}-py3-none-any.whl
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
docker build -t metawalletgen/cli:{self.version} .

# Run container
docker run -it --rm -v $(pwd)/wallets:/app/wallets metawalletgen/cli:{self.version}

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

- **Source Distribution:** `metawalletgen_cli-{self.version}.tar.gz`
- **Wheel Distribution:** `metawalletgen_cli-{self.version}-py3-none-any.whl`
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

*Generated on: {platform.system()} {platform.release()}*
*Python Version: {sys.version}*
"""
        
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    def build_all(self):
        """Run complete build process"""
        print("🚀 Starting MetaWalletGen CLI build process...")
        print(f"📋 Version: {self.version}")
        print(f"🏗️  Platform: {platform.system()} {platform.release()}")
        print(f"🐍 Python: {sys.version}")
        print()
        
        steps = [
            ("Clean build directories", self.clean_build_dirs),
            ("Install build dependencies", self.install_build_deps),
            ("Run tests", self.run_tests),
            ("Build package", self.build_package),
            ("Check package quality", self.check_package),
            ("Create installer scripts", self.create_installer_scripts),
            ("Create deployment guide", self.create_deployment_guide),
        ]
        
        for step_name, step_func in steps:
            print(f"🔄 {step_name}...")
            if not step_func():
                print(f"❌ Build failed at: {step_name}")
                return False
            print()
        
        print("✅ Build completed successfully!")
        print(f"📦 Package files created in: {self.dist_dir}")
        print(f"📚 Documentation created: DEPLOYMENT.md")
        print()
        print("🚀 Ready for distribution!")
        
        return True

def main():
    """Main build function"""
    builder = PackageBuilder()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--clean":
        builder.clean_build_dirs()
        return
    
    success = builder.build_all()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
