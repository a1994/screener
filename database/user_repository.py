"""Repository for user database operations."""

import sqlite3
import logging
from typing import List, Dict, Optional
from datetime import datetime

from .db_manager import get_db_connection

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for user CRUD operations."""
    
    def add_user(self, username: str, display_name: str) -> Optional[int]:
        """
        Add a new user.
        
        Args:
            username: Unique username (used internally)
            display_name: Human-readable display name
            
        Returns:
            user_id of inserted record, or None if username already exists
        """
        with get_db_connection() as conn:
            try:
                # Check if username already exists
                existing = conn.execute(
                    "SELECT id FROM users WHERE username = ? AND is_active = 1",
                    (username,)
                ).fetchone()
                
                if existing:
                    logger.debug(f"Username {username} already exists")
                    return None
                
                # Insert new user
                cursor = conn.execute(
                    """INSERT INTO users (username, display_name, created_at) 
                       VALUES (?, ?, ?)""",
                    (username, display_name, datetime.now().isoformat())
                )
                user_id = cursor.lastrowid
                logger.info(f"Added new user: {display_name} (ID: {user_id})")
                return user_id
                
            except sqlite3.IntegrityError:
                logger.error(f"Username {username} already exists")
                return None
    
    def get_all_users(self) -> List[Dict]:
        """
        Get all active users.
        
        Returns:
            List of user dictionaries with id, username, display_name, created_at
        """
        with get_db_connection() as conn:
            cursor = conn.execute(
                """SELECT id, username, display_name, created_at 
                   FROM users 
                   WHERE is_active = 1 
                   ORDER BY display_name"""
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID to retrieve
            
        Returns:
            User dictionary or None if not found
        """
        with get_db_connection() as conn:
            row = conn.execute(
                """SELECT id, username, display_name, created_at 
                   FROM users 
                   WHERE id = ? AND is_active = 1""",
                (user_id,)
            ).fetchone()
            return dict(row) if row else None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """
        Get user by username.
        
        Args:
            username: Username to retrieve
            
        Returns:
            User dictionary or None if not found
        """
        with get_db_connection() as conn:
            row = conn.execute(
                """SELECT id, username, display_name, created_at 
                   FROM users 
                   WHERE username = ? AND is_active = 1""",
                (username,)
            ).fetchone()
            return dict(row) if row else None
    
    def update_user(self, user_id: int, display_name: str) -> bool:
        """
        Update user's display name.
        
        Args:
            user_id: User ID to update
            display_name: New display name
            
        Returns:
            True if updated successfully, False otherwise
        """
        with get_db_connection() as conn:
            cursor = conn.execute(
                "UPDATE users SET display_name = ? WHERE id = ? AND is_active = 1",
                (display_name, user_id)
            )
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Updated user {user_id} display name to {display_name}")
            return success
    
    def deactivate_user(self, user_id: int) -> bool:
        """
        Deactivate a user (soft delete).
        
        Args:
            user_id: User ID to deactivate
            
        Returns:
            True if deactivated successfully, False otherwise
        """
        if user_id == 1:
            logger.warning("Cannot deactivate default admin user")
            return False
            
        with get_db_connection() as conn:
            cursor = conn.execute(
                "UPDATE users SET is_active = 0 WHERE id = ?",
                (user_id,)
            )
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Deactivated user {user_id}")
            return success
    
    def get_user_stats(self, user_id: int) -> Dict:
        """
        Get statistics for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with user statistics
        """
        with get_db_connection() as conn:
            # Count active tickers
            ticker_count = conn.execute(
                "SELECT COUNT(*) FROM tickers WHERE user_id = ? AND is_active = 1",
                (user_id,)
            ).fetchone()[0]
            
            # Count alerts
            alert_count = conn.execute(
                """SELECT COUNT(*) FROM alerts a 
                   JOIN tickers t ON a.ticker_id = t.id 
                   WHERE t.user_id = ?""",
                (user_id,)
            ).fetchone()[0]
            
            return {
                'ticker_count': ticker_count,
                'alert_count': alert_count
            }
    
    def ensure_default_user(self) -> int:
        """
        Ensure default user exists and return its ID.
        
        Returns:
            Default user ID
        """
        with get_db_connection() as conn:
            # Check if default user exists
            row = conn.execute(
                "SELECT id FROM users WHERE id = 1 AND is_active = 1"
            ).fetchone()
            
            if row:
                return row[0]
            
            # Create default user
            conn.execute(
                """INSERT OR REPLACE INTO users (id, username, display_name) 
                   VALUES (1, 'admin', 'Default User')"""
            )
            logger.info("Created default user")
            return 1