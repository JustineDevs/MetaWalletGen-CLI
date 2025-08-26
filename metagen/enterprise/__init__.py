"""
MetaWalletGen CLI - Enterprise Features Module

Provides enterprise-grade features including:
- Multi-user authentication and role-based access control
- Database integration for wallet management
- Advanced reporting and analytics
- Audit logging and compliance
- Enterprise security features
"""

__version__ = "2.0.0"
__author__ = "MetaWalletGen Team"
__email__ = "support@metawalletgen.com"

from .auth import AuthManager, User, Role, Permission
from .database import DatabaseManager, WalletRepository
from .analytics import AnalyticsEngine, ReportGenerator
from .audit import AuditLogger, ComplianceChecker

__all__ = [
    'AuthManager', 'User', 'Role', 'Permission',
    'DatabaseManager', 'WalletRepository',
    'AnalyticsEngine', 'ReportGenerator',
    'AuditLogger', 'ComplianceChecker'
]
