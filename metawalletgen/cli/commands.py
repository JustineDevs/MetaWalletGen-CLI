"""
CLI Commands Module

This module contains the implementation of all CLI commands
for the MetaWalletGen CLI tool.
"""

import sys
import datetime
from typing import Optional
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text
from tqdm import tqdm

from ..core.wallet_generator import WalletGenerator
from ..core.storage_manager import StorageManager

console = Console()


def generate_command(
    ctx, count, output, format, encrypt, password, 
    network, derivation, strength, summary
):
    """Generate new Ethereum wallets."""
    
    if ctx.obj.get("quiet", False):
        console = Console(quiet=True)
    
    # Validate inputs
    if count < 1:
        console.print("[red]Count must be at least 1[/red]")
        sys.exit(1)
    
    if count > 10000:
        console.print("[yellow]Warning: Generating more than 10,000 wallets may take a while[/yellow]")
        if not click.confirm("Continue?"):
            sys.exit(0)
    
    # Initialize components
    generator = WalletGenerator(network=network)
    storage = StorageManager()
    
    # Handle encryption password
    if encrypt and not password:
        password = click.prompt("Enter encryption password", hide_input=True)
        confirm_password = click.prompt("Confirm password", hide_input=True)
        if password != confirm_password:
            console.print("[red]Passwords do not match[/red]")
            sys.exit(1)
    
    # Generate wallets
    console.print(f"[blue]Generating {count} wallet(s)...[/blue]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Generating wallets...", total=count)
        
        if count == 1:
            wallets = [generator.generate_new_wallet()]
            progress.update(task, advance=1)
        else:
            wallets = generator.generate_batch_wallets(count)
            progress.update(task, advance=count)
    
    # Generate output filename if not provided
    if not output:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output = f"wallets_{count}_{timestamp}.{format}"
    
    # Save wallets
    try:
        if format == "json":
            filepath = storage.save_wallets_json(
                wallets, output, encrypt=encrypt, password=password
            )
        elif format == "csv":
            filepath = storage.save_wallets_csv(
                wallets, output, encrypt=encrypt, password=password
            )
        elif format == "yaml":
            filepath = storage.save_wallets_yaml(
                wallets, output, encrypt=encrypt, password=password
            )
        
        console.print(f"[green]Successfully generated {len(wallets)} wallet(s)[/green]")
        console.print(f"[green]Saved to: {filepath}[/green]")
        
        # Generate summary if requested
        if summary:
            summary_file = storage.save_wallet_summary(wallets)
            console.print(f"[green]Summary saved to: {summary_file}[/green]")
        
        # Display wallet information
        if not ctx.obj.get("quiet", False) and count <= 5:
            display_wallets(wallets)
        
    except Exception as e:
        console.print(f"[red]Error saving wallets: {str(e)}[/red]")
        sys.exit(1)


def import_command(
    ctx, mnemonic, private_key, output, format, 
    encrypt, password, network, derivation
):
    """Import wallet from mnemonic or private key."""
    
    if ctx.obj.get("quiet", False):
        console = Console(quiet=True)
    
    # Validate inputs
    if not mnemonic and not private_key:
        console.print("[red]Either --mnemonic or --private-key must be provided[/red]")
        sys.exit(1)
    
    if mnemonic and private_key:
        console.print("[red]Cannot provide both mnemonic and private key[/red]")
        sys.exit(1)
    
    # Initialize components
    generator = WalletGenerator(network=network)
    storage = StorageManager()
    
    # Handle encryption password
    if encrypt and not password:
        password = click.prompt("Enter encryption password", hide_input=True)
        confirm_password = click.prompt("Confirm password", hide_input=True)
        if password != confirm_password:
            console.print("[red]Passwords do not match[/red]")
            sys.exit(1)
    
    try:
        # Import wallet
        if mnemonic:
            console.print("[blue]Importing wallet from mnemonic...[/blue]")
            wallet = generator.create_wallet_from_mnemonic(
                mnemonic, derivation_path=derivation
            )
        else:
            console.print("[blue]Importing wallet from private key...[/blue]")
            wallet = generator.create_wallet_from_private_key(private_key)
        
        wallets = [wallet]
        
        # Generate output filename if not provided
        if not output:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output = f"imported_wallet_{timestamp}.{format}"
        
        # Save wallet
        if format == "json":
            filepath = storage.save_wallets_json(
                wallets, output, encrypt=encrypt, password=password
            )
        elif format == "csv":
            filepath = storage.save_wallets_csv(
                wallets, output, encrypt=encrypt, password=password
            )
        elif format == "yaml":
            filepath = storage.save_wallets_yaml(
                wallets, output, encrypt=encrypt, password=password
            )
        
        console.print(f"[green]Successfully imported wallet[/green]")
        console.print(f"[green]Saved to: {filepath}[/green]")
        
        # Display wallet information
        if not ctx.obj.get("quiet", False):
            display_wallets(wallets)
        
    except Exception as e:
        console.print(f"[red]Error importing wallet: {str(e)}[/red]")
        sys.exit(1)


