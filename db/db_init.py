"""
SHASTRA Database Initialization Module
=
SQLite database management with automatic schema creation.
Handles all database operations for authentication and audit logging.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager
from core.app_paths import get_database_path, ensure_app_directories


# SQL Schema Definitions
SCHEMA_USERS = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('Admin', 'Operator')),
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    must_change_password INTEGER NOT NULL DEFAULT 0,
    last_login TEXT
);
"""

SCHEMA_AUDIT_LOG = """
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    action TEXT NOT NULL,
    details TEXT,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""

# Index for faster queries
SCHEMA_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);
"""


class DatabaseManager:
    """
    Manages SQLite database operations for SHASTRA.
    Thread-safe singleton pattern for database connections.
    """
    
    _instance: Optional['DatabaseManager'] = None
    
    def __new__(cls) -> 'DatabaseManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._db_path: Path = get_database_path()
        self._ensure_database()
    
    def _ensure_database(self) -> None:
        """Ensure database and schema exist."""
        ensure_app_directories()
        self._create_schema()
    
    def _create_schema(self) -> None:
        """Create database schema if not exists."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(SCHEMA_USERS)
            cursor.execute(SCHEMA_AUDIT_LOG)
            cursor.executescript(SCHEMA_INDEXES)
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        Ensures proper connection handling and cleanup.
        
        Yields:
            sqlite3.Connection: Database connection
        """
        conn = sqlite3.connect(
            str(self._db_path),
            timeout=30.0,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        finally:
            conn.close()
    
    def database_exists(self) -> bool:
        """Check if database file exists."""
        return self._db_path.exists()
    
    def has_users(self) -> bool:
        """Check if any users exist in the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            return count > 0
    
    #User Operations
    
    def create_user(
        self,
        username: str,
        password_hash: str,
        role: str,
        must_change_password: bool = False
    ) -> Optional[int]:
        """
        Create a new user in the database.
        
        Args:
            username: Unique username
            password_hash: Argon2 hashed password
            role: User role ('Admin' or 'Operator')
            must_change_password: Force password change on first login
            
        Returns:
            int: User ID if successful, None if failed
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO users (username, password_hash, role, is_active, created_at, must_change_password)
                    VALUES (?, ?, ?, 1, ?, ?)
                    """,
                    (username, password_hash, role, datetime.now().isoformat(), int(must_change_password))
                )
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get user by username.
        
        Args:
            username: Username to look up
            
        Returns:
            dict: User data or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID to look up
            
        Returns:
            dict: User data or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """
        Get all users from the database.
        
        Returns:
            list: List of user dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, role, is_active, created_at, last_login FROM users ORDER BY created_at"
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def update_user_password(self, user_id: int, password_hash: str) -> bool:
        """
        Update user's password hash.
        
        Args:
            user_id: User ID
            password_hash: New Argon2 hashed password
            
        Returns:
            bool: True if successful
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE users 
                SET password_hash = ?, must_change_password = 0 
                WHERE id = ?
                """,
                (password_hash, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def update_user_role(self, user_id: int, role: str) -> bool:
        """
        Update user's role.
        
        Args:
            user_id: User ID
            role: New role ('Admin' or 'Operator')
            
        Returns:
            bool: True if successful
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET role = ? WHERE id = ?",
                (role, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def update_user_status(self, user_id: int, is_active: bool) -> bool:
        """
        Enable or disable a user.
        
        Args:
            user_id: User ID
            is_active: New active status
            
        Returns:
            bool: True if successful
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET is_active = ? WHERE id = ?",
                (int(is_active), user_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def update_last_login(self, user_id: int) -> None:
        """Update user's last login timestamp."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (datetime.now().isoformat(), user_id)
            )
            conn.commit()
    
    def delete_user(self, user_id: int) -> bool:
        """
        Delete a user from the database.
        
        Args:
            user_id: User ID to delete
            
        Returns:
            bool: True if successful
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def count_admins(self) -> int:
        """Count the number of admin users."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'Admin' AND is_active = 1")
            return cursor.fetchone()[0]
    
    #Audit Log Operations
    
    def log_audit(
        self,
        action: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        details: Optional[str] = None
    ) -> None:
        """
        Write an entry to the audit log.
        
        Args:
            action: Action description (e.g., 'LOGIN_SUCCESS', 'USER_CREATED')
            user_id: Optional user ID performing the action
            username: Optional username for logging
            details: Optional additional details
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO audit_log (user_id, username, action, details, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, username, action, details, datetime.now().isoformat())
            )
            conn.commit()
    
    def get_audit_log(
        self,
        limit: int = 100,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get audit log entries.
        
        Args:
            limit: Maximum number of entries to return
            user_id: Optional filter by user ID
            
        Returns:
            list: List of audit log entries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute(
                    """
                    SELECT * FROM audit_log 
                    WHERE user_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                    """,
                    (user_id, limit)
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM audit_log 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                    """,
                    (limit,)
                )
            return [dict(row) for row in cursor.fetchall()]


# Global database instance accessor
def get_db() -> DatabaseManager:
    """Get the singleton DatabaseManager instance."""
    return DatabaseManager()
