"""
Main CLI Entry Point

This module provides the main entry point for the MetaWalletGen CLI tool
using the Click framework for command-line interface with enhanced features.
"""

import sys
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from .commands import generate_command, import_command, list_command, validate_command

console = Console()


@click.group()
@click.version_option(version="1.0.0", prog_name="MetaWalletGen CLI")
@click.option(
    "--verbose", "-v", 
    is_flag=True, 
    help="Enable verbose output with detailed information"
)
@click.option(
    "--quiet", "-q", 
    is_flag=True, 
    help="Suppress output except errors"
)
@click.pass_context
def main(ctx, verbose, quiet):
    """
    MetaWalletGen CLI - A secure command-line tool for generating Ethereum-compatible wallets.
    
    This tool supports:
    - Generating wallets using BIP-39/BIP-44 standards
    - Batch wallet creation with progress tracking
    - Encrypted storage with AES-256
    - Multiple output formats (JSON, CSV, YAML)
    - Wallet validation and import/export
    - MetaMask compatibility
    - Enhanced security features
    """
    # Ensure context object exists
    ctx.ensure_object(dict)
    
    # Store options in context
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    
    if not quiet:
        # Display welcome message
        welcome_text = Text("MetaWalletGen CLI", style="bold blue")
        welcome_text.append("\nSecure Ethereum Wallet Generator", style="green")
        welcome_text.append("\nEnhanced with validation, encryption, and progress tracking", style="yellow")
        welcome_panel = Panel(welcome_text, border_style="blue")
        console.print(welcome_panel)


@main.command()
@click.option(
    "--count", "-c",
    default=1,
    type=int,
    help="Number of wallets to generate (default: 1, max: 10,000)"
)
@click.option(
    "--output", "-o",
    help="Output filename (default: auto-generated with timestamp)"
)
@click.option(
    "--format", "-f",
    type=click.Choice(["json", "csv", "yaml"]),
    default="json",
    help="Output format (default: json)"
)
@click.option(
    "--encrypt", "-e",
    is_flag=True,
    help="Encrypt the output file with AES-256"
)
@click.option(
    "--password", "-p",
    help="Encryption password (use $ENV_VAR for environment variable)"
)
@click.option(
    "--network", "-n",
    type=click.Choice(["mainnet", "testnet", "sepolia"]),
    default="mainnet",
    help="Network type (default: mainnet)"
)
@click.option(
    "--derivation", "-d",
    help="Custom derivation path (default: m/44'/60'/0'/0/0)"
)
@click.option(
    "--strength", "-s",
    type=click.Choice(["128", "160", "192", "224", "256"]),
    default="128",
    help="Mnemonic strength in bits (default: 128)"
)
@click.option(
    "--summary", "-S",
    is_flag=True,
    help="Generate a summary report of generated wallets"
)
@click.pass_context
def generate(ctx, count, output, format, encrypt, password, 
             network, derivation, strength, summary):
    """
    Generate new Ethereum wallets with enhanced security and validation.
    
    Examples:
        # Generate a single wallet
        metawalletgen generate
        
        # Generate 10 encrypted wallets
        metawalletgen generate --count 10 --encrypt --password mypassword
        
        # Generate wallets with custom parameters
        metawalletgen generate -c 5 -f csv -n testnet -s 256
        
        # Use environment variable for password
        metawalletgen generate -c 3 --encrypt --password $WALLET_PASSWORD
    """
    # Convert strength to int
    strength = int(strength)
    
    # Get verbose flag from context
    verbose = ctx.obj.get("verbose", False)
    
    generate_command(
        ctx, count, output, format, encrypt, password,
        network, derivation, strength, summary, verbose
    )


@main.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "--output", "-o",
    help="Output filename (default: auto-generated with timestamp)"
)
@click.option(
    "--format", "-f",
    type=click.Choice(["json", "csv", "yaml"]),
    default="json",
    help="Output format (default: json)"
)
@click.option(
    "--encrypt", "-e",
    is_flag=True,
    help="Encrypt the output file with AES-256"
)
@click.option(
    "--password", "-p",
    help="Encryption password (use $ENV_VAR for environment variable)"
)
@click.option(
    "--network", "-n",
    type=click.Choice(["mainnet", "testnet", "sepolia"]),
    default="mainnet",
    help="Network type for imported wallets (default: mainnet)"
)
@click.option(
    "--derivation", "-d",
    help="Custom derivation path for imported wallets"
)
@click.option(
    "--summary", "-S",
    is_flag=True,
    help="Generate a summary report of imported wallets"
)
@click.pass_context
def import_wallets(ctx, input_file, output, format, encrypt, password,
                   network, derivation, summary):
    """
    Import wallets from existing data files with validation.
    
    Supported formats: JSON, CSV, YAML
    
    Examples:
        # Import from JSON file
        metawalletgen import wallets.json
        
        # Import and encrypt
        metawalletgen import wallets.csv --encrypt --password mypassword
        
        # Import with custom format
        metawalletgen import wallets.yaml -f json -o imported_wallets.json
    """
    # Get verbose flag from context
    verbose = ctx.obj.get("verbose", False)
    
    import_command(
        ctx, input_file, output, format, encrypt, password,
        network, derivation, summary, verbose
    )


