"""
Enterprise Database Management System

Provides database integration for wallet management, user data,
and enterprise features with support for multiple database backends.
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass, asdict
import threading
import queue
import time

logger = logging.getLogger(__name__)

@dataclass
class WalletRecord:
    """Wallet database record"""
    id: Optional[int]
    address: str
    private_key: str
    mnemonic: str
    derivation_path: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    tags: List[str]
    metadata: Dict[str, Any]
    is_encrypted: bool
    encryption_algorithm: Optional[str]
    last_accessed: Optional[datetime]
    access_count: int

class DatabaseManager:
    """Database connection and management"""
    
    def __init__(self, db_path: str = "enterprise.db", max_connections: int = 10):
        self.db_path = db_path
        self.max_connections = max_connections
        self.connection_pool = queue.Queue(maxsize=max_connections)
        self.lock = threading.Lock()
        
        # Initialize connection pool
        for _ in range(max_connections):
            conn = self._create_connection()
            self.connection_pool.put(conn)
        
        self._init_database()
    
    def _create_connection(self) -> sqlite3.Connection:
        """Create new database connection"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_connection(self) -> sqlite3.Connection:
        """Get connection from pool"""
        try:
            conn = self.connection_pool.get(timeout=5)
            return conn
        except queue.Empty:
            # Create new connection if pool is empty
            logger.warning("Connection pool exhausted, creating new connection")
            return self._create_connection()
    
    def return_connection(self, conn: sqlite3.Connection) -> None:
        """Return connection to pool"""
        try:
            if not self.connection_pool.full():
                self.connection_pool.put(conn)
            else:
                conn.close()
        except Exception as e:
            logger.error(f"Error returning connection to pool: {e}")
            conn.close()
    
    def _init_database(self) -> None:
        """Initialize database schema"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Create wallets table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS wallets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    address TEXT UNIQUE NOT NULL,
                    private_key TEXT NOT NULL,
                    mnemonic TEXT NOT NULL,
                    derivation_path TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    is_encrypted BOOLEAN DEFAULT 0,
                    encryption_algorithm TEXT,
                    last_accessed TEXT,
                    access_count INTEGER DEFAULT 0
                )
            ''')
            
            # Create wallet_access_log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS wallet_access_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    wallet_address TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    details TEXT
                )
            ''')
            
            # Create wallet_tags table for efficient tag searching
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS wallet_tags (
                    wallet_address TEXT NOT NULL,
                    tag TEXT NOT NULL,
                    PRIMARY KEY (wallet_address, tag)
                )
            ''')
            
            # Create indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_wallets_created_by ON wallets(created_by)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_wallets_created_at ON wallets(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_wallets_tags ON wallet_tags(tag)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_access_log_wallet ON wallet_access_log(wallet_address)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_access_log_user ON wallet_access_log(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_access_log_timestamp ON wallet_access_log(timestamp)')
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
        finally:
            self.return_connection(conn)
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute SELECT query and return results"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
        finally:
            self.return_connection(conn)
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute UPDATE/INSERT/DELETE query and return affected rows"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            logger.error(f"Update execution failed: {e}")
            conn.rollback()
            raise
        finally:
            self.return_connection(conn)
    
    def execute_transaction(self, queries: List[tuple]) -> bool:
        """Execute multiple queries in a transaction"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            for query, params in queries:
                cursor.execute(query, params)
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            conn.rollback()
            return False
        finally:
            self.return_connection(conn)

