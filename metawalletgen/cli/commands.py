"""
CLI Commands Module

This module contains the implementation of all CLI commands
for the MetaWalletGen CLI tool with enhanced validation and error handling.
"""

import sys
import os
import datetime
from typing import Optional
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from tqdm import tqdm
from pathlib import Path

from ..core.wallet_generator import WalletGenerator
from ..core.storage_manager import StorageManager
from ..utils.validators import (
    validate_ethereum_address, 
    validate_private_key, 
    validate_mnemonic, 
    validate_derivation_path
)

console = Console()


def validate_generation_inputs(count: int, strength: int, network: str, derivation: Optional[str]) -> None:
    """Validate all generation inputs before processing."""
    errors = []
    
    if count < 1:
        errors.append("Count must be at least 1")
    elif count > 10000:
        errors.append("Count cannot exceed 10,000 for performance reasons")
    
    if strength not in [128, 160, 192, 224, 256]:
        errors.append("Strength must be one of: 128, 160, 192, 224, 256")
    
    if network not in ["mainnet", "testnet", "sepolia"]:
        errors.append("Network must be one of: mainnet, testnet, sepolia")
    
    if derivation and not validate_derivation_path(derivation):
        errors.append("Invalid derivation path format")
    
    if errors:
        console.print("[red]Validation errors:[/red]")
        for error in errors:
            console.print(f"  • {error}")
        sys.exit(1)


def get_encryption_password(encrypt: bool, password: Optional[str], confirm: bool = True) -> Optional[str]:
    """Get encryption password with proper validation."""
    if not encrypt:
        return None
    
    if password:
        # Check if password is from environment variable
        if password.startswith("$"):
            env_var = password[1:]
            password = os.getenv(env_var)
            if not password:
                console.print(f"[red]Environment variable {env_var} not set[/red]")
                sys.exit(1)
            console.print(f"[green]Using password from environment variable {env_var}[/green]")
    
    if not password:
        password = Prompt.ask("Enter encryption password", password=True)
        if confirm:
            confirm_password = Prompt.ask("Confirm password", password=True)
            if password != confirm_password:
                console.print("[red]Passwords do not match[/red]")
                sys.exit(1)
    
    # Validate password strength
    if len(password) < 8:
        console.print("[yellow]Warning: Password is shorter than 8 characters[/yellow]")
        if not Confirm.ask("Continue with weak password?"):
            sys.exit(0)
    
    return password