@main.command()
@click.option(
    "--directory", "-d",
    type=click.Path(exists=True),
    help="Directory to list (default: wallets/)"
)
@click.pass_context
def list(ctx, directory):
    """
    List wallet files with detailed information.
    
    Shows file size, modification date, type, and encryption status.
    
    Examples:
        # List files in default wallets directory
        metawalletgen list
        
        # List files in custom directory
        metawalletgen list --directory /path/to/wallets
    """
    # Get verbose flag from context
    verbose = ctx.obj.get("verbose", False)
    
    list_command(ctx, directory, verbose)


@main.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.pass_context
def validate(ctx, input_file):
    """
    Validate wallet data with comprehensive checks.
    
    Performs validation on addresses, private keys, and mnemonics.
    
    Examples:
        # Validate wallets in JSON file
        metawalletgen validate wallets.json
        
        # Validate wallets in CSV file
        metawalletgen validate wallets.csv
    """
    # Get verbose flag from context
    verbose = ctx.obj.get("verbose", False)
    
    validate_command(ctx, input_file, verbose)


@main.command()
def info():
    """Display system information and configuration."""
    console.print("[blue]MetaWalletGen CLI System Information[/blue]")
    console.print("=" * 50)
    
    # Python version
    import sys
    console.print(f"Python Version: {sys.version}")
    
    # Package version
    try:
        import metawalletgen
        console.print(f"MetaWalletGen Version: 1.0.0")
    except ImportError:
        console.print("MetaWalletGen: Not installed")
    
    # Check dependencies
    console.print("\n[blue]Dependencies:[/blue]")
    dependencies = [
        ("hdwallet", "HD Wallet functionality"),
        ("web3", "Ethereum interaction"),
        ("eth-account", "Account management"),
        ("cryptography", "Encryption support"),
        ("rich", "Enhanced CLI interface"),
        ("click", "CLI framework")
    ]
    
    for dep, description in dependencies:
        try:
            module = __import__(dep)
            version = getattr(module, '__version__', 'Unknown')
            console.print(f"  ✅ {dep}: {version} - {description}")
        except ImportError:
            console.print(f"  ❌ {dep}: Not installed - {description}")
    
    # Configuration info
    console.print("\n[blue]Configuration:[/blue]")
    import os
    config_file = "config.yaml"
    if os.path.exists(config_file):
        console.print(f"  ✅ Config file: {config_file}")
    else:
        console.print(f"  ⚠️  Config file: {config_file} (not found)")
    
    wallets_dir = "wallets"
    if os.path.exists(wallets_dir):
        console.print(f"  ✅ Wallets directory: {wallets_dir}")
    else:
        console.print(f"  ⚠️  Wallets directory: {wallets_dir} (not found)")


@main.command()
def examples():
    """Show usage examples and common commands."""
    console.print("[blue]MetaWalletGen CLI Usage Examples[/blue]")
    console.print("=" * 50)
    
    examples_data = [
        ("Generate a single wallet", "metawalletgen generate"),
        ("Generate 5 encrypted wallets", "metawalletgen generate -c 5 --encrypt"),
        ("Generate wallets for testnet", "metawalletgen generate -c 3 -n testnet"),
        ("Import from existing file", "metawalletgen import wallets.json"),
        ("List wallet files", "metawalletgen list"),
        ("Validate wallet data", "metawalletgen validate wallets.json"),
        ("Show system info", "metawalletgen info"),
        ("Get help", "metawalletgen --help"),
    ]
    
    for description, command in examples_data:
        console.print(f"[cyan]{description}:[/cyan]")
        console.print(f"  {command}")
        console.print()
    
    console.print("[yellow]For more detailed help on any command:[/yellow]")
    console.print("  metawalletgen <command> --help")


if __name__ == "__main__":
    main() 