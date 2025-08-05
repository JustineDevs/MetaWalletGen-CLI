"""
Main CLI Entry Point

This module provides the main entry point for the MetaWalletGen CLI tool
using the Click framework for command-line interface.
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
    help="Enable verbose output"
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
    - Batch wallet creation
    - Encrypted storage
    - Multiple output formats (JSON, CSV, encrypted)
    - MetaMask compatibility
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
        welcome_panel = Panel(welcome_text, border_style="blue")
        console.print(welcome_panel)


@main.command()
@click.option(
    "--count", "-c",
    default=1,
    type=int,
    help="Number of wallets to generate (default: 1)"
)
@click.option(
    "--output", "-o",
    help="Output filename (default: auto-generated)"
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
    help="Encrypt the output file"
)
@click.option(
    "--password", "-p",
    help="Encryption password (prompted if not provided)"
)
@click.option(
    "--network", "-n",
    type=click.Choice(["mainnet", "testnet"]),
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
    help="Generate a human-readable summary file"
)
@click.pass_context
def generate(ctx, count, output, format, encrypt, password, network, derivation, strength, summary):
    """Generate new Ethereum wallets."""
    generate_command(
        ctx, count, output, format, encrypt, password, 
        network, derivation, int(strength), summary
    )


@main.command()
@click.option(
    "--mnemonic", "-m",
    help="BIP-39 mnemonic phrase"
)
@click.option(
    "--private-key", "-k",
    help="Private key in hex format"
)
@click.option(
    "--output", "-o",
    help="Output filename (default: auto-generated)"
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
    help="Encrypt the output file"
)
@click.option(
    "--password", "-p",
    help="Encryption password (prompted if not provided)"
)
@click.option(
    "--network", "-n",
    type=click.Choice(["mainnet", "testnet"]),
    default="mainnet",
    help="Network type (default: mainnet)"
)
@click.option(
    "--derivation", "-d",
    help="Custom derivation path (default: m/44'/60'/0'/0/0)"
)
@click.pass_context
def import_wallet(ctx, mnemonic, private_key, output, format, encrypt, password, network, derivation):
    """Import wallet from mnemonic or private key."""
    import_command(
        ctx, mnemonic, private_key, output, format, 
        encrypt, password, network, derivation
    )


@main.command()
@click.option(
    "--file", "-f",
    help="Specific file to list information about"
)
@click.option(
    "--decrypt", "-d",
    is_flag=True,
    help="Attempt to decrypt encrypted files"
)
@click.option(
    "--password", "-p",
    help="Password for decryption"
)
@click.pass_context
def list(ctx, file, decrypt, password):
    """List wallet files and their information."""
    list_command(ctx, file, decrypt, password)


@main.command()
@click.argument("mnemonic", required=False)
@click.argument("private_key", required=False)
@click.option(
    "--type", "-t",
    type=click.Choice(["mnemonic", "private_key", "address"]),
    help="Type of data to validate"
)
@click.pass_context
def validate(ctx, mnemonic, private_key, type):
    """Validate mnemonic phrases, private keys, or addresses."""
    validate_command(ctx, mnemonic, private_key, type)


@main.command()
@click.option(
    "--file", "-f",
    required=True,
    help="File to decrypt"
)
@click.option(
    "--output", "-o",
    help="Output filename (default: auto-generated)"
)
@click.option(
    "--password", "-p",
    help="Decryption password (prompted if not provided)"
)
@click.pass_context
def decrypt(ctx, file, output, password):
    """Decrypt an encrypted wallet file."""
    from ..core.storage_manager import StorageManager
    
    storage = StorageManager()
    
    if not password:
        password = click.prompt("Enter decryption password", hide_input=True)
    
    try:
        if file.endswith('.json'):
            wallets = storage.load_wallets_json(file, decrypt=True, password=password)
        elif file.endswith('.csv'):
            wallets = storage.load_wallets_csv(file, decrypt=True, password=password)
        else:
            console.print(f"[red]Unsupported file format: {file}[/red]")
            sys.exit(1)
        
        # Save decrypted data
        if not output:
            output = file.replace('.enc', '_decrypted.json')
        
        storage.save_wallets_json(wallets, output, encrypt=False)
        console.print(f"[green]Successfully decrypted {len(wallets)} wallets to: {output}[/green]")
        
    except Exception as e:
        console.print(f"[red]Decryption failed: {str(e)}[/red]")
        sys.exit(1)


@main.command()
@click.option(
    "--file", "-f",
    required=True,
    help="File to encrypt"
)
@click.option(
    "--output", "-o",
    help="Output filename (default: auto-generated)"
)
@click.option(
    "--password", "-p",
    help="Encryption password (prompted if not provided)"
)
@click.pass_context
def encrypt(ctx, file, output, password):
    """Encrypt a wallet file."""
    from ..core.storage_manager import StorageManager
    
    storage = StorageManager()
    
    if not password:
        password = click.prompt("Enter encryption password", hide_input=True)
        confirm_password = click.prompt("Confirm password", hide_input=True)
        if password != confirm_password:
            console.print("[red]Passwords do not match[/red]")
            sys.exit(1)
    
    try:
        # Load wallets
        if file.endswith('.json'):
            wallets = storage.load_wallets_json(file, decrypt=False)
        elif file.endswith('.csv'):
            wallets = storage.load_wallets_csv(file, decrypt=False)
        else:
            console.print(f"[red]Unsupported file format: {file}[/red]")
            sys.exit(1)
        
        # Save encrypted data
        if not output:
            output = file.replace('.json', '.enc.json').replace('.csv', '.enc.json')
        
        storage.save_wallets_json(wallets, output, encrypt=True, password=password)
        console.print(f"[green]Successfully encrypted {len(wallets)} wallets to: {output}[/green]")
        
    except Exception as e:
        console.print(f"[red]Encryption failed: {str(e)}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main() 