def generate_command(
    ctx, count, output, format, encrypt, password, 
    network, derivation, strength, summary, verbose
):
    """Generate new Ethereum wallets with enhanced validation and feedback."""
    
    # Initialize console
    if ctx.obj.get("quiet", False):
        console = Console(quiet=True)
    else:
        console = Console()
    
    # Enhanced input validation
    validate_generation_inputs(count, strength, network, derivation)
    
    # Initialize components
    generator = WalletGenerator(network=network)
    storage = StorageManager()
    
    # Handle encryption password with enhanced security
    password = get_encryption_password(encrypt, password)
    
    # Display generation parameters
    if verbose:
        console.print(f"[blue]Generation Parameters:[/blue]")
        console.print(f"  • Count: {count}")
        console.print(f"  • Network: {network}")
        console.print(f"  • Strength: {strength} bits")
        console.print(f"  • Derivation: {derivation or generator.default_derivation}")
        console.print(f"  • Format: {format}")
        console.print(f"  • Encryption: {'Yes' if encrypt else 'No'}")
        console.print()
    
    # Generate wallets with enhanced progress tracking
    console.print(f"[blue]Generating {count} wallet(s)...[/blue]")
    
    if count == 1:
        # Single wallet generation
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Generating wallet...", total=1)
            wallets = [generator.generate_new_wallet()]
            progress.update(task, advance=1)
    else:
        # Batch wallet generation with progress bar
        wallets = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Generating wallets...", total=count)
            
            for i in range(count):
                wallet = generator.generate_new_wallet(index=i)
                wallets.append(wallet)
                progress.update(task, advance=1)
                
                if verbose and (i + 1) % 100 == 0:
                    progress.print(f"[green]Generated {i + 1}/{count} wallets[/green]")
    
    # Generate output filename if not provided
    if not output:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output = f"wallets_{count}_{timestamp}.{format}"
    
    # Ensure proper file extension
    if not output.endswith(f".{format}"):
        output = f"{output}.{format}"
    
    # Save wallets with enhanced error handling
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
        
        # Enhanced success feedback
        console.print(f"[green]✅ Successfully generated {len(wallets)} wallet(s)[/green]")
        console.print(f"[green]📁 Saved to: {filepath}[/green]")
        
        # Show file size and location
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            file_size_mb = file_size / (1024 * 1024)
            console.print(f"[blue]📊 File size: {file_size_mb:.2f} MB[/blue]")
        
        # Generate summary if requested
        if summary:
            try:
                summary_file = storage.save_wallet_summary(wallets)
                console.print(f"[green]📋 Summary saved to: {summary_file}[/green]")
            except Exception as e:
                console.print(f"[yellow]⚠️  Warning: Could not save summary: {e}[/yellow]")
        
        # Display wallet preview (first few wallets)
        if verbose and wallets:
            console.print(f"\n[blue]Wallet Preview (showing first 3):[/blue]")
            preview_table = Table(show_header=True, header_style="bold magenta")
            preview_table.add_column("Index", style="cyan")
            preview_table.add_column("Address", style="green")
            preview_table.add_column("Private Key", style="red")
            preview_table.add_column("Mnemonic", style="yellow")
            
            for i, wallet in enumerate(wallets[:3]):
                preview_table.add_row(
                    str(i + 1),
                    f"{wallet.address[:10]}...{wallet.address[-8:]}",
                    f"{wallet.private_key[:10]}...{wallet.private_key[-8:]}",
                    f"{wallet.mnemonic[:30]}..." if len(wallet.mnemonic) > 30 else wallet.mnemonic
                )
            
            console.print(preview_table)
        
        # Security reminder
        if encrypt:
            console.print(f"\n[green]🔒 File is encrypted with AES-256[/green]")
            console.print(f"[yellow]⚠️  Remember your password - it cannot be recovered![/yellow]")
        else:
            console.print(f"\n[yellow]⚠️  Warning: File is not encrypted - keep it secure![/yellow]")
        
    except Exception as e:
        console.print(f"[red]❌ Error saving wallets: {e}[/red]")
        if verbose:
            import traceback
            console.print(f"[red]Traceback:[/red]")
            console.print(Syntax(traceback.format_exc(), "python", theme="monokai"))
        sys.exit(1)
    
    # Clear sensitive data from memory
    if hasattr(generator, '_clear_sensitive_data'):
        generator._clear_sensitive_data()
    
    return wallets


