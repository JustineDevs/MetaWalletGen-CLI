"""
RESTful API for MetaWalletGen CLI

Provides programmatic access to wallet generation, management,
and enterprise features through HTTP endpoints.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import asdict
from pathlib import Path
import hashlib
import hmac
import time
import secrets

from flask import Flask, request, jsonify, make_response, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import check_password_hash, generate_password_hash

from metagen.enterprise.auth import AuthManager, Permission
from metagen.enterprise.database import DatabaseManager, WalletRepository
from metagen.enterprise.analytics import AnalyticsEngine, ReportGenerator
from metagen.enterprise.audit import AuditLogger, AuditLevel
from metagen.core.wallet_generator import WalletGenerator
from metagen.core.encryption import EncryptionManager
from metagen.core.storage_manager import StorageManager

logger = logging.getLogger(__name__)

class MetaWalletGenAPI:
    """RESTful API server for MetaWalletGen CLI"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.app = Flask(__name__)
        self.setup_app()
        
        # Initialize enterprise components
        self.auth_manager = AuthManager()
        self.db_manager = DatabaseManager()
        self.wallet_repo = WalletRepository(self.db_manager)
        self.analytics_engine = AnalyticsEngine(self.db_manager)
        self.audit_logger = AuditLogger()
        
        # Initialize core components
        self.wallet_generator = WalletGenerator()
        self.encryption_manager = EncryptionManager()
        self.storage_manager = StorageManager()
        
        # Setup rate limiting
        self.limiter = Limiter(
            app=self.app,
            key_func=get_remote_address,
            default_limits=["200 per day", "50 per hour"]
        )
        
        self.setup_routes()
        self.setup_middleware()
    
    def setup_app(self) -> None:
        """Setup Flask application configuration"""
        self.app.config['SECRET_KEY'] = self.config.get('secret_key', secrets.token_urlsafe(32))
        self.app.config['JSON_SORT_KEYS'] = False
        self.app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
        
        # Enable CORS
        CORS(self.app, resources={
            r"/api/*": {
                "origins": self.config.get('allowed_origins', ["*"]),
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"]
            }
        })
    
    def setup_middleware(self) -> None:
        """Setup API middleware"""
        @self.app.before_request
        def before_request():
            g.start_time = time.time()
            g.request_id = secrets.token_urlsafe(16)
            
            # Log request
            logger.info(f"Request {g.request_id}: {request.method} {request.path}")
        
        @self.app.after_request
        def after_request(response):
            # Calculate response time
            response_time = time.time() - g.start_time
            
            # Add response headers
            response.headers['X-Request-ID'] = g.request_id
            response.headers['X-Response-Time'] = f"{response_time:.3f}s"
            
            # Log response
            logger.info(f"Response {g.request_id}: {response.status_code} ({response_time:.3f}s)")
            
            return response
        
        @self.app.errorhandler(Exception)
        def handle_exception(e):
            logger.error(f"Unhandled exception: {e}")
            return jsonify({
                'error': 'Internal server error',
                'message': str(e),
                'request_id': g.request_id
            }), 500
    
    def setup_routes(self) -> None:
        """Setup API routes"""
        
        # Health check endpoint
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'version': '2.0.0',
                'services': {
                    'database': 'connected',
                    'auth': 'active',
                    'wallet_generator': 'ready'
                }
            })
        
        # Authentication endpoints
        @self.app.route('/api/auth/login', methods=['POST'])
        @self.limiter.limit("5 per minute")
        def login():
            """User login endpoint"""
            try:
                data = request.get_json()
                username = data.get('username')
                password = data.get('password')
                
                if not username or not password:
                    return jsonify({'error': 'Username and password required'}), 400
                
                # Authenticate user
                session_id = self.auth_manager.authenticate(
                    username, password,
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
                
                # Log successful login
                self.audit_logger.log_event(
                    level=AuditLevel.INFO,
                    user_id=username,
                    action='auth:login',
                    resource_type='auth',
                    resource_id='login',
                    details={'ip_address': request.remote_addr},
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent'),
                    session_id=session_id
                )
                
                return jsonify({
                    'message': 'Login successful',
                    'session_id': session_id,
                    'expires_at': (datetime.utcnow() + timedelta(hours=8)).isoformat()
                })
                
            except ValueError as e:
                return jsonify({'error': str(e)}), 401
            except Exception as e:
                logger.error(f"Login error: {e}")
                return jsonify({'error': 'Authentication failed'}), 500
        
        @self.app.route('/api/auth/logout', methods=['POST'])
        def logout():
            """User logout endpoint"""
            try:
                session_id = request.headers.get('X-Session-ID')
                if not session_id:
                    return jsonify({'error': 'Session ID required'}), 400
                
                # Get user from session
                user = self.auth_manager.validate_session(session_id)
                if not user:
                    return jsonify({'error': 'Invalid session'}), 401
                
                # Logout user
                self.auth_manager.logout(session_id)
                
                # Log logout
                self.audit_logger.log_event(
                    level=AuditLevel.INFO,
                    user_id=user.username,
                    action='auth:logout',
                    resource_type='auth',
                    resource_id='logout',
                    details={},
                    session_id=session_id
                )
                
                return jsonify({'message': 'Logout successful'})
                
            except Exception as e:
                logger.error(f"Logout error: {e}")
                return jsonify({'error': 'Logout failed'}), 500
        
        # Wallet management endpoints
        @self.app.route('/api/wallets', methods=['POST'])
        @self.limiter.limit("100 per hour")
        def create_wallet():
            """Create new wallet endpoint"""
            try:
                # Authenticate user
                user = self._authenticate_request()
                if not user:
                    return jsonify({'error': 'Authentication required'}), 401
                
                # Check permissions
                if not user.has_permission(Permission.WALLET_WRITE):
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                data = request.get_json()
                count = data.get('count', 1)
                strength = data.get('strength', 128)
                tags = data.get('tags', [])
                encrypt = data.get('encrypt', True)
                password = data.get('password') if encrypt else None
                
                # Validate input
                if count < 1 or count > 1000:
                    return jsonify({'error': 'Count must be between 1 and 1000'}), 400
                
                if strength not in [128, 160, 192, 224, 256]:
                    return jsonify({'error': 'Invalid strength value'}), 400
                
                # Generate wallets
                wallets = []
                for i in range(count):
                    wallet = self.wallet_generator.generate_wallet(strength=strength)
                    
                    # Encrypt if requested
                    if encrypt and password:
                        encrypted_data = self.encryption_manager.encrypt_wallet(
                            wallet, password
                        )
                        wallet_data = {
                            'address': wallet.address,
                            'encrypted_data': encrypted_data,
                            'is_encrypted': True,
                            'encryption_algorithm': 'AES-256'
                        }
                    else:
                        wallet_data = {
                            'address': wallet.address,
                            'private_key': wallet.private_key,
                            'mnemonic': wallet.mnemonic,
                            'derivation_path': wallet.derivation_path,
                            'is_encrypted': False
                        }
                    
                    # Add metadata
                    wallet_data.update({
                        'created_by': user.username,
                        'created_at': datetime.utcnow().isoformat(),
                        'tags': tags,
                        'metadata': {
                            'api_request': True,
                            'request_id': g.request_id
                        }
                    })
                    
                    wallets.append(wallet_data)
                
                # Store in database
                for wallet_data in wallets:
                    self.wallet_repo.create_wallet(wallet_data)
                
                # Log wallet creation
                self.audit_logger.log_event(
                    level=AuditLevel.INFO,
                    user_id=user.username,
                    action='wallet:create',
                    resource_type='wallet',
                    resource_id=f'batch_{count}',
                    details={
                        'count': count,
                        'strength': strength,
                        'encrypted': encrypt,
                        'tags': tags
                    },
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent'),
                    session_id=request.headers.get('X-Session-ID')
                )
                
                return jsonify({
                    'message': f'Created {count} wallet(s)',
                    'wallets': wallets,
                    'request_id': g.request_id
                })
                
            except Exception as e:
                logger.error(f"Wallet creation error: {e}")
                return jsonify({'error': 'Wallet creation failed'}), 500
        
        @self.app.route('/api/wallets', methods=['GET'])
        def list_wallets():
            """List wallets endpoint"""
            try:
                # Authenticate user
                user = self._authenticate_request()
                if not user:
                    return jsonify({'error': 'Authentication required'}), 401
                
                # Check permissions
                if not user.has_permission(Permission.WALLET_READ):
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                # Get query parameters
                page = int(request.args.get('page', 1))
                per_page = min(int(request.args.get('per_page', 50)), 100)
                tags = request.args.get('tags', '').split(',') if request.args.get('tags') else []
                search = request.args.get('search', '')
                
                # Get wallets
                offset = (page - 1) * per_page
                
                if search:
                    wallets = self.wallet_repo.search_wallets(search, per_page, offset)
                elif tags and tags[0]:
                    wallets = self.wallet_repo.get_wallets_by_tag(tags[0], per_page, offset)
                else:
                    wallets = self.wallet_repo.get_wallets_by_user(user.username, per_page, offset)
                
                # Convert to dict format
                wallet_list = []
                for wallet in wallets:
                    wallet_dict = asdict(wallet)
                    # Remove sensitive data for non-admin users
                    if not user.has_permission(Permission.ADMIN):
                        wallet_dict.pop('private_key', None)
                        wallet_dict.pop('mnemonic', None)
                    wallet_list.append(wallet_dict)
                
                # Log wallet listing
                self.audit_logger.log_event(
                    level=AuditLevel.INFO,
                    user_id=user.username,
                    action='wallet:list',
                    resource_type='wallet',
                    resource_id='list',
                    details={
                        'page': page,
                        'per_page': per_page,
                        'tags': tags,
                        'search': search,
                        'results_count': len(wallet_list)
                    },
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent'),
                    session_id=request.headers.get('X-Session-ID')
                )
                
                return jsonify({
                    'wallets': wallet_list,
                    'pagination': {
                        'page': page,
                        'per_page': per_page,
                        'total': len(wallet_list),
                        'has_next': len(wallet_list) == per_page
                    },
                    'request_id': g.request_id
                })
                
            except Exception as e:
                logger.error(f"Wallet listing error: {e}")
                return jsonify({'error': 'Failed to list wallets'}), 500
        
        @self.app.route('/api/wallets/<address>', methods=['GET'])
        def get_wallet(address):
            """Get specific wallet endpoint"""
            try:
                # Authenticate user
                user = self._authenticate_request()
                if not user:
                    return jsonify({'error': 'Authentication required'}), 401
                
                # Check permissions
                if not user.has_permission(Permission.WALLET_READ):
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                # Get wallet
                wallet = self.wallet_repo.get_wallet_by_address(address)
                if not wallet:
                    return jsonify({'error': 'Wallet not found'}), 404
                
                # Check if user owns the wallet or has admin rights
                if wallet.created_by != user.username and not user.has_permission(Permission.ADMIN):
                    return jsonify({'error': 'Access denied'}), 403
                
                # Convert to dict
                wallet_dict = asdict(wallet)
                
                # Remove sensitive data for non-admin users
                if not user.has_permission(Permission.ADMIN):
                    wallet_dict.pop('private_key', None)
                    wallet_dict.pop('mnemonic', None)
                
                # Log wallet access
                self.audit_logger.log_event(
                    level=AuditLevel.INFO,
                    user_id=user.username,
                    action='wallet:read',
                    resource_type='wallet',
                    resource_id=address,
                    details={},
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent'),
                    session_id=request.headers.get('X-Session-ID')
                )
                
                return jsonify({
                    'wallet': wallet_dict,
                    'request_id': g.request_id
                })
                
            except Exception as e:
                logger.error(f"Wallet retrieval error: {e}")
                return jsonify({'error': 'Failed to retrieve wallet'}), 500
        
        # Analytics endpoints
        @self.app.route('/api/analytics/metrics', methods=['GET'])
        def get_analytics():
            """Get analytics metrics endpoint"""
            try:
                # Authenticate user
                user = self._authenticate_request()
                if not user:
                    return jsonify({'error': 'Authentication required'}), 401
                
                # Check permissions
                if not user.has_permission(Permission.ANALYTICS_READ):
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                # Get metrics
                username = None if user.has_permission(Permission.ADMIN) else user.username
                metrics = self.analytics_engine.generate_comprehensive_metrics(username)
                
                # Log analytics access
                self.audit_logger.log_event(
                    level=AuditLevel.INFO,
                    user_id=user.username,
                    action='analytics:read',
                    resource_type='analytics',
                    resource_id='metrics',
                    details={'scope': 'user' if username else 'system'},
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent'),
                    session_id=request.headers.get('X-Session-ID')
                )
                
                return jsonify({
                    'metrics': asdict(metrics),
                    'request_id': g.request_id
                })
                
            except Exception as e:
                logger.error(f"Analytics error: {e}")
                return jsonify({'error': 'Failed to retrieve analytics'}), 500
        
        # User management endpoints (admin only)
        @self.app.route('/api/users', methods=['GET'])
        def list_users():
            """List users endpoint (admin only)"""
            try:
                # Authenticate user
                user = self._authenticate_request()
                if not user:
                    return jsonify({'error': 'Authentication required'}), 401
                
                # Check permissions
                if not user.has_permission(Permission.USER_READ):
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                # Get users
                users = self.auth_manager.list_users()
                
                # Log user listing
                self.audit_logger.log_event(
                    level=AuditLevel.INFO,
                    user_id=user.username,
                    action='user:list',
                    resource_type='user',
                    resource_id='list',
                    details={'results_count': len(users)},
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent'),
                    session_id=request.headers.get('X-Session-ID')
                )
                
                return jsonify({
                    'users': users,
                    'request_id': g.request_id
                })
                
            except Exception as e:
                logger.error(f"User listing error: {e}")
                return jsonify({'error': 'Failed to list users'}), 500
        
        @self.app.route('/api/users', methods=['POST'])
        def create_user():
            """Create user endpoint (admin only)"""
            try:
                # Authenticate user
                user = self._authenticate_request()
                if not user:
                    return jsonify({'error': 'Authentication required'}), 401
                
                # Check permissions
                if not user.has_permission(Permission.USER_WRITE):
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                data = request.get_json()
                username = data.get('username')
                email = data.get('email')
                password = data.get('password')
                role = data.get('role', 'user')
                
                if not all([username, email, password]):
                    return jsonify({'error': 'Username, email, and password required'}), 400
                
                # Create user
                new_user = self.auth_manager.create_user(username, email, password, role)
                
                # Log user creation
                self.audit_logger.log_event(
                    level=AuditLevel.INFO,
                    user_id=user.username,
                    action='user:create',
                    resource_type='user',
                    resource_id=username,
                    details={'role': role, 'email': email},
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent'),
                    session_id=request.headers.get('X-Session-ID')
                )
                
                return jsonify({
                    'message': 'User created successfully',
                    'user': new_user.to_dict(),
                    'request_id': g.request_id
                })
                
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
            except Exception as e:
                logger.error(f"User creation error: {e}")
                return jsonify({'error': 'Failed to create user'}), 500
    
    def _authenticate_request(self) -> Optional[Any]:
        """Authenticate API request"""
        session_id = request.headers.get('X-Session-ID')
        if not session_id:
            return None
        
        return self.auth_manager.validate_session(session_id)
    
    def run(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False) -> None:
        """Run the API server"""
        logger.info(f"Starting MetaWalletGen API server on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)
    
    def get_app(self) -> Flask:
        """Get Flask application instance"""
        return self.app
