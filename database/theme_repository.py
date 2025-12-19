"""Theme repository for managing themes and ticker-theme relationships."""

import sqlite3
import logging
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager

from database.db_manager import get_db_connection

logger = logging.getLogger(__name__)


class ThemeRepository:
    """Repository for theme operations and ticker-theme relationships."""
    
    def __init__(self):
        """Initialize the ThemeRepository."""
        pass
    
    @contextmanager
    def _get_connection(self):
        """Get database connection."""
        with get_db_connection() as conn:
            yield conn
    
    def create_theme(self, user_id: int, name: str, description: str = None) -> Optional[int]:
        """
        Create a new theme for a user.
        
        Args:
            user_id: User ID who owns the theme
            name: Theme name
            description: Optional theme description
            
        Returns:
            Theme ID if successful, None otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO themes (user_id, name, description)
                    VALUES (?, ?, ?)
                    """,
                    (user_id, name.strip(), description)
                )
                theme_id = cursor.lastrowid
                logger.info(f"Created theme '{name}' with ID {theme_id} for user {user_id}")
                return theme_id
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                logger.warning(f"Theme '{name}' already exists for user {user_id}")
                return None
            raise
        except Exception as e:
            logger.error(f"Error creating theme: {e}")
            return None
    
    def get_user_themes(self, user_id: int) -> List[Dict]:
        """
        Get all themes for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of theme dictionaries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, name, description, created_at, is_active
                    FROM themes
                    WHERE user_id = ? AND is_active = 1
                    ORDER BY name
                    """,
                    (user_id,)
                )
                
                themes = []
                for row in cursor.fetchall():
                    themes.append({
                        'id': row[0],
                        'name': row[1],
                        'description': row[2],
                        'created_at': row[3],
                        'is_active': row[4]
                    })
                
                return themes
        except Exception as e:
            logger.error(f"Error getting user themes: {e}")
            return []
    
    def get_theme_by_id(self, theme_id: int, user_id: int) -> Optional[Dict]:
        """
        Get a theme by ID for a specific user.
        
        Args:
            theme_id: Theme ID
            user_id: User ID (for security)
            
        Returns:
            Theme dictionary or None
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, user_id, name, description, created_at, is_active
                    FROM themes
                    WHERE id = ? AND user_id = ? AND is_active = 1
                    """,
                    (theme_id, user_id)
                )
                
                row = cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'user_id': row[1],
                        'name': row[2],
                        'description': row[3],
                        'created_at': row[4],
                        'is_active': row[5]
                    }
                return None
        except Exception as e:
            logger.error(f"Error getting theme by ID: {e}")
            return None
    
    def get_theme_by_name(self, user_id: int, name: str) -> Optional[Dict]:
        """
        Get a theme by name for a specific user.
        
        Args:
            user_id: User ID
            name: Theme name
            
        Returns:
            Theme dictionary or None
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, user_id, name, description, created_at, is_active
                    FROM themes
                    WHERE user_id = ? AND name = ? AND is_active = 1
                    """,
                    (user_id, name.strip())
                )
                
                row = cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'user_id': row[1],
                        'name': row[2],
                        'description': row[3],
                        'created_at': row[4],
                        'is_active': row[5]
                    }
                return None
        except Exception as e:
            logger.error(f"Error getting theme by name: {e}")
            return None
    
    def add_ticker_to_theme(self, ticker_id: int, theme_id: int) -> bool:
        """
        Add a ticker to a theme.
        
        Args:
            ticker_id: Ticker ID
            theme_id: Theme ID
            
        Returns:
            True if successful (including if already exists), False on error
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # First check if the relationship already exists
                cursor.execute(
                    "SELECT 1 FROM ticker_themes WHERE ticker_id = ? AND theme_id = ?",
                    (ticker_id, theme_id)
                )
                if cursor.fetchone():
                    # Already exists - this is not an error
                    return True
                
                # Insert new relationship
                cursor.execute(
                    "INSERT INTO ticker_themes (ticker_id, theme_id) VALUES (?, ?)",
                    (ticker_id, theme_id)
                )
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error adding ticker to theme: {e}")
            return False
    
    def is_ticker_in_theme(self, ticker_id: int, theme_id: int) -> bool:
        """
        Check if a ticker is already in a theme.
        
        Args:
            ticker_id: Ticker ID
            theme_id: Theme ID
            
        Returns:
            True if ticker is in theme, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT 1 FROM ticker_themes
                    WHERE ticker_id = ? AND theme_id = ?
                    """,
                    (ticker_id, theme_id)
                )
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking if ticker is in theme: {e}")
            return False
    
    def remove_ticker_from_theme(self, ticker_id: int, theme_id: int) -> bool:
        """
        Remove a ticker from a theme.
        
        Args:
            ticker_id: Ticker ID
            theme_id: Theme ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    DELETE FROM ticker_themes
                    WHERE ticker_id = ? AND theme_id = ?
                    """,
                    (ticker_id, theme_id)
                )
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error removing ticker from theme: {e}")
            return False
    
    def get_tickers_by_theme(self, theme_id: int, user_id: int) -> List[Dict]:
        """
        Get all tickers in a theme.
        
        Args:
            theme_id: Theme ID
            user_id: User ID (for security)
            
        Returns:
            List of ticker dictionaries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT t.id, t.symbol, t.added_date, t.last_updated, t.is_active,
                           th.name as theme_name
                    FROM tickers t
                    INNER JOIN ticker_themes tt ON t.id = tt.ticker_id
                    INNER JOIN themes th ON tt.theme_id = th.id
                    WHERE th.id = ? AND t.user_id = ? AND t.is_active = 1
                    ORDER BY t.symbol
                    """,
                    (theme_id, user_id)
                )
                
                tickers = []
                for row in cursor.fetchall():
                    tickers.append({
                        'id': row[0],
                        'symbol': row[1],
                        'added_date': row[2],
                        'last_updated': row[3],
                        'is_active': row[4],
                        'theme_name': row[5]
                    })
                
                return tickers
        except Exception as e:
            logger.error(f"Error getting tickers by theme: {e}")
            return []
    
    def get_themes_for_ticker(self, ticker_id: int, user_id: int) -> List[Dict]:
        """
        Get all themes for a ticker.
        
        Args:
            ticker_id: Ticker ID
            user_id: User ID (for security)
            
        Returns:
            List of theme dictionaries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT th.id, th.name, th.description, th.created_at
                    FROM themes th
                    INNER JOIN ticker_themes tt ON th.id = tt.theme_id
                    WHERE tt.ticker_id = ? AND th.user_id = ? AND th.is_active = 1
                    ORDER BY th.name
                    """,
                    (ticker_id, user_id)
                )
                
                themes = []
                for row in cursor.fetchall():
                    themes.append({
                        'id': row[0],
                        'name': row[1],
                        'description': row[2],
                        'created_at': row[3]
                    })
                
                return themes
        except Exception as e:
            logger.error(f"Error getting ticker themes: {e}")
            return []
    
    def delete_theme(self, theme_id: int, user_id: int) -> bool:
        """
        Delete a theme (soft delete - sets is_active to 0).
        
        Args:
            theme_id: Theme ID
            user_id: User ID (for security)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # First, remove all ticker-theme relationships
                cursor.execute(
                    """
                    DELETE FROM ticker_themes
                    WHERE theme_id = ?
                    """,
                    (theme_id,)
                )
                
                # Then soft delete the theme
                cursor.execute(
                    """
                    UPDATE themes
                    SET is_active = 0
                    WHERE id = ? AND user_id = ?
                    """,
                    (theme_id, user_id)
                )
                
                success = cursor.rowcount > 0
                if success:
                    logger.info(f"Deleted theme {theme_id} for user {user_id}")
                return success
        except Exception as e:
            logger.error(f"Error deleting theme: {e}")
            return False
    
    def get_theme_stats(self, user_id: int) -> Dict:
        """
        Get theme statistics for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with theme statistics
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get total themes count
                cursor.execute(
                    "SELECT COUNT(*) FROM themes WHERE user_id = ? AND is_active = 1",
                    (user_id,)
                )
                total_themes = cursor.fetchone()[0]
                
                # Get themes with ticker counts
                cursor.execute(
                    """
                    SELECT th.name, COUNT(tt.ticker_id) as ticker_count
                    FROM themes th
                    LEFT JOIN ticker_themes tt ON th.id = tt.theme_id
                    WHERE th.user_id = ? AND th.is_active = 1
                    GROUP BY th.id, th.name
                    ORDER BY ticker_count DESC, th.name
                    """,
                    (user_id,)
                )
                
                theme_details = []
                for row in cursor.fetchall():
                    theme_details.append({
                        'name': row[0],
                        'ticker_count': row[1]
                    })
                
                return {
                    'total_themes': total_themes,
                    'theme_details': theme_details
                }
        except Exception as e:
            logger.error(f"Error getting theme stats: {e}")
            return {'total_themes': 0, 'theme_details': []}
    
    def can_delete_theme(self, theme_id: int, user_id: int) -> bool:
        """
        Check if a theme can be safely deleted.
        
        A theme can be deleted if:
        1. It exists and belongs to the user
        2. All its tickers either have no themes or belong to other themes as well
        
        Args:
            theme_id: Theme ID to check
            user_id: User ID (for security)
            
        Returns:
            True if theme can be safely deleted, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if theme exists and belongs to user
                cursor.execute(
                    "SELECT id FROM themes WHERE id = ? AND user_id = ? AND is_active = 1",
                    (theme_id, user_id)
                )
                if not cursor.fetchone():
                    return False  # Theme doesn't exist or doesn't belong to user
                
                # Check if any tickers would be orphaned (only in this theme)
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM ticker_themes tt1
                    WHERE tt1.theme_id = ? 
                    AND NOT EXISTS (
                        SELECT 1 FROM ticker_themes tt2 
                        WHERE tt2.ticker_id = tt1.ticker_id 
                        AND tt2.theme_id != ?
                    )
                    """,
                    (theme_id, theme_id)
                )
                orphaned_count = cursor.fetchone()[0]
                
                # Theme can be deleted if no tickers would be orphaned
                return orphaned_count == 0
                
        except Exception as e:
            logger.error(f"Error checking if theme can be deleted: {e}")
            return False
    
    def get_ticker_themes(self, ticker_ids: List[int], user_id: int) -> Dict[int, List[str]]:
        """
        Get themes for multiple tickers efficiently.
        
        Args:
            ticker_ids: List of ticker IDs
            user_id: User ID (for security)
            
        Returns:
            Dictionary mapping ticker_id to list of theme names
        """
        if not ticker_ids:
            return {}
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Build placeholders for IN clause
                placeholders = ','.join('?' * len(ticker_ids))
                
                cursor.execute(
                    f"""
                    SELECT tt.ticker_id, th.name
                    FROM ticker_themes tt
                    INNER JOIN themes th ON tt.theme_id = th.id
                    WHERE tt.ticker_id IN ({placeholders}) 
                    AND th.user_id = ? AND th.is_active = 1
                    ORDER BY tt.ticker_id, th.name
                    """,
                    ticker_ids + [user_id]
                )
                
                result = {}
                for row in cursor.fetchall():
                    ticker_id = row[0]
                    theme_name = row[1]
                    
                    if ticker_id not in result:
                        result[ticker_id] = []
                    result[ticker_id].append(theme_name)
                
                # Ensure all ticker_ids are in result (even if they have no themes)
                for ticker_id in ticker_ids:
                    if ticker_id not in result:
                        result[ticker_id] = []
                
                return result
        except Exception as e:
            logger.error(f"Error getting ticker themes: {e}")
            return {ticker_id: [] for ticker_id in ticker_ids}
    
    def get_orphaned_tickers(self, user_id: int, search_query: str = None, sort_by: str = 'symbol', sort_dir: str = 'ASC') -> List[Dict]:
        """
        Get tickers that are not assigned to any theme (orphaned tickers).
        
        Args:
            user_id: User ID
            search_query: Optional search query to filter symbols
            sort_by: Column to sort by
            sort_dir: Sort direction (ASC or DESC)
            
        Returns:
            List of orphaned ticker dictionaries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Build the query
                query = """
                    SELECT t.id, t.symbol, t.added_date as created_at, t.last_updated, t.is_active
                    FROM tickers t
                    WHERE t.user_id = ? AND t.is_active = 1
                    AND NOT EXISTS (
                        SELECT 1 FROM ticker_themes tt 
                        INNER JOIN themes th ON tt.theme_id = th.id 
                        WHERE tt.ticker_id = t.id AND th.is_active = 1
                    )
                """
                
                params = [user_id]
                
                # Add search filter
                if search_query:
                    query += " AND t.symbol LIKE ?"
                    params.append(f"%{search_query}%")
                
                # Add sorting
                valid_sort_columns = ['symbol', 'created_at', 'last_updated']
                if sort_by in valid_sort_columns:
                    if sort_by == 'created_at':
                        sort_column = 't.added_date'
                    else:
                        sort_column = f't.{sort_by}'
                    
                    query += f" ORDER BY {sort_column} {sort_dir}"
                else:
                    query += " ORDER BY t.symbol ASC"
                
                cursor.execute(query, params)
                
                orphaned_tickers = []
                for row in cursor.fetchall():
                    orphaned_tickers.append({
                        'id': row[0],
                        'symbol': row[1],
                        'created_at': row[2],
                        'last_updated': row[3],
                        'is_active': row[4]
                    })
                
                return orphaned_tickers
        except Exception as e:
            logger.error(f"Error getting orphaned tickers: {e}")
            return []