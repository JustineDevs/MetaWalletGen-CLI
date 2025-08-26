#!/usr/bin/env python3
"""
Setup script for MetaWalletGen CLI

This script installs the MetaWalletGen CLI tool with all its dependencies.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "docs" / "README.md").read_text(encoding='utf-8')

# Read requirements
requirements = (this_directory / "deployment" / "requirements.txt").read_text(encoding='utf-8').splitlines()

setup(
    name="metawalletgen-cli",
    version="2.0.0",
    author="MetaWalletGen Team",
    author_email="team@metawalletgen.com",
    description="A secure command-line tool for generating Ethereum-compatible wallets",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/metawalletgen-cli",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Security",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-xdist>=3.0.0",
            "pytest-benchmark>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "bandit>=1.7.0",
            "safety>=2.0.0",
        ],
        "enterprise": [
            "flask>=2.3.0",
            "flask-cors>=4.0.0",
            "flask-limiter>=3.0.0",
            "psutil>=5.9.0",
            "pyyaml>=6.0.0",
            "pandas>=2.0.0",
            "matplotlib>=3.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "metawalletgen=metagen.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "metagen": [
            "config/*.yaml",
            "config/*.yml",
            "docs/*.md",
            "deployment/*.sh",
            "deployment/*.bat",
        ],
    },
    zip_safe=False,
    keywords="ethereum,wallet,cryptocurrency,blockchain,bip39,bip44,cli",
    project_urls={
        "Bug Reports": "https://github.com/your-org/metawalletgen-cli/issues",
        "Source": "https://github.com/your-org/metawalletgen-cli",
        "Documentation": "https://github.com/your-org/metawalletgen-cli/docs",
    },
)
