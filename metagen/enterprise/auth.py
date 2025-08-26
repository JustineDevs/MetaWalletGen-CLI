"""
Enterprise Authentication and Authorization System

Provides multi-user authentication, role-based access control,
and enterprise security features for MetaWalletGen CLI.
"""

import hashlib
import secrets
import time
import jwt
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import bcrypt
import sqlite3
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

class Permission(Enum):
    """System permissions"""
    WALLET_READ = "wallet:read"
    WALLET_WRITE = "wallet:write"
    WALLET_DELETE = "wallet:delete"
    WALLET_EXPORT = "wallet:export"
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"
    ROLE_READ = "role:read"
    ROLE_WRITE = "role:write"
    ROLE_DELETE = "role:delete"
    SYSTEM_CONFIG = "system:config"
    AUDIT_READ = "audit:read"
    ANALYTICS_READ = "analytics:read"
    ADMIN = "admin"

class Role:
    """User role with permissions"""
    
    def __init__(self, name: str, description: str = "", permissions: Optional[Set[Permission]] = None):
        self.name = name
        self.description = description
        self.permissions = permissions or set()
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def add_permission(self, permission: Permission) -> None:
        """Add permission to role"""
        self.permissions.add(permission)
        self.updated_at = datetime.utcnow()
    
    def remove_permission(self, permission: Permission) -> None:
        """Remove permission from role"""
        self.permissions.discard(permission)
        self.updated_at = datetime.utcnow()
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if role has specific permission"""
        return permission in self.permissions
    
    def to_dict(self) -> Dict:
        """Convert role to dictionary"""
        return {
            'name': self.name,
            'description': self.description,
            'permissions': [p.value for p in self.permissions],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

@dataclass
class User:
    """User entity"""
    username: str
    email: str
    password_hash: str
    role: Role
    is_active: bool = True
    is_locked: bool = False
    failed_attempts: int = 0
    last_login: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def check_password(self, password: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission"""
        return self.role.has_permission(permission)
    
    def to_dict(self) -> Dict:
        """Convert user to dictionary (excluding sensitive data)"""
        return {
            'username': self.username,
            'email': self.email,
            'role': self.role.name,
            'is_active': self.is_active,
            'is_locked': self.is_locked,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class AuthManager:
    """Authentication and authorization manager"""
    
    def __init__(self, db_path: str = "enterprise.db"):
        self.db_path = db_path
        self.secret_key = self._load_or_generate_secret()
        self.session_timeout = timedelta(hours=8)
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=30)
        self.active_sessions: Dict[str, Dict] = {}
        
        self._init_database()
        self._create_default_roles()
    
    def _load_or_generate_secret(self) -> str:
        """Load existing secret key or generate new one"""
        secret_file = Path("auth_secret.key")
        if secret_file.exists():
            return secret_file.read_text().strip()
        else:
            secret = secrets.token_urlsafe(32)
            secret_file.write_text(secret)
            return secret
    
    def _init_database(self) -> None:
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role_name TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                is_locked BOOLEAN DEFAULT 0,
                failed_attempts INTEGER DEFAULT 0,
                last_login TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        # Create roles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                name TEXT PRIMARY KEY,
                description TEXT,
                permissions TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        # Create sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _create_default_roles(self) -> None:
        """Create default system roles"""
        default_roles = {
            'admin': Role('admin', 'System Administrator', {
                Permission.ADMIN, Permission.WALLET_READ, Permission.WALLET_WRITE,
                Permission.WALLET_DELETE, Permission.WALLET_EXPORT, Permission.USER_READ,
                Permission.USER_WRITE, Permission.USER_DELETE, Permission.ROLE_READ,
                Permission.ROLE_WRITE, Permission.ROLE_DELETE, Permission.SYSTEM_CONFIG,
                Permission.AUDIT_READ, Permission.ANALYTICS_READ
            }),
            'manager': Role('manager', 'Wallet Manager', {
                Permission.WALLET_READ, Permission.WALLET_WRITE, Permission.WALLET_EXPORT,
                Permission.USER_READ, Permission.AUDIT_READ, Permission.ANALYTICS_READ
            }),
            'user': Role('user', 'Standard User', {
                Permission.WALLET_READ, Permission.WALLET_WRITE
            }),
            'viewer': Role('viewer', 'Read-Only User', {
                Permission.WALLET_READ
            })
        }
        
        for role in default_roles.values():
            self._save_role(role)
    
    def _save_role(self, role: Role) -> None:
        """Save role to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO roles (name, description, permissions, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            role.name,
            role.description,
            json.dumps([p.value for p in role.permissions]),
            role.created_at.isoformat(),
            role.updated_at.isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def _load_role(self, role_name: str) -> Optional[Role]:
        """Load role from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM roles WHERE name = ?', (role_name,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            permissions = set(Permission(p) for p in json.loads(row[2]))
            role = Role(row[0], row[1], permissions)
            role.created_at = datetime.fromisoformat(row[3])
            role.updated_at = datetime.fromisoformat(row[4])
            return role
        
        return None
    
    def create_user(self, username: str, email: str, password: str, role_name: str) -> User:
        """Create new user"""
        if self._user_exists(username):
            raise ValueError(f"User '{username}' already exists")
        
        role = self._load_role(role_name)
        if not role:
            raise ValueError(f"Role '{role_name}' does not exist")
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        user = User(username, email, password_hash, role)
        self._save_user(user)
        
        logger.info(f"Created user: {username} with role: {role_name}")
        return user
    
    def _user_exists(self, username: str) -> bool:
        """Check if user exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE username = ?', (username,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists
    
    def _save_user(self, user: User) -> None:
        """Save user to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            (username, email, password_hash, role_name, is_active, is_locked, 
             failed_attempts, last_login, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user.username, user.email, user.password_hash, user.role.name,
            user.is_active, user.is_locked, user.failed_attempts,
            user.last_login.isoformat() if user.last_login else None,
            user.created_at.isoformat(), user.updated_at.isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def authenticate(self, username: str, password: str, ip_address: str = None, user_agent: str = None) -> str:
        """Authenticate user and return session token"""
        user = self._load_user(username)
        if not user:
            raise ValueError("Invalid username or password")
        
        if not user.is_active:
            raise ValueError("User account is deactivated")
        
        if user.is_locked:
            if datetime.utcnow() - user.updated_at < self.lockout_duration:
                raise ValueError("Account is temporarily locked due to failed attempts")
            else:
                # Unlock account after lockout duration
                user.is_locked = False
                user.failed_attempts = 0
        
        if not user.check_password(password):
            user.failed_attempts += 1
            if user.failed_attempts >= self.max_failed_attempts:
                user.is_locked = True
            user.updated_at = datetime.utcnow()
            self._save_user(user)
            
            if user.is_locked:
                raise ValueError("Account locked due to too many failed attempts")
            else:
                raise ValueError("Invalid username or password")
        
        # Reset failed attempts on successful login
        user.failed_attempts = 0
        user.last_login = datetime.utcnow()
        user.updated_at = datetime.utcnow()
        self._save_user(user)
        
        # Create session
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + self.session_timeout
        
        self.active_sessions[session_id] = {
            'username': username,
            'created_at': datetime.utcnow(),
            'expires_at': expires_at,
            'ip_address': ip_address,
            'user_agent': user_agent
        }
        
        # Save session to database
        self._save_session(session_id, username, expires_at, ip_address, user_agent)
        
        logger.info(f"User '{username}' authenticated successfully from {ip_address}")
        return session_id
    
    def _load_user(self, username: str) -> Optional[User]:
        """Load user from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            role = self._load_role(row[4])
            if role:
                user = User(
                    username=row[1],
                    email=row[2],
                    password_hash=row[3],
                    role=role,
                    is_active=bool(row[5]),
                    is_locked=bool(row[6]),
                    failed_attempts=row[7],
                    last_login=datetime.fromisoformat(row[8]) if row[8] else None,
                    created_at=datetime.fromisoformat(row[9]),
                    updated_at=datetime.fromisoformat(row[10])
                )
                return user
        
        return None
    
    def _save_session(self, session_id: str, username: str, expires_at: datetime, 
                     ip_address: str = None, user_agent: str = None) -> None:
        """Save session to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO sessions 
            (session_id, username, created_at, expires_at, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            session_id, username, datetime.utcnow().isoformat(),
            expires_at.isoformat(), ip_address, user_agent
        ))
        
        conn.commit()
        conn.close()
    
    def validate_session(self, session_id: str) -> Optional[User]:
        """Validate session and return user"""
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        if datetime.utcnow() > session['expires_at']:
            del self.active_sessions[session_id]
            return None
        
        return self._load_user(session['username'])
    
    def logout(self, session_id: str) -> None:
        """Logout user and invalidate session"""
        if session_id in self.active_sessions:
            username = self.active_sessions[session_id]['username']
            del self.active_sessions[session_id]
            self._remove_session(session_id)
            logger.info(f"User '{username}' logged out")
    
    def _remove_session(self, session_id: str) -> None:
        """Remove session from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
        conn.commit()
        conn.close()
    
    def get_user_permissions(self, username: str) -> Set[Permission]:
        """Get user permissions"""
        user = self._load_user(username)
        if user:
            return user.role.permissions
        return set()
    
    def list_users(self) -> List[Dict]:
        """List all users (admin only)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT username, email, role_name, is_active, is_locked, created_at FROM users')
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'username': row[0],
                'email': row[1],
                'role': row[2],
                'is_active': bool(row[3]),
                'is_locked': bool(row[4]),
                'created_at': row[5]
            }
            for row in rows
        ]
    
    def change_user_role(self, username: str, new_role: str) -> None:
        """Change user role (admin only)"""
        user = self._load_user(username)
        if not user:
            raise ValueError(f"User '{username}' not found")
        
        role = self._load_role(new_role)
        if not role:
            raise ValueError(f"Role '{new_role}' not found")
        
        user.role = role
        user.updated_at = datetime.utcnow()
        self._save_user(user)
        
        logger.info(f"Changed role for user '{username}' to '{new_role}'")
    
    def deactivate_user(self, username: str) -> None:
        """Deactivate user account (admin only)"""
        user = self._load_user(username)
        if not user:
            raise ValueError(f"User '{username}' not found")
        
        user.is_active = False
        user.updated_at = datetime.utcnow()
        self._save_user(user)
        
        logger.info(f"Deactivated user account: {username}")
    
    def cleanup_expired_sessions(self) -> None:
        """Remove expired sessions"""
        current_time = datetime.utcnow()
        expired_sessions = [
            sid for sid, session in self.active_sessions.items()
            if current_time > session['expires_at']
        ]
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
            self._remove_session(session_id)
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
