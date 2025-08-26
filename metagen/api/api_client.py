"""
API Client for MetaWalletGen CLI.

This module provides a Python client for programmatic access to the
MetaWalletGen CLI REST API.
"""

import json
import logging
import requests
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum


class APIError(Exception):
    """Custom exception for API errors."""
    
    def __init__(self, message: str, status_code: int = None, response: requests.Response = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class WalletStatus(Enum):
    """Wallet status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


@dataclass
class WalletInfo:
    """Wallet information structure."""
    id: str
    address: str
    user_id: str
    created_at: datetime
    tags: List[str]
    encrypted: bool
    status: WalletStatus = WalletStatus.ACTIVE


@dataclass
class UserInfo:
    """User information structure."""
    user_id: str
    username: str
    email: Optional[str]
    role: str
    created_at: datetime
    last_login: Optional[datetime]


class MetaWalletGenAPIClient:
    """Client for MetaWalletGen CLI REST API."""
    
    def __init__(self, base_url: str = "http://localhost:5000", 
                 username: str = None, password: str = None):
        """Initialize API client."""
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.auth_token = None
        self.logger = logging.getLogger(__name__)
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'MetaWalletGen-APIClient/1.0'
        })
        
        # Authenticate if credentials provided
        if username and password:
            self.authenticate(username, password)
    
    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate with the API."""
        try:
            response = self.session.post(f"{self.base_url}/login", json={
                'username': username,
                'password': password
            })
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.auth_token = data.get('token')
                    self.username = username
                    self.password = password
                    
                    # Update session headers with auth token
                    if self.auth_token:
                        self.session.headers.update({
                            'Authorization': f'Bearer {self.auth_token}'
                        })
                    
                    self.logger.info(f"Successfully authenticated as {username}")
                    return True
                else:
                    raise APIError("Authentication failed", response=response)
            else:
                raise APIError(f"Authentication failed: {response.status_code}", 
                             status_code=response.status_code, response=response)
                
        except requests.RequestException as e:
            raise APIError(f"Network error during authentication: {e}")
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request to API."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            
            # Handle authentication errors
            if response.status_code == 401:
                # Try to re-authenticate
                if self.username and self.password:
                    if self.authenticate(self.username, self.password):
                        # Retry request with new token
                        if self.auth_token:
                            self.session.headers.update({
                                'Authorization': f'Bearer {self.auth_token}'
                            })
                        response = self.session.request(method, url, **kwargs)
                    else:
                        raise APIError("Re-authentication failed", 
                                     status_code=response.status_code, response=response)
            
            # Handle other errors
            if response.status_code >= 400:
                error_msg = "API request failed"
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', error_msg)
                except:
                    pass
                
                raise APIError(error_msg, status_code=response.status_code, response=response)
            
            return response
            
        except requests.RequestException as e:
            raise APIError(f"Network error: {e}")
    
    def get_health(self) -> Dict[str, Any]:
        """Get system health status."""
        response = self._make_request('GET', '/health')
        return response.json()
    
    def create_wallet(self, tags: List[str] = None, encrypt: bool = True) -> WalletInfo:
        """Create a new wallet."""
        data = {
            'tags': tags or [],
            'encrypt': encrypt
        }
        
        response = self._make_request('POST', '/api/wallets', json=data)
        wallet_data = response.json()
        
        return WalletInfo(
            id=wallet_data['id'],
            address=wallet_data['address'],
            user_id=wallet_data['user_id'],
            created_at=datetime.fromisoformat(wallet_data['created_at']),
            tags=wallet_data.get('tags', []),
            encrypted=wallet_data.get('encrypted', False),
            status=WalletStatus(wallet_data.get('status', 'active'))
        )
    
    def list_wallets(self, limit: int = 100, offset: int = 0) -> List[WalletInfo]:
        """List user's wallets."""
        params = {'limit': limit, 'offset': offset}
        response = self._make_request('GET', '/api/wallets', params=params)
        wallets_data = response.json()
        
        wallets = []
        for wallet_data in wallets_data:
            wallet = WalletInfo(
                id=wallet_data['id'],
                address=wallet_data['address'],
                user_id=wallet_data['user_id'],
                created_at=datetime.fromisoformat(wallet_data['created_at']),
                tags=wallet_data.get('tags', []),
                encrypted=wallet_data.get('encrypted', False),
                status=WalletStatus(wallet_data.get('status', 'active'))
            )
            wallets.append(wallet)
        
        return wallets
    
    def get_wallet(self, wallet_id: str) -> WalletInfo:
        """Get specific wallet by ID."""
        response = self._make_request('GET', f'/api/wallets/{wallet_id}')
        wallet_data = response.json()
        
        return WalletInfo(
            id=wallet_data['id'],
            address=wallet_data['address'],
            user_id=wallet_data['user_id'],
            created_at=datetime.fromisoformat(wallet_data['created_at']),
            tags=wallet_data.get('tags', []),
            encrypted=wallet_data.get('encrypted', False),
            status=WalletStatus(wallet_data.get('status', 'active'))
        )
    
    def update_wallet_tags(self, wallet_id: str, tags: List[str]) -> bool:
        """Update wallet tags."""
        data = {'tags': tags}
        response = self._make_request('PUT', f'/api/wallets/{wallet_id}', json=data)
        return response.status_code == 200
    
    def archive_wallet(self, wallet_id: str) -> bool:
        """Archive a wallet."""
        data = {'status': 'archived'}
        response = self._make_request('PUT', f'/api/wallets/{wallet_id}', json=data)
        return response.status_code == 200
    
    def get_analytics(self, metric_type: str = None, time_range: str = None) -> Dict[str, Any]:
        """Get analytics data."""
        params = {}
        if metric_type:
            params['type'] = metric_type
        if time_range:
            params['range'] = time_range
        
        response = self._make_request('GET', '/api/analytics', params=params)
        return response.json()
    
    def get_compliance_report(self, format: str = "json") -> Union[str, Dict[str, Any]]:
        """Get compliance report."""
        params = {'format': format}
        response = self._make_request('GET', '/api/compliance/report', params=params)
        
        if format.lower() == 'json':
            return response.json()
        else:
            return response.text
    
    def run_compliance_check(self, rule_id: str = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run compliance check."""
        data = {}
        if rule_id:
            data['rule_id'] = rule_id
        if context:
            data['context'] = context
        
        response = self._make_request('POST', '/api/compliance/check', json=data)
        return response.json()
    
    def get_users(self) -> List[UserInfo]:
        """Get list of users (admin only)."""
        response = self._make_request('GET', '/api/users')
        users_data = response.json()
        
        users = []
        for user_data in users_data:
            user = UserInfo(
                user_id=user_data['user_id'],
                username=user_data['username'],
                email=user_data.get('email'),
                role=user_data['role'],
                created_at=datetime.fromisoformat(user_data['created_at']),
                last_login=datetime.fromisoformat(user_data['last_login']) if user_data.get('last_login') else None
            )
            users.append(user)
        
        return users
    
    def create_user(self, username: str, password: str, email: str = None, role: str = "user") -> UserInfo:
        """Create a new user (admin only)."""
        data = {
            'username': username,
            'password': password,
            'email': email,
            'role': role
        }
        
        response = self._make_request('POST', '/api/users', json=data)
        user_data = response.json()
        
        return UserInfo(
            user_id=user_data['user_id'],
            username=user_data['username'],
            email=user_data.get('email'),
            role=user_data['role'],
            created_at=datetime.fromisoformat(user_data['created_at']),
            last_login=None
        )
    
    def export_wallets(self, format: str = "json", file_path: str = None) -> str:
        """Export wallets to file."""
        params = {'format': format}
        response = self._make_request('GET', '/api/wallets/export', params=params)
        
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"wallets_export_{timestamp}.{format}"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            if format.lower() == 'json':
                json.dump(response.json(), f, indent=2, default=str)
            else:
                f.write(response.text)
        
        self.logger.info(f"Wallets exported to {file_path}")
        return file_path
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        response = self._make_request('GET', '/api/system/info')
        return response.json()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        response = self._make_request('GET', '/api/performance/metrics')
        return response.json()
    
    def run_benchmark(self, wallet_count: int = 100) -> Dict[str, Any]:
        """Run performance benchmark."""
        data = {'wallet_count': wallet_count}
        response = self._make_request('POST', '/api/performance/benchmark', json=data)
        return response.json()
    
    def close(self):
        """Close the API client session."""
        if self.session:
            self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Convenience functions for quick API access
def quick_wallet_creation(api_url: str, username: str, password: str, 
                          count: int = 1, tags: List[str] = None) -> List[WalletInfo]:
    """Quickly create multiple wallets."""
    with MetaWalletGenAPIClient(api_url, username, password) as client:
        wallets = []
        for i in range(count):
            wallet = client.create_wallet(tags=tags)
            wallets.append(wallet)
            print(f"Created wallet {i+1}/{count}: {wallet.address}")
        return wallets


def quick_analytics_report(api_url: str, username: str, password: str, 
                          format: str = "json") -> Union[str, Dict[str, Any]]:
    """Quickly get analytics report."""
    with MetaWalletGenAPIClient(api_url, username, password) as client:
        return client.get_analytics()


def quick_compliance_check(api_url: str, username: str, password: str) -> Dict[str, Any]:
    """Quickly run compliance check."""
    with MetaWalletGenAPIClient(api_url, username, password) as client:
        return client.run_compliance_check()


# Example usage
if __name__ == "__main__":
    # Example: Create a wallet
    try:
        client = MetaWalletGenAPIClient("http://localhost:5000", "admin", "password")
        
        # Create a wallet
        wallet = client.create_wallet(tags=["test", "example"])
        print(f"Created wallet: {wallet.address}")
        
        # List wallets
        wallets = client.list_wallets()
        print(f"Total wallets: {len(wallets)}")
        
        # Get analytics
        analytics = client.get_analytics()
        print(f"Analytics: {analytics}")
        
        client.close()
        
    except APIError as e:
        print(f"API Error: {e}")
    except Exception as e:
        print(f"Error: {e}")
