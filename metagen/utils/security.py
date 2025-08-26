"""
Advanced Security Utilities Module

This module provides enhanced security features including:
- Password strength validation
- Rate limiting for sensitive operations
- Audit logging
- Security policy enforcement
"""

import re
import time
import hashlib
import secrets
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging


@dataclass
class PasswordPolicy:
    """Password policy configuration."""
    min_length: int = 12
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_numbers: bool = True
    require_special_chars: bool = True
    max_common_passwords: int = 1000
    prevent_reuse: bool = True
    max_age_days: int = 90


@dataclass
class SecurityEvent:
    """Security event record."""
    timestamp: datetime
    event_type: str
    user_id: Optional[str]
    ip_address: Optional[str]
    details: Dict
    severity: str = "INFO"


class SecurityManager:
    """Advanced security management system."""
    
    def __init__(self, password_policy: Optional[PasswordPolicy] = None):
        self.password_policy = password_policy or PasswordPolicy()
        self.failed_attempts: Dict[str, List[float]] = {}
        self.locked_accounts: Dict[str, float] = {}
        self.audit_logger = logging.getLogger("security_audit")
        self._setup_audit_logging()
        
        # Common weak passwords to check against
        self.common_passwords = self._load_common_passwords()
    
    def _setup_audit_logging(self):
        """Setup audit logging configuration."""
        handler = logging.FileHandler("security_audit.log")
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        self.audit_logger.addHandler(handler)
        self.audit_logger.setLevel(logging.INFO)
    
    def _load_common_passwords(self) -> set:
        """Load list of common weak passwords."""
        # This would typically load from a secure database or file
        # For now, we'll use a small set of examples
        return {
            "password", "123456", "qwerty", "admin", "letmein",
            "welcome", "monkey", "dragon", "master", "football"
        }
    
    def validate_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        """
        Validate password against security policy.
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check length
        if len(password) < self.password_policy.min_length:
            issues.append(f"Password must be at least {self.password_policy.min_length} characters")
        
        # Check character requirements
        if self.password_policy.require_uppercase and not re.search(r'[A-Z]', password):
            issues.append("Password must contain at least one uppercase letter")
        
        if self.password_policy.require_lowercase and not re.search(r'[a-z]', password):
            issues.append("Password must contain at least one lowercase letter")
        
        if self.password_policy.require_numbers and not re.search(r'\d', password):
            issues.append("Password must contain at least one number")
        
        if self.password_policy.require_special_chars and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            issues.append("Password must contain at least one special character")
        
        # Check against common passwords
        if password.lower() in self.common_passwords:
            issues.append("Password is too common and easily guessable")
        
        # Check for patterns
        if re.search(r'(.)\1{2,}', password):
            issues.append("Password contains repeated characters")
        
        if re.search(r'(123|abc|qwe)', password.lower()):
            issues.append("Password contains common keyboard patterns")
        
        # Calculate entropy
        entropy = self._calculate_password_entropy(password)
        if entropy < 50:
            issues.append("Password entropy is too low")
        
        return len(issues) == 0, issues
    
    def _calculate_password_entropy(self, password: str) -> float:
        """Calculate password entropy (bits)."""
        char_set_size = 0
        if re.search(r'[a-z]', password):
            char_set_size += 26
        if re.search(r'[A-Z]', password):
            char_set_size += 26
        if re.search(r'\d', password):
            char_set_size += 10
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            char_set_size += 32
        
        if char_set_size == 0:
            return 0
        
        return len(password) * (char_set_size ** 0.5)
    
    def generate_secure_password(self, length: int = 16) -> str:
        """Generate a cryptographically secure password."""
        if length < self.password_policy.min_length:
            length = self.password_policy.min_length
        
        # Character sets
        lowercase = "abcdefghijklmnopqrstuvwxyz"
        uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        digits = "0123456789"
        special = "!@#$%^&*(),.?\":{}|<>"
        
        # Ensure at least one character from each required set
        password = []
        if self.password_policy.require_lowercase:
            password.append(secrets.choice(lowercase))
        if self.password_policy.require_uppercase:
            password.append(secrets.choice(uppercase))
        if self.password_policy.require_numbers:
            password.append(secrets.choice(digits))
        if self.password_policy.require_special_chars:
            password.append(secrets.choice(special))
        
        # Fill remaining length with random characters
        all_chars = lowercase + uppercase + digits + special
        while len(password) < length:
            password.append(secrets.choice(all_chars))
        
        # Shuffle the password
        password_list = list(password)
        secrets.SystemRandom().shuffle(password_list)
        return ''.join(password_list)
    
    def check_rate_limit(self, identifier: str, max_attempts: int = 5, 
                        window_minutes: int = 15) -> bool:
        """
        Check if operation is rate limited.
        
        Args:
            identifier: Unique identifier (IP, user ID, etc.)
            max_attempts: Maximum attempts allowed in window
            window_minutes: Time window in minutes
            
        Returns:
            True if operation is allowed, False if rate limited
        """
        now = time.time()
        window_seconds = window_minutes * 60
        
        # Clean old attempts
        if identifier in self.failed_attempts:
            self.failed_attempts[identifier] = [
                attempt for attempt in self.failed_attempts[identifier]
                if now - attempt < window_seconds
            ]
        
        # Check if account is locked
        if identifier in self.locked_accounts:
            lock_time = self.locked_accounts[identifier]
            if now - lock_time < window_seconds:
                return False
            else:
                del self.locked_accounts[identifier]
        
        # Check rate limit
        attempts = self.failed_attempts.get(identifier, [])
        if len(attempts) >= max_attempts:
            # Lock account
            self.locked_accounts[identifier] = now
            self.log_security_event(
                "RATE_LIMIT_EXCEEDED",
                identifier,
                {"max_attempts": max_attempts, "window_minutes": window_minutes}
            )
            return False
        
        return True
    
    def record_failed_attempt(self, identifier: str):
        """Record a failed authentication attempt."""
        now = time.time()
        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = []
        self.failed_attempts[identifier].append(now)
        
        self.log_security_event(
            "FAILED_ATTEMPT",
            identifier,
            {"attempt_count": len(self.failed_attempts[identifier])}
        )
    
    def log_security_event(self, event_type: str, user_id: Optional[str], 
                          details: Dict, severity: str = "INFO"):
        """Log a security event."""
        event = SecurityEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            user_id=user_id,
            ip_address=None,  # Would be set in web context
            details=details,
            severity=severity
        )
        
        # Log to audit log
        log_message = f"{event.event_type} - User: {event.user_id} - {event.details}"
        if event.severity == "ERROR":
            self.audit_logger.error(log_message)
        elif event.severity == "WARNING":
            self.audit_logger.warning(log_message)
        else:
            self.audit_logger.info(log_message)
    
    def get_security_report(self) -> Dict:
        """Generate security status report."""
        now = time.time()
        window_seconds = 15 * 60  # 15 minutes
        
        # Count recent failed attempts
        recent_failures = 0
        for attempts in self.failed_attempts.values():
            recent_failures += len([a for a in attempts if now - a < window_seconds])
        
        # Count locked accounts
        active_locks = 0
        for lock_time in self.locked_accounts.values():
            if now - lock_time < window_seconds:
                active_locks += 1
        
        return {
            "timestamp": datetime.now().isoformat(),
            "recent_failed_attempts": recent_failures,
            "active_locks": active_locks,
            "total_tracked_identifiers": len(self.failed_attempts),
            "security_status": "NORMAL" if recent_failures < 10 else "ELEVATED"
        }


def get_security_manager(policy: Optional[PasswordPolicy] = None) -> SecurityManager:
    """Get or create security manager instance."""
    if not hasattr(get_security_manager, '_instance'):
        get_security_manager._instance = SecurityManager(policy)
    return get_security_manager._instance