def import_command(
    ctx, input_file, output, format, encrypt, password, 
    network, derivation, summary, verbose
):
    """Import wallets from existing data with enhanced validation."""
    
    # Initialize console
    if ctx.obj.get("quiet", False):
        console = Console(quiet=True)
    else:
        console = Console()
    
    # Validate input file
    if not os.path.exists(input_file):
        console.print(f"[red]❌ Input file not found: {input_file}[/red]")
        sys.exit(1)
    
    # Initialize components
    generator = WalletGenerator(network=network)
    storage = StorageManager()
    
    # Handle encryption password
    password = get_encryption_password(encrypt, password)
    
    try:
        # Import wallets based on file type
        if input_file.endswith('.json'):
            wallets = storage.load_wallets_json(input_file)
        elif input_file.endswith('.csv'):
            wallets = storage.load_wallets_csv(input_file)
        elif input_file.endswith('.yaml') or input_file.endswith('.yml'):
            wallets = storage.load_wallets_yaml(input_file)
        else:
            console.print(f"[red]❌ Unsupported file format: {input_file}[/red]")
            sys.exit(1)
        
        if not wallets:
            console.print(f"[yellow]⚠️  No wallets found in {input_file}[/yellow]")
            sys.exit(0)
        
        console.print(f"[green]✅ Successfully imported {len(wallets)} wallet(s)[/green]")
        
        # Validate imported wallets
        if verbose:
            console.print(f"[blue]Validating imported wallets...[/blue]")
            valid_count = 0
            for i, wallet in enumerate(wallets):
                if (validate_ethereum_address(wallet.address) and 
                    validate_private_key(wallet.private_key)):
                    valid_count += 1
                else:
                    console.print(f"[yellow]⚠️  Wallet {i+1} has invalid data[/yellow]")
            
            console.print(f"[green]✅ {valid_count}/{len(wallets)} wallets are valid[/green]")
        
        # Generate output filename if not provided
        if not output:
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output = f"{base_name}_imported_{timestamp}.{format}"
        
        # Save imported wallets
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
        
        console.print(f"[green]📁 Saved imported wallets to: {filepath}[/green]")
        
        # Generate summary if requested
        if summary:
            summary_file = storage.save_wallet_summary(wallets)
            console.print(f"[green]📋 Summary saved to: {summary_file}[/green]")
        
    except Exception as e:
        console.print(f"[red]❌ Error importing wallets: {e}[/red]")
        if verbose:
            import traceback
            console.print(f"[red]Traceback:[/red]")
            console.print(Syntax(traceback.format_exc(), "python", theme="monokai"))
        sys.exit(1)


def list_command(ctx, directory, verbose):
    """List wallet files with enhanced information display."""
    
    # Initialize console
    if ctx.obj.get("quiet", False):
        console = Console(quiet=True)
    else:
        console = Console()
    
    # Use default directory if not specified
    if not directory:
        directory = "wallets"
    
    if not os.path.exists(directory):
        console.print(f"[red]❌ Directory not found: {directory}[/red]")
        sys.exit(1)
    
    # Find wallet files
    wallet_files = []
    for ext in ['*.json', '*.csv', '*.yaml', '*.yml']:
        wallet_files.extend(Path(directory).glob(ext))
    
    if not wallet_files:
        console.print(f"[yellow]⚠️  No wallet files found in {directory}[/yellow]")
        return
    
    # Display wallet files information
    console.print(f"[blue]📁 Wallet files in {directory}:[/blue]")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Filename", style="cyan")
    table.add_column("Size", style="green")
    table.add_column("Modified", style="yellow")
    table.add_column("Type", style="blue")
    table.add_column("Encrypted", style="red")
    
    for file_path in sorted(wallet_files):
        try:
            stat = file_path.stat()
            size_mb = stat.st_size / (1024 * 1024)
            modified = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            
            # Determine file type and encryption status
            file_type = file_path.suffix[1:].upper()
            is_encrypted = "Unknown"
            
            # Try to detect if file is encrypted
            try:
                with open(file_path, 'r') as f:
                    content = f.read(100)  # Read first 100 chars
                    if '"encrypted": true' in content or '"vault"' in content:
                        is_encrypted = "Yes"
                    else:
                        is_encrypted = "No"
            except:
                is_encrypted = "Error"
            
            table.add_row(
                file_path.name,
                f"{size_mb:.2f} MB",
                modified,
                file_type,
                is_encrypted
            )
        except Exception as e:
            if verbose:
                console.print(f"[yellow]⚠️  Error reading {file_path.name}: {e}[/yellow]")
    
    console.print(table)
    console.print(f"[green]✅ Found {len(wallet_files)} wallet file(s)[/green]")


