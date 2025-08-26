"""
Enhanced Logging Module

This module provides configurable logging for MetaWalletGen CLI
with support for different levels, formats, and output destinations.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme
from .config_manager import get_config

# Custom theme for rich logging
rich_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red",
    "critical": "red bold",
    "debug": "dim",
})


class MetaWalletGenLogger:
    """
    Enhanced logger for MetaWalletGen CLI with rich formatting and
    configurable output destinations.
    """
    
    def __init__(self, name: str = "metawalletgen"):
        """
        Initialize the logger.
        
        Args:
            name: Logger name
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.console = Console(theme=rich_theme)
        self.config = get_config()
        
        # Configure logging
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Setup logging configuration based on config."""
        # Get logging config
        log_config = self.config.get_logging()
        log_level = getattr(logging, log_config.get("level", "INFO").upper(), logging.INFO)
        log_format = log_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        log_file = log_config.get("file", "metawalletgen.log")
        console_logging = log_config.get("console", True)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set log level
        self.logger.setLevel(log_level)
        
        # Create formatter
        formatter = logging.Formatter(log_format)
        
        # Console handler with rich formatting
        if console_logging:
            console_handler = RichHandler(
                console=self.console,
                show_time=True,
                show_path=False,
                markup=True,
                rich_tracebacks=True
            )
            console_handler.setLevel(log_level)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # File handler
        if log_file:
            try:
                log_path = Path(log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setLevel(log_level)
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
            except Exception as e:
                # Fallback to console only if file logging fails
                self.warning(f"Could not setup file logging to {log_file}: {e}")
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def debug(self, message: str, *args, **kwargs) -> None:
        """Log debug message."""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs) -> None:
        """Log info message."""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs) -> None:
        """Log warning message."""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs) -> None:
        """Log error message."""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs) -> None:
        """Log critical message."""
        self.logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs) -> None:
        """Log exception with traceback."""
        self.logger.exception(message, *args, **kwargs)
    
    def log_wallet_generation(self, count: int, network: str, format: str, encrypted: bool) -> None:
        """Log wallet generation event."""
        self.info(
            "Generated %d wallet(s) for %s network, format: %s, encrypted: %s",
            count, network, format, encrypted
        )
    
    def log_wallet_import(self, count: int, source_file: str, format: str) -> None:
        """Log wallet import event."""
        self.info(
            "Imported %d wallet(s) from %s, format: %s",
            count, source_file, format
        )
    
    def log_file_operation(self, operation: str, filepath: str, success: bool, error: Optional[str] = None) -> None:
        """Log file operation event."""
        if success:
            self.info("File operation '%s' completed successfully: %s", operation, filepath)
        else:
            self.error("File operation '%s' failed: %s - %s", operation, filepath, error or "Unknown error")
    
    def log_validation_result(self, total: int, valid: int, invalid: int) -> None:
        """Log validation result."""
        if invalid == 0:
            self.info("Validation completed: %d/%d wallets are valid", valid, total)
        else:
            self.warning("Validation completed: %d/%d wallets are valid, %d have issues", valid, total, invalid)
    
    def log_security_event(self, event_type: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Log security-related events."""
        if details:
            self.info("Security event '%s': %s", event_type, details)
        else:
            self.info("Security event: %s", event_type)
    
    def log_performance_metric(self, operation: str, duration: float, count: Optional[int] = None) -> None:
        """Log performance metrics."""
        if count:
            self.info("Performance: %s completed in %.2f seconds (%d items)", operation, duration, count)
        else:
            self.info("Performance: %s completed in %.2f seconds", operation, duration)
    
    def set_level(self, level: str) -> None:
        """
        Set logging level dynamically.
        
        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        try:
            log_level = getattr(logging, level.upper())
            self.logger.setLevel(log_level)
            
            # Update all handlers
            for handler in self.logger.handlers:
                handler.setLevel(log_level)
            
            self.info("Logging level set to: %s", level.upper())
        except AttributeError:
            self.error("Invalid logging level: %s", level)
    
    def add_file_handler(self, filepath: str, level: Optional[str] = None) -> None:
        """
        Add a new file handler.
        
        Args:
            filepath: Path to log file
            level: Optional logging level for this handler
        """
        try:
            log_path = Path(filepath)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Get formatter from existing handler
            formatter = None
            for handler in self.logger.handlers:
                if hasattr(handler, 'formatter') and handler.formatter:
                    formatter = handler.formatter
                    break
            
            if not formatter:
                formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            
            # Create file handler
            file_handler = logging.FileHandler(filepath, encoding='utf-8')
            if level:
                file_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
            else:
                file_handler.setLevel(self.logger.level)
            
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
            self.info("Added file handler: %s", filepath)
        except Exception as e:
            self.error("Could not add file handler %s: %s", filepath, e)
    
    def get_log_file_paths(self) -> list:
        """Get list of current log file paths."""
        log_files = []
        for handler in self.logger.handlers:
            if isinstance(handler, logging.FileHandler):
                log_files.append(handler.baseFilename)
        return log_files
    
    def rotate_logs(self, max_size_mb: int = 10, max_backups: int = 5) -> None:
        """
        Rotate log files if they exceed size limit.
        
        Args:
            max_size_mb: Maximum log file size in MB
            max_backups: Maximum number of backup files
        """
        max_size_bytes = max_size_mb * 1024 * 1024
        
        for handler in self.logger.handlers:
            if isinstance(handler, logging.FileHandler):
                filepath = Path(handler.baseFilename)
                if filepath.exists() and filepath.stat().st_size > max_size_bytes:
                    self._rotate_log_file(filepath, max_backups)
    
    def _rotate_log_file(self, filepath: Path, max_backups: int) -> None:
        """Rotate a single log file."""
        try:
            # Remove oldest backup if we have too many
            for i in range(max_backups - 1, 0, -1):
                old_backup = filepath.with_suffix(f".{i}")
                if old_backup.exists():
                    old_backup.unlink()
            
            # Rename current log file to .1
            backup_path = filepath.with_suffix(".1")
            if backup_path.exists():
                backup_path.unlink()
            
            filepath.rename(backup_path)
            self.info("Rotated log file: %s -> %s", filepath.name, backup_path.name)
            
        except Exception as e:
            self.error("Could not rotate log file %s: %s", filepath, e)


# Global logger instance
logger = MetaWalletGenLogger()


def get_logger(name: Optional[str] = None) -> MetaWalletGenLogger:
    """
    Get logger instance.
    
    Args:
        name: Optional logger name (defaults to main logger)
        
    Returns:
        Logger instance
    """
    if name:
        return MetaWalletGenLogger(name)
    return logger


def setup_logging(level: str = "INFO", log_file: Optional[str] = None, 
                  console: bool = True) -> MetaWalletGenLogger:
    """
    Setup logging with custom configuration.
    
    Args:
        level: Logging level
        log_file: Optional log file path
        console: Whether to enable console logging
        
    Returns:
        Configured logger instance
    """
    # Update config
    config = get_config()
    config.set("logging.level", level)
    config.set("logging.file", log_file or "metawalletgen.log")
    config.set("logging.console", console)
    
    # Create new logger with updated config
    return MetaWalletGenLogger()
