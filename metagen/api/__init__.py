"""
MetaWalletGen CLI - API Interfaces Module

Provides RESTful API for programmatic access and
web dashboard for wallet management.
"""

__version__ = "2.0.0"
__author__ = "MetaWalletGen Team"
__email__ = "support@metawalletgen.com"

from .rest_api import MetaWalletGenAPI
from .web_dashboard import WebDashboard
from .api_client import APIClient

__all__ = [
    'MetaWalletGenAPI',
    'WebDashboard', 
    'APIClient'
]