def validate_command(ctx, input_file, verbose):
    """Validate wallet data with detailed feedback."""
    
    # Initialize console
    if ctx.obj.get("quiet", False):
        console = Console(quiet=True)
    else:
        console = Console()
    
    # Validate input file
    if not os.path.exists(input_file):
        console.print(f"[red]❌ Input file not found: {input_file}[/red]")
        sys.exit(1)
    
    try:
        # Load wallets
        storage = StorageManager()
        if input_file.endswith('.json'):
            wallets = storage.load_wallets_json(input_file)
        elif input_file.endswith('.csv'):
            wallets = storage.load_wallets_csv(input_file)
        elif input_file.endswith('.yaml') or input_file.endswith('.yml'):
            wallets = storage.load_wallets_yaml(input_file)
        else:
            console.print(f"[red]❌ Unsupported file format: {input_file}[/red]")
            sys.exit(1)
        
        if not wallets:
            console.print(f"[yellow]⚠️  No wallets found in {input_file}[/yellow]")
            return
        
        console.print(f"[blue]🔍 Validating {len(wallets)} wallet(s)...[/blue]")
        
        # Validation results
        validation_results = {
            'total': len(wallets),
            'valid': 0,
            'invalid_address': 0,
            'invalid_private_key': 0,
            'invalid_mnemonic': 0,
            'details': []
        }
        
        # Validate each wallet
        for i, wallet in enumerate(wallets):
            wallet_errors = []
            
            # Validate address
            if not validate_ethereum_address(wallet.address):
                wallet_errors.append("Invalid address")
                validation_results['invalid_address'] += 1
            
            # Validate private key
            if not validate_private_key(wallet.private_key):
                wallet_errors.append("Invalid private key")
                validation_results['invalid_private_key'] += 1
            
            # Validate mnemonic if present
            if wallet.mnemonic and not validate_mnemonic(wallet.mnemonic):
                wallet_errors.append("Invalid mnemonic")
                validation_results['invalid_mnemonic'] += 1
            
            if not wallet_errors:
                validation_results['valid'] += 1
                status = "✅ Valid"
            else:
                status = f"❌ {'; '.join(wallet_errors)}"
            
            validation_results['details'].append({
                'index': i + 1,
                'address': wallet.address,
                'status': status,
                'errors': wallet_errors
            })
        
        # Display validation summary
        console.print(f"\n[blue]📊 Validation Summary:[/blue]")
        summary_table = Table(show_header=True, header_style="bold magenta")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Count", style="green")
        summary_table.add_column("Percentage", style="yellow")
        
        summary_table.add_row("Total Wallets", str(validation_results['total']), "100%")
        summary_table.add_row("Valid", str(validation_results['valid']), 
                             f"{(validation_results['valid']/validation_results['total']*100):.1f}%")
        summary_table.add_row("Invalid Address", str(validation_results['invalid_address']),
                             f"{(validation_results['invalid_address']/validation_results['total']*100):.1f}%")
        summary_table.add_row("Invalid Private Key", str(validation_results['invalid_private_key']),
                             f"{(validation_results['invalid_private_key']/validation_results['total']*100):.1f}%")
        summary_table.add_row("Invalid Mnemonic", str(validation_results['invalid_mnemonic']),
                             f"{(validation_results['invalid_mnemonic']/validation_results['total']*100):.1f}%")
        
        console.print(summary_table)
        
        # Display detailed results if verbose
        if verbose:
            console.print(f"\n[blue]📋 Detailed Results:[/blue]")
            detail_table = Table(show_header=True, header_style="bold magenta")
            detail_table.add_column("Index", style="cyan")
            detail_table.add_column("Address", style="green")
            detail_table.add_column("Status", style="yellow")
            
            for detail in validation_results['details']:
                detail_table.add_row(
                    str(detail['index']),
                    f"{detail['address'][:10]}...{detail['address'][-8:]}",
                    detail['status']
                )
            
            console.print(detail_table)
        
        # Final status
        if validation_results['valid'] == validation_results['total']:
            console.print(f"\n[green]🎉 All wallets are valid![/green]")
        else:
            console.print(f"\n[yellow]⚠️  {validation_results['total'] - validation_results['valid']} wallet(s) have issues[/yellow]")
        
    except Exception as e:
        console.print(f"[red]❌ Error validating wallets: {e}[/red]")
        if verbose:
            import traceback
            console.print(f"[red]Traceback:[/red]")
            console.print(Syntax(traceback.format_exc(), "python", theme="monokai"))
        sys.exit(1) 