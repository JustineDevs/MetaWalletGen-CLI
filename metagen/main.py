#!/usr/bin/env python3
"""
MetaWalletGen CLI - Main Entry Point

This is the main entry point for the MetaWalletGen CLI tool.
It provides a command-line interface for wallet generation and management.
"""

import sys
import os
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.commands import main

if __name__ == "__main__":
    main()
