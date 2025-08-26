#!/usr/bin/env python3
"""
Simple CLI runner for MetaWalletGen
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Run the CLI"""
    try:
        print("🚀 Starting MetaWalletGen CLI...")
        print("=" * 50)
        
        # Import and run CLI
        from metawalletgen.cli.main import main as cli_main
        
        # Simulate command line arguments for testing
        sys.argv = ['metawalletgen', '--help']
        
        print("Running CLI with --help flag...")
        cli_main()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed:")
        print("  pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Error running CLI: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 