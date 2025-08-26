#!/usr/bin/env python3
"""
MetaWalletGen CLI - Professional Ethereum Wallet Generator
Enhanced setup configuration for PyPI distribution
"""

from setuptools import setup, find_packages
import os

# Read the README file for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Professional Ethereum Wallet Generator with Advanced Security Features"

# Read requirements
def read_requirements():
    req_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(req_path):
        with open(req_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="metawalletgen-cli",
    version="2.0.0",
    author="MetaWalletGen Team",
    author_email="support@metawalletgen.com",
    description="Professional Ethereum Wallet Generator with Advanced Security & Performance Features",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/metawalletgen/cli",
    project_urls={
        "Bug Tracker": "https://github.com/metawalletgen/cli/issues",
        "Documentation": "https://metawalletgen.com/docs",
        "Source Code": "https://github.com/metawalletgen/cli",
        "Security": "https://metawalletgen.com/security",
    },
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
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Security :: Cryptography",
        "Topic :: Office/Business :: Financial",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    keywords=[
        "ethereum", "wallet", "cryptocurrency", "blockchain", "bip39", "bip44",
        "cryptography", "security", "cli", "command-line", "hdwallet", "metamask"
    ],
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
        ],
        "enterprise": [
            "psycopg2-binary>=2.9.0",
            "redis>=4.0.0",
            "celery>=5.0.0",
            "prometheus-client>=0.16.0",
        ],
        "full": [
            "psutil>=5.9.0",
            "rich>=13.0.0",
            "cryptography>=41.0.0",
            "hdwallet>=2.2.0",
            "eth-account>=0.9.0",
            "click>=8.0.0",
            "pyyaml>=6.0.0",
            "pandas>=2.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "metawalletgen=metawalletgen.cli.main:main",
            "mwg=metawalletgen.cli.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "metawalletgen": [
            "config/*.yaml",
            "config/*.yml",
            "templates/*.txt",
            "*.md",
        ],
    },
    zip_safe=False,
    platforms=["any"],
    license="MIT",
    maintainer="MetaWalletGen Team",
    maintainer_email="maintainers@metawalletgen.com",
) 