def list_command(ctx, file, decrypt, password):
    """List wallet files and their information."""
    
    if ctx.obj.get("quiet", False):
        console = Console(quiet=True)
    
    storage = StorageManager()
    
    try:
        if file:
            # List specific file
            info = storage.get_file_info(file)
            display_file_info(info)
        else:
            # List all files
            files = storage.list_wallet_files()
            if not files:
                console.print("[yellow]No wallet files found[/yellow]")
                return
            
            display_file_list(files)
            
            if decrypt and password:
                # Try to decrypt and show wallet count
                for file_info in files:
                    if file_info.get("encrypted", False):
                        try:
                            if file_info["filename"].endswith('.json'):
                                wallets = storage.load_wallets_json(
                                    file_info["filename"], decrypt=True, password=password
                                )
                            elif file_info["filename"].endswith('.csv'):
                                wallets = storage.load_wallets_csv(
                                    file_info["filename"], decrypt=True, password=password
                                )
                            else:
                                continue
                            
                            console.print(f"[green]Decrypted {file_info['filename']}: {len(wallets)} wallets[/green]")
                        except Exception as e:
                            console.print(f"[red]Failed to decrypt {file_info['filename']}: {str(e)}[/red]")
        
    except Exception as e:
        console.print(f"[red]Error listing files: {str(e)}[/red]")
        sys.exit(1)


def validate_command(ctx, mnemonic, private_key, type):
    """Validate mnemonic phrases, private keys, or addresses."""
    
    if ctx.obj.get("quiet", False):
        console = Console(quiet=True)
    
    generator = WalletGenerator()
    
    if type == "mnemonic" or mnemonic:
        if not mnemonic:
            mnemonic = click.prompt("Enter mnemonic phrase")
        
        is_valid = generator.validate_mnemonic(mnemonic)
        if is_valid:
            console.print("[green]✓ Valid mnemonic phrase[/green]")
        else:
            console.print("[red]✗ Invalid mnemonic phrase[/red]")
            sys.exit(1)
    
    elif type == "private_key" or private_key:
        if not private_key:
            private_key = click.prompt("Enter private key")
        
        is_valid = generator.validate_private_key(private_key)
        if is_valid:
            console.print("[green]✓ Valid private key[/green]")
        else:
            console.print("[red]✗ Invalid private key[/red]")
            sys.exit(1)
    
    elif type == "address":
        address = click.prompt("Enter Ethereum address")
        
        # Check if it's a valid address format
        try:
            checksum_address = generator.to_checksum_address(address)
            is_checksum_valid = generator.verify_address_checksum(checksum_address)
            
            if is_checksum_valid:
                console.print(f"[green]✓ Valid Ethereum address: {checksum_address}[/green]")
            else:
                console.print(f"[yellow]⚠ Address format is valid but checksum is incorrect: {checksum_address}[/yellow]")
        except Exception:
            console.print("[red]✗ Invalid Ethereum address format[/red]")
            sys.exit(1)
    
    else:
        console.print("[red]Please specify what to validate (mnemonic, private_key, or address)[/red]")
        sys.exit(1)


def display_wallets(wallets):
    """Display wallet information in a formatted table."""
    table = Table(title="Generated Wallets")
    table.add_column("Index", style="cyan", no_wrap=True)
    table.add_column("Address", style="green")
    table.add_column("Private Key", style="red")
    table.add_column("Mnemonic", style="yellow")
    table.add_column("Derivation Path", style="blue")
    
    for i, wallet in enumerate(wallets, 1):
        table.add_row(
            str(i),
            wallet.address,
            wallet.private_key[:10] + "..." if len(wallet.private_key) > 10 else wallet.private_key,
            wallet.mnemonic[:20] + "..." if wallet.mnemonic and len(wallet.mnemonic) > 20 else wallet.mnemonic,
            wallet.derivation_path
        )
    
    console.print(table)


def display_file_info(info):
    """Display information about a specific file."""
    table = Table(title=f"File Information: {info['filename']}")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    for key, value in info.items():
        if key != "filename":
            table.add_row(key.replace("_", " ").title(), str(value))
    
    console.print(table)


def display_file_list(files):
    """Display a list of wallet files."""
    table = Table(title="Wallet Files")
    table.add_column("Filename", style="cyan")
    table.add_column("Size", style="green")
    table.add_column("Wallets", style="yellow")
    table.add_column("Encrypted", style="red")
    table.add_column("Modified", style="blue")
    
    for file_info in files:
        encrypted_status = "Yes" if file_info.get("encrypted", False) else "No"
        wallet_count = str(file_info.get("wallet_count", "Unknown"))
        size_mb = f"{file_info['size_bytes'] / 1024:.1f} KB"
        
        table.add_row(
            file_info["filename"],
            size_mb,
            wallet_count,
            encrypted_status,
            file_info["modified"][:10]  # Just the date part
        )
    
    console.print(table) 