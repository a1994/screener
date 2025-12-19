"""Repository for ticker database operations."""

import sqlite3
import logging
import threading
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime

from .db_manager import get_db_connection

logger = logging.getLogger(__name__)


class TickerRepository:
    """Repository for ticker CRUD operations."""
    
    def add_ticker(self, symbol: str, user_id: int = 1) -> Optional[int]:
        """
        Insert single ticker or reactivate if it exists but is inactive for the user.
        
        Args:
            symbol: Ticker symbol (normalized)
            user_id: User ID who owns this ticker
            
        Returns:
            ticker_id of inserted/reactivated record, or None if ticker already active for this user
        """
        with get_db_connection() as conn:
            # Check if ticker exists for this user (active or inactive)
            row = conn.execute(
                "SELECT id, is_active FROM tickers WHERE symbol = ? AND user_id = ?",
                (symbol, user_id)
            ).fetchone()
            
            if row:
                ticker_id, is_active = row['id'], row['is_active']
                if is_active == 1:
                    # Already active for this user
                    logger.debug(f"Ticker {symbol} already exists and is active for user {user_id}")
                    return None
                else:
                    # Reactivate inactive ticker for this user
                    conn.execute(
                        "UPDATE tickers SET is_active = 1, added_date = ? WHERE id = ?",
                        (datetime.now().isoformat(), ticker_id)
                    )
                    logger.info(f"Reactivated ticker {symbol} for user {user_id} (ID: {ticker_id})")
                    return ticker_id
            else:
                # Insert new ticker for this user
                cursor = conn.execute(
                    "INSERT INTO tickers (symbol, user_id) VALUES (?, ?)",
                    (symbol, user_id)
                )
                ticker_id = cursor.lastrowid
                logger.info(f"Added new ticker {symbol} for user {user_id} (ID: {ticker_id})")
                return ticker_id
    
    def bulk_add(self, symbols: List[str], user_id: int = 1, generate_alerts: bool = True) -> Dict[str, Any]:
        """
        Insert multiple tickers for a specific user.
        
        Args:
            symbols: List of ticker symbols (normalized)
            user_id: User ID who owns these tickers
            generate_alerts: If True, trigger background alert generation for new tickers
            
        Returns:
            Dictionary with keys:
            - 'added': Number of successfully added symbols
            - 'failed': Number of failed insertions
            - 'errors': List of error messages
        """
        added = 0
        failed = 0
        errors = []
        new_tickers = []  # Track newly added tickers for alert generation
        
        with get_db_connection() as conn:
            for symbol in symbols:
                try:
                    # Check if ticker exists for this user (active or inactive)
                    row = conn.execute(
                        "SELECT id, is_active FROM tickers WHERE symbol = ? AND user_id = ?",
                        (symbol, user_id)
                    ).fetchone()
                    
                    if row:
                        ticker_id, is_active = row['id'], row['is_active']
                        if is_active == 1:
                            # Already active for this user, skip
                            failed += 1
                            logger.debug(f"Ticker {symbol} already exists and is active for user {user_id}")
                        else:
                            # Reactivate inactive ticker
                            conn.execute(
                                "UPDATE tickers SET is_active = 1, added_date = ? WHERE id = ?",
                                (datetime.now().isoformat(), ticker_id)
                            )
                            added += 1
                            new_tickers.append({
                                'id': ticker_id,
                                'symbol': symbol
                            })
                            logger.info(f"Reactivated ticker {symbol} for user {user_id} (ID: {ticker_id})")
                    else:
                        # Insert new ticker for this user
                        cursor = conn.execute(
                            "INSERT INTO tickers (symbol, user_id) VALUES (?, ?)",
                            (symbol, user_id)
                        )
                        added += 1
                        new_tickers.append({
                            'id': cursor.lastrowid,
                            'symbol': symbol
                        })
                        logger.info(f"Added new ticker {symbol} for user {user_id} (ID: {cursor.lastrowid})")
                except Exception as e:
                    failed += 1
                    error_msg = f"{symbol}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(f"Error inserting ticker {symbol}: {e}")
        
        # Trigger background alert generation for new tickers
        if generate_alerts and new_tickers:
            self._generate_alerts_async(new_tickers)
        
        return {'added': added, 'failed': failed, 'errors': errors}
    
    def _generate_alerts_async(self, tickers: List[Dict]) -> None:
        """
        Generate alerts for tickers in background thread.
        
        Args:
            tickers: List of ticker dictionaries with 'id' and 'symbol' keys
        """
        def generate_alerts():
            """Background task to generate alerts."""
            try:
                # Import here to avoid circular dependency
                from config.settings import DATABASE_PATH
                from alerts.generator import AlertGenerator
                from database.alert_repository import AlertRepository
                
                generator = AlertGenerator()
                alert_repo = AlertRepository(DATABASE_PATH)
                
                for ticker in tickers:
                    try:
                        # Generate alerts
                        result = generator.generate_for_ticker(
                            ticker['id'],
                            ticker['symbol']
                        )
                        
                        # Update database if successful
                        if result['success']:
                            alert_repo.update_for_ticker(
                                ticker['id'],
                                ticker['symbol'],
                                result['alerts']
                            )
                        else:
                            logger.warning(
                                f"Failed to generate alerts for {ticker['symbol']}: {result['error']}"
                            )
                    except Exception as e:
                        logger.error(
                            f"Error generating alerts for {ticker['symbol']}: {e}"
                        )
                
                logger.info(f"Background alert generation completed for {len(tickers)} ticker(s)")
                
            except Exception as e:
                logger.error(f"Error in background alert generation: {e}")
        
        # Start background thread
        thread = threading.Thread(target=generate_alerts, daemon=True)
        thread.start()
    
    def get_all(self, user_id: int = 1, page: int = 1, page_size: int = 50, 
                sort_by: str = 'symbol', sort_dir: str = 'ASC',
                search_query: Optional[str] = None, theme_id: Optional[int] = None) -> Tuple[List[Dict], int]:
        """
        Get paginated tickers with sorting for a specific user.
        
        Args:
            user_id: User ID to filter tickers by
            page: Page number (1-indexed)
            page_size: Number of records per page
            sort_by: Column to sort by ('symbol' or 'added_date')
            sort_dir: Sort direction ('ASC' or 'DESC')
            search_query: Optional symbol search filter
            theme_id: Optional theme ID to filter tickers by theme
            
        Returns:
            Tuple of (rows, total_count)
        """
        offset = (page - 1) * page_size
        
        # Validate sort parameters
        if sort_by not in ['symbol', 'added_date']:
            sort_by = 'symbol'
        if sort_dir not in ['ASC', 'DESC']:
            sort_dir = 'ASC'
        
        with get_db_connection() as conn:
            # Build base query
            base_query = "SELECT t.id, t.symbol, t.added_date, t.last_updated FROM tickers t"
            count_base = "SELECT COUNT(*) FROM tickers t"
            
            # Add theme join if needed
            if theme_id is not None:
                base_query += " INNER JOIN ticker_themes tt ON t.id = tt.ticker_id"
                count_base += " INNER JOIN ticker_themes tt ON t.id = tt.ticker_id"
            
            # Build where clause
            where_clause = "WHERE t.is_active = 1 AND t.user_id = ?"
            params = [user_id]
            
            if theme_id is not None:
                where_clause += " AND tt.theme_id = ?"
                params.append(theme_id)
            
            if search_query:
                where_clause += " AND t.symbol LIKE ?"
                params.append(f"%{search_query}%")
            
            # Get total count
            count_query = f"{count_base} {where_clause}"
            total_count = conn.execute(count_query, params).fetchone()[0]
            
            # Get paginated results
            query = f"{base_query} {where_clause} ORDER BY {sort_by} {sort_dir} LIMIT ? OFFSET ?"
            params.extend([page_size, offset])
            
            rows = conn.execute(query, params).fetchall()
            
            # Convert to list of dicts
            result = [
                {
                    'id': row['id'],
                    'symbol': row['symbol'],
                    'added_date': row['added_date'],
                    'last_updated': row['last_updated']
                }
                for row in rows
            ]
            
            return result, total_count
    
    def search(self, query: str, user_id: int = 1, page: int = 1, page_size: int = 50) -> Tuple[List[Dict], int]:
        """
        Search tickers by symbol (case-insensitive) for a specific user.
        
        Args:
            query: Search query
            user_id: User ID to filter tickers by
            page: Page number
            page_size: Records per page
            
        Returns:
            Tuple of (rows, total_count)
        """
        return self.get_all(page, page_size, search_query=query)
    
    def delete(self, ticker_id: int) -> bool:
        """
        Soft delete ticker (set is_active=0).
        
        Args:
            ticker_id: ID of ticker to delete
            
        Returns:
            True if deleted, False if not found
        """
        with get_db_connection() as conn:
            cursor = conn.execute(
                "UPDATE tickers SET is_active = 0 WHERE id = ?",
                (ticker_id,)
            )
            return cursor.rowcount > 0
    
    def bulk_delete(self, ticker_ids: List[int]) -> int:
        """
        Soft delete multiple tickers.
        
        Args:
            ticker_ids: List of ticker IDs to delete
            
        Returns:
            Count of deleted tickers
        """
        if not ticker_ids:
            return 0
        
        with get_db_connection() as conn:
            placeholders = ','.join('?' * len(ticker_ids))
            query = f"UPDATE tickers SET is_active = 0 WHERE id IN ({placeholders})"
            cursor = conn.execute(query, ticker_ids)
            return cursor.rowcount
    
    def get_by_symbol(self, symbol: str, user_id: int = 1) -> Optional[Dict]:
        """
        Get ticker by symbol for a specific user.
        
        Args:
            symbol: Ticker symbol
            user_id: User ID to filter by
            
        Returns:
            Ticker dict or None if not found for this user
        """
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT id, symbol, added_date, last_updated FROM tickers WHERE symbol = ? AND user_id = ? AND is_active = 1",
                (symbol, user_id)
            ).fetchone()
            
            if row:
                return {
                    'id': row['id'],
                    'symbol': row['symbol'],
                    'added_date': row['added_date'],
                    'last_updated': row['last_updated']
                }
            return None
    
    def get_active_tickers(self, user_id: int = 1) -> List[str]:
        """
        Get list of all active ticker symbols for a specific user.
        
        Args:
            user_id: User ID to filter by
        
        Returns:
            List of ticker symbols for this user
        """
        with get_db_connection() as conn:
            rows = conn.execute(
                "SELECT symbol FROM tickers WHERE is_active = 1 AND user_id = ? ORDER BY symbol ASC",
                (user_id,)
            ).fetchall()
            return [row['symbol'] for row in rows]
    
    def update_last_updated(self, ticker_id: int):
        """
        Update last_updated timestamp for a ticker.
        
        Args:
            ticker_id: ID of ticker to update
        """
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE tickers SET last_updated = ? WHERE id = ?",
                (datetime.now().isoformat(), ticker_id)
            )