class WalletRepository:
    """Wallet data repository with CRUD operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def create_wallet(self, wallet: WalletRecord) -> int:
        """Create new wallet record"""
        # Insert main wallet record
        wallet_query = '''
            INSERT INTO wallets (
                address, private_key, mnemonic, derivation_path, created_by,
                created_at, updated_at, tags, metadata, is_encrypted,
                encryption_algorithm, last_accessed, access_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        wallet_params = (
            wallet.address, wallet.private_key, wallet.mnemonic,
            wallet.derivation_path, wallet.created_by, wallet.created_at.isoformat(),
            wallet.updated_at.isoformat(), json.dumps(wallet.tags),
            json.dumps(wallet.metadata), wallet.is_encrypted,
            wallet.encryption_algorithm,
            wallet.last_accessed.isoformat() if wallet.last_accessed else None,
            wallet.access_count
        )
        
        # Insert tags
        tag_queries = []
        for tag in wallet.tags:
            tag_queries.append((
                'INSERT INTO wallet_tags (wallet_address, tag) VALUES (?, ?)',
                (wallet.address, tag)
            ))
        
        # Execute transaction
        queries = [(wallet_query, wallet_params)] + tag_queries
        if self.db_manager.execute_transaction(queries):
            # Get the inserted wallet ID
            result = self.db_manager.execute_query(
                'SELECT id FROM wallets WHERE address = ?', (wallet.address,)
            )
            return result[0]['id'] if result else None
        else:
            raise Exception("Failed to create wallet record")
    
    def get_wallet_by_address(self, address: str) -> Optional[WalletRecord]:
        """Get wallet by address"""
        query = 'SELECT * FROM wallets WHERE address = ?'
        rows = self.db_manager.execute_query(query, (address,))
        
        if not rows:
            return None
        
        row = rows[0]
        return self._row_to_wallet_record(row)
    
    def get_wallets_by_user(self, username: str, limit: int = 100, offset: int = 0) -> List[WalletRecord]:
        """Get wallets created by specific user"""
        query = '''
            SELECT * FROM wallets 
            WHERE created_by = ? 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        '''
        rows = self.db_manager.execute_query(query, (username, limit, offset))
        return [self._row_to_wallet_record(row) for row in rows]
    
    def get_wallets_by_tag(self, tag: str, limit: int = 100, offset: int = 0) -> List[WalletRecord]:
        """Get wallets by tag"""
        query = '''
            SELECT w.* FROM wallets w
            INNER JOIN wallet_tags wt ON w.address = wt.wallet_address
            WHERE wt.tag = ?
            ORDER BY w.created_at DESC
            LIMIT ? OFFSET ?
        '''
        rows = self.db_manager.execute_query(query, (tag, limit, offset))
        return [self._row_to_wallet_record(row) for row in rows]
    
    def search_wallets(self, search_term: str, limit: int = 100, offset: int = 0) -> List[WalletRecord]:
        """Search wallets by address, tags, or metadata"""
        query = '''
            SELECT DISTINCT w.* FROM wallets w
            LEFT JOIN wallet_tags wt ON w.address = wt.wallet_address
            WHERE w.address LIKE ? 
               OR wt.tag LIKE ? 
               OR w.metadata LIKE ?
            ORDER BY w.created_at DESC
            LIMIT ? OFFSET ?
        '''
        search_pattern = f"%{search_term}%"
        rows = self.db_manager.execute_query(
            query, (search_pattern, search_pattern, search_pattern, limit, offset)
        )
        return [self._row_to_wallet_record(row) for row in rows]
    
    def update_wallet(self, address: str, updates: Dict[str, Any]) -> bool:
        """Update wallet record"""
        # Build dynamic update query
        set_clauses = []
        params = []
        
        for key, value in updates.items():
            if key in ['tags', 'metadata']:
                set_clauses.append(f"{key} = ?")
                params.append(json.dumps(value))
            elif key in ['created_at', 'updated_at', 'last_accessed']:
                set_clauses.append(f"{key} = ?")
                params.append(value.isoformat() if value else None)
            else:
                set_clauses.append(f"{key} = ?")
                params.append(value)
        
        if not set_clauses:
            return False
        
        # Add updated_at timestamp
        set_clauses.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        
        query = f"UPDATE wallets SET {', '.join(set_clauses)} WHERE address = ?"
        params.append(address)
        
        affected_rows = self.db_manager.execute_update(query, tuple(params))
        return affected_rows > 0
    
    def delete_wallet(self, address: str) -> bool:
        """Delete wallet record"""
        # Delete tags first
        self.db_manager.execute_update(
            'DELETE FROM wallet_tags WHERE wallet_address = ?', (address,)
        )
        
        # Delete access logs
        self.db_manager.execute_update(
            'DELETE FROM wallet_access_log WHERE wallet_address = ?', (address,)
        )
        
        # Delete main wallet record
        affected_rows = self.db_manager.execute_update(
            'DELETE FROM wallets WHERE address = ?', (address,)
        )
        
        return affected_rows > 0
    
    def log_wallet_access(self, wallet_address: str, user_id: str, action: str,
                         ip_address: str = None, user_agent: str = None,
                         details: Dict[str, Any] = None) -> None:
        """Log wallet access for audit purposes"""
        query = '''
            INSERT INTO wallet_access_log 
            (wallet_address, user_id, action, timestamp, ip_address, user_agent, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        
        params = (
            wallet_address, user_id, action, datetime.utcnow().isoformat(),
            ip_address, user_agent, json.dumps(details) if details else None
        )
        
        self.db_manager.execute_update(query, params)
        
        # Update wallet access count and last accessed
        self.update_wallet(wallet_address, {
            'last_accessed': datetime.utcnow(),
            'access_count': self._get_wallet_access_count(wallet_address) + 1
        })
    
    def _get_wallet_access_count(self, wallet_address: str) -> int:
        """Get current access count for wallet"""
        query = 'SELECT access_count FROM wallets WHERE address = ?'
        rows = self.db_manager.execute_query(query, (wallet_address,))
        return rows[0]['access_count'] if rows else 0
    
    def _row_to_wallet_record(self, row: Dict) -> WalletRecord:
        """Convert database row to WalletRecord"""
        return WalletRecord(
            id=row['id'],
            address=row['address'],
            private_key=row['private_key'],
            mnemonic=row['mnemonic'],
            derivation_path=row['derivation_path'],
            created_by=row['created_by'],
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at']),
            tags=json.loads(row['tags']),
            metadata=json.loads(row['metadata']),
            is_encrypted=bool(row['is_encrypted']),
            encryption_algorithm=row['encryption_algorithm'],
            last_accessed=datetime.fromisoformat(row['last_accessed']) if row['last_accessed'] else None,
            access_count=row['access_count']
        )
    
    def get_wallet_statistics(self, username: str = None) -> Dict[str, Any]:
        """Get wallet statistics"""
        if username:
            # User-specific stats
            total_wallets = self.db_manager.execute_query(
                'SELECT COUNT(*) as count FROM wallets WHERE created_by = ?', (username,)
            )[0]['count']
            
            encrypted_wallets = self.db_manager.execute_query(
                'SELECT COUNT(*) as count FROM wallets WHERE created_by = ? AND is_encrypted = 1', (username,)
            )[0]['count']
            
            recent_wallets = self.db_manager.execute_query(
                'SELECT COUNT(*) as count FROM wallets WHERE created_by = ? AND created_at >= ?', 
                (username, (datetime.utcnow() - timedelta(days=30)).isoformat())
            )[0]['count']
        else:
            # System-wide stats
            total_wallets = self.db_manager.execute_query(
                'SELECT COUNT(*) as count FROM wallets'
            )[0]['count']
            
            encrypted_wallets = self.db_manager.execute_query(
                'SELECT COUNT(*) as count FROM wallets WHERE is_encrypted = 1'
            )[0]['count']
            
            recent_wallets = self.db_manager.execute_query(
                'SELECT COUNT(*) as count FROM wallets WHERE created_at >= ?',
                ((datetime.utcnow() - timedelta(days=30)).isoformat(),)
            )[0]['count']
        
        return {
            'total_wallets': total_wallets,
            'encrypted_wallets': encrypted_wallets,
            'recent_wallets': recent_wallets,
            'encryption_rate': (encrypted_wallets / total_wallets * 100) if total_wallets > 0 else 0
        }
    
    def cleanup_old_access_logs(self, days: int = 90) -> int:
        """Clean up old access log entries"""
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        affected_rows = self.db_manager.execute_update(
            'DELETE FROM wallet_access_log WHERE timestamp < ?', (cutoff_date,)
        )
        return affected_rows
