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

from metagen.core.wallet_generator import WalletGenerator
from metagen.core.storage_manager import StorageManager
from metagen.utils.validators import (
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
    
    # Validate input file - check both absolute and relative paths
    file_exists = False
    actual_path = input_file
    
    if os.path.exists(input_file):
        file_exists = True
        actual_path = input_file
    elif os.path.exists(os.path.join("wallets", input_file)):
        file_exists = True
        actual_path = os.path.join("wallets", input_file)
    
    if not file_exists:
        console.print(f"[red]❌ Input file not found: {input_file}[/red]")
        console.print(f"[yellow]💡 Try using just the filename if it's in the wallets directory[/yellow]")
        sys.exit(1)
    
    try:
        # Load wallets
        storage = StorageManager()
        
        # Handle both relative and absolute paths
        if os.path.isabs(input_file):
            # If absolute path, extract just the filename for storage manager
            filename = os.path.basename(input_file)
        else:
            # If relative path, use as is
            filename = input_file
            
        if input_file.endswith('.json'):
            wallets = storage.load_wallets_json(filename)
        elif input_file.endswith('.csv'):
            wallets = storage.load_wallets_csv(filename)
        elif input_file.endswith('.yaml') or input_file.endswith('.yml'):
            wallets = storage.load_wallets_yaml(filename)
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


def security_command(ctx, verbose):
    """Display security status and audit information."""
    
    # Initialize console
    if ctx.obj.get("quiet", False):
        console = Console(quiet=True)
    else:
        console = Console()
    
    try:
        from ..utils.security import get_security_manager
        
        security_mgr = get_security_manager()
        report = security_mgr.get_security_report()
        
        console.print(f"[blue]🔒 Security Status Report[/blue]")
        console.print("=" * 50)
        
        # Security status
        status_color = "green" if report["security_status"] == "NORMAL" else "red"
        console.print(f"[{status_color}]Security Status: {report['security_status']}[/{status_color}]")
        
        # Security metrics
        console.print(f"\n[blue]Security Metrics (Last 15 minutes):[/blue]")
        metrics_table = Table(show_header=True, header_style="bold magenta")
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", style="green")
        metrics_table.add_column("Status", style="yellow")
        
        # Failed attempts
        failed_attempts = report["recent_failed_attempts"]
        failed_status = "🟢 Normal" if failed_attempts < 5 else "🟡 Warning" if failed_attempts < 10 else "🔴 Critical"
        metrics_table.add_row("Failed Attempts", str(failed_attempts), failed_status)
        
        # Active locks
        active_locks = report["active_locks"]
        lock_status = "🟢 None" if active_locks == 0 else "🟡 Active" if active_locks < 3 else "🔴 Multiple"
        metrics_table.add_row("Active Locks", str(active_locks), lock_status)
        
        # Tracked identifiers
        tracked = report["total_tracked_identifiers"]
        tracked_status = "🟢 Normal" if tracked < 10 else "🟡 Elevated" if tracked < 50 else "🔴 High"
        metrics_table.add_row("Tracked Identifiers", str(tracked), tracked_status)
        
        console.print(metrics_table)
        
        # Password policy information
        policy = security_mgr.password_policy
        console.print(f"\n[blue]Password Policy:[/blue]")
        policy_table = Table(show_header=True, header_style="bold magenta")
        policy_table.add_column("Requirement", style="cyan")
        policy_table.add_column("Setting", style="green")
        
        policy_table.add_row("Minimum Length", str(policy.min_length))
        policy_table.add_row("Uppercase Required", "Yes" if policy.require_uppercase else "No")
        policy_table.add_row("Lowercase Required", "Yes" if policy.require_lowercase else "No")
        policy_table.add_row("Numbers Required", "Yes" if policy.require_numbers else "No")
        policy_table.add_row("Special Chars Required", "Yes" if policy.require_special_chars else "No")
        policy_table.add_row("Max Age (days)", str(policy.max_age_days))
        
        console.print(policy_table)
        
        # Security recommendations
        console.print(f"\n[blue]🔍 Security Recommendations:[/blue]")
        if failed_attempts > 5:
            console.print("  • Consider implementing additional rate limiting")
        if active_locks > 0:
            console.print("  • Review locked accounts and consider manual intervention")
        if tracked > 20:
            console.print("  • Monitor for potential security threats")
        
        if failed_attempts <= 5 and active_locks == 0 and tracked <= 20:
            console.print("  • Security posture appears healthy")
        
        # Audit log information
        if verbose:
            console.print(f"\n[blue]📋 Recent Security Events:[/blue]")
            console.print("  • Check security_audit.log for detailed event history")
            console.print("  • Monitor for unusual patterns or spikes in activity")
        
    except ImportError:
        console.print("[red]❌ Security module not available[/red]")
        console.print("[yellow]💡 Install required dependencies for security features[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error retrieving security information: {e}[/red]")


def performance_command(ctx, verbose):
    """Display performance metrics and optimization suggestions."""
    
    # Initialize console
    if ctx.obj.get("quiet", False):
        console = Console(quiet=True)
    else:
        console = Console()
    
    try:
        from ..utils.performance import get_performance_monitor
        
        monitor = get_performance_monitor()
        summary = monitor.get_performance_summary()
        
        if "error" in summary:
            console.print(f"[yellow]⚠️  {summary['error']}[/yellow]")
            console.print("[blue]💡 Start performance monitoring to collect metrics[/blue]")
            return
        
        console.print(f"[blue]📊 Performance Status Report[/blue]")
        console.print("=" * 50)
        
        # Overall status
        status = summary["status"]
        status_color = "green" if status == "NORMAL" else "yellow" if status in ["ATTENTION", "WARNING"] else "red"
        console.print(f"[{status_color}]Overall Status: {status}[/{status_color}]")
        
        # Performance metrics
        console.print(f"\n[blue]Performance Metrics (Last {summary['time_window_minutes']} minutes):[/blue]")
        metrics_table = Table(show_header=True, header_style="bold magenta")
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Average", style="green")
        metrics_table.add_column("Peak", style="yellow")
        metrics_table.add_column("Trend", style="blue")
        
        # CPU metrics
        cpu_avg = summary["averages"]["cpu_percent"]
        cpu_peak = summary["peaks"]["cpu_percent"]
        cpu_trend = summary["trends"]["cpu_trend"]
        cpu_trend_arrow = "↗️" if cpu_trend > 0 else "↘️" if cpu_trend < 0 else "➡️"
        
        metrics_table.add_row(
            "CPU Usage (%)", 
            f"{cpu_avg}%", 
            f"{cpu_peak}%",
            f"{cpu_trend_arrow} {abs(cpu_trend):.1f}%"
        )
        
        # Memory metrics
        mem_avg = summary["averages"]["memory_mb"]
        mem_peak = summary["peaks"]["memory_mb"]
        mem_trend = summary["trends"]["memory_trend"]
        mem_trend_arrow = "↗️" if mem_trend > 0 else "↘️" if mem_trend < 0 else "➡️"
        
        metrics_table.add_row(
            "Memory Usage (MB)", 
            f"{mem_avg:.1f}", 
            f"{mem_peak:.1f}",
            f"{mem_trend_arrow} {abs(mem_trend):.1f} MB"
        )
        
        console.print(metrics_table)
        
        # Data summary
        console.print(f"\n[blue]Data Summary:[/blue]")
        console.print(f"  • Data Points: {summary['data_points']}")
        console.print(f"  • Time Window: {summary['time_window_minutes']} minutes")
        
        # Optimization suggestions
        suggestions = monitor.get_optimization_suggestions()
        console.print(f"\n[blue]🔧 Optimization Suggestions:[/blue]")
        for suggestion in suggestions:
            console.print(f"  • {suggestion}")
        
        # Performance monitoring status
        if monitor.monitoring:
            console.print(f"\n[green]✅ Performance monitoring is active[/green]")
        else:
            console.print(f"\n[yellow]⚠️  Performance monitoring is inactive[/yellow]")
            console.print("  • Use 'start_performance_monitoring' to begin collection")
        
        # Export option
        if verbose:
            console.print(f"\n[blue]📁 Export Options:[/blue]")
            console.print("  • Use 'export_metrics' to save performance data")
            console.print("  • Supported formats: JSON")
        
    except ImportError:
        console.print("[red]❌ Performance module not available[/red]")
        console.print("[yellow]💡 Install psutil for performance monitoring features[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error retrieving performance information: {e}[/red]")


def health_command(ctx, verbose):
    """Perform comprehensive system health check."""
    
    # Initialize console
    if ctx.obj.get("quiet", False):
        console = Console(quiet=True)
    else:
        console = Console()
    
    console.print(f"[blue]🏥 System Health Check[/blue]")
    console.print("=" * 50)
    
    health_status = {"checks": [], "overall": "HEALTHY"}
    
    # Check 1: Python environment
    try:
        import sys
        python_version = sys.version_info
        if python_version.major == 3 and python_version.minor >= 8:
            health_status["checks"].append(("Python Version", "✅", f"Python {python_version.major}.{python_version.minor}.{python_version.micro}"))
        else:
            health_status["checks"].append(("Python Version", "❌", f"Python {python_version.major}.{python_version.minor}.{python_version.micro} (3.8+ required)"))
            health_status["overall"] = "DEGRADED"
    except Exception as e:
        health_status["checks"].append(("Python Version", "❌", f"Error: {e}"))
        health_status["overall"] = "UNHEALTHY"
    
    # Check 2: Core dependencies
    core_deps = ["hdwallet", "cryptography", "rich", "click"]
    for dep in core_deps:
        try:
            module = __import__(dep)
            version = getattr(module, '__version__', 'Unknown')
            health_status["checks"].append((f"{dep} Dependency", "✅", f"v{version}"))
        except ImportError:
            health_status["checks"].append((f"{dep} Dependency", "❌", "Not installed"))
            health_status["overall"] = "UNHEALTHY"
    
    # Check 3: File system access
    try:
        test_dir = "wallets"
        if os.path.exists(test_dir):
            if os.access(test_dir, os.W_OK):
                health_status["checks"].append(("File System Access", "✅", "Wallets directory writable"))
            else:
                health_status["checks"].append(("File System Access", "⚠️", "Wallets directory not writable"))
                health_status["overall"] = "DEGRADED"
        else:
            try:
                os.makedirs(test_dir, exist_ok=True)
                health_status["checks"].append(("File System Access", "✅", "Wallets directory created"))
            except Exception as e:
                health_status["checks"].append(("File System Access", "❌", f"Cannot create wallets directory: {e}"))
                health_status["overall"] = "UNHEALTHY"
    except Exception as e:
        health_status["checks"].append(("File System Access", "❌", f"Error: {e}"))
        health_status["overall"] = "UNHEALTHY"
    
    # Check 4: Wallet generation capability
    try:
        from ..core.wallet_generator import WalletGenerator
        generator = WalletGenerator()
        test_wallet = generator.generate_new_wallet()
        if test_wallet and test_wallet.address:
            health_status["checks"].append(("Wallet Generation", "✅", "Core functionality working"))
        else:
            health_status["checks"].append(("Wallet Generation", "❌", "Generated wallet is invalid"))
            health_status["overall"] = "UNHEALTHY"
    except Exception as e:
        health_status["checks"].append(("Wallet Generation", "❌", f"Error: {e}"))
        health_status["overall"] = "UNHEALTHY"
    
    # Check 5: Storage functionality
    try:
        from ..core.storage_manager import StorageManager
        storage = StorageManager()
        health_status["checks"].append(("Storage System", "✅", "Storage manager initialized"))
    except Exception as e:
        health_status["checks"].append(("Storage System", "❌", f"Error: {e}"))
        health_status["overall"] = "UNHEALTHY"
    
    # Check 6: Configuration system
    try:
        from ..utils.config_manager import get_config
        config = get_config()
        defaults = config.get_defaults()
        if defaults:
            health_status["checks"].append(("Configuration", "✅", f"{len(defaults)} settings loaded"))
        else:
            health_status["checks"].append(("Configuration", "⚠️", "No default settings"))
            health_status["overall"] = "DEGRADED"
    except Exception as e:
        health_status["checks"].append(("Configuration", "❌", f"Error: {e}"))
        health_status["overall"] = "UNHEALTHY"
    
    # Display health check results
    overall_color = {
        "HEALTHY": "green",
        "DEGRADED": "yellow", 
        "UNHEALTHY": "red"
    }[health_status["overall"]]
    
    console.print(f"[{overall_color}]Overall Health: {health_status['overall']}[/{overall_color}]")
    
    # Display individual checks
    console.print(f"\n[blue]Health Check Results:[/blue]")
    health_table = Table(show_header=True, header_style="bold magenta")
    health_table.add_column("Component", style="cyan")
    health_table.add_column("Status", style="green")
    health_table.add_column("Details", style="yellow")
    
    for component, status, details in health_status["checks"]:
        health_table.add_row(component, status, details)
    
    console.print(health_table)
    
    # Recommendations
    console.print(f"\n[blue]💡 Recommendations:[/blue]")
    if health_status["overall"] == "HEALTHY":
        console.print("  • System is healthy and ready for production use")
        console.print("  • Continue regular monitoring and maintenance")
    elif health_status["overall"] == "DEGRADED":
        console.print("  • Some components have issues but system is functional")
        console.print("  • Review warnings and address non-critical issues")
    else:
        console.print("  • System has critical issues requiring immediate attention")
        console.print("  • Review error messages and fix critical problems")
        console.print("  • Consider reinstalling or updating dependencies")
    
    # Additional checks for verbose mode
    if verbose:
        console.print(f"\n[blue]🔍 Additional Diagnostics:[/blue]")
        
        # Memory usage
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            console.print(f"  • Current Memory Usage: {memory_mb:.1f} MB")
            
            if memory_mb > 500:
                console.print("  • Memory usage is high - consider optimization")
        except ImportError:
            console.print("  • psutil not available for memory diagnostics")
        
        # Disk space
        try:
            disk_usage = psutil.disk_usage('.')
            free_gb = disk_usage.free / (1024**3)
            console.print(f"  • Available Disk Space: {free_gb:.1f} GB")
            
            if free_gb < 1:
                console.print("  • Low disk space - consider cleanup")
        except:
            console.print("  • Cannot check disk space")
    
    return health_status["overall"] 