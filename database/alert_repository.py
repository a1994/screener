"""
Repository for managing alert data in the database.
Provides CRUD operations for alerts with pagination and sorting.
"""

import sqlite3
from typing import List, Dict, Optional
from datetime import datetime


class AlertRepository:
    """Repository for alert operations."""
    
    def __init__(self, db_path: str):
        """
        Initialize the AlertRepository.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
    
    def get_all(
        self, 
        page: int = 1, 
        page_size: int = 20, 
        sort_order: str = 'DESC',
        ticker_filter: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> List[Dict]:
        """
        Get all alerts with pagination, sorting, and optional filtering.
        
        Args:
            page: Page number (1-based)
            page_size: Number of alerts per page
            sort_order: Sort order for signal_date ('ASC' or 'DESC')
            ticker_filter: Optional ticker symbol filter (case-insensitive partial match)
            user_id: Optional user ID to filter alerts by associated tickers
            
        Returns:
            List of alert dictionaries
        """
        # Validate sort order
        if sort_order not in ['ASC', 'DESC']:
            sort_order = 'DESC'
        
        offset = (page - 1) * page_size
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Build query with optional filter
            query = """
                SELECT 
                    a.id,
                    a.ticker_id,
                    a.ticker_symbol,
                    a.alert_type,
                    a.signal_date,
                    a.price,
                    a.created_at
                FROM alerts a
                INNER JOIN tickers t ON a.ticker_id = t.id
                WHERE t.is_active = 1
            """
            
            params = []
            where_clauses = []
            
            if user_id is not None:
                where_clauses.append("t.user_id = ?")
                params.append(user_id)
            
            if ticker_filter:
                where_clauses.append("a.ticker_symbol LIKE ?")
                params.append(f"%{ticker_filter}%")
            
            if where_clauses:
                query += " AND " + " AND ".join(where_clauses)
            
            query += f" ORDER BY a.signal_date {sort_order}, a.id {sort_order} LIMIT ? OFFSET ?"
            params.extend([page_size, offset])
            
            cursor.execute(query, params)
            
            alerts = [dict(row) for row in cursor.fetchall()]
            return alerts
            
        finally:
            conn.close()
    
    def get_total_count(self, ticker_filter: Optional[str] = None, user_id: Optional[int] = None) -> int:
        """
        Get total count of alerts, optionally filtered.
        
        Args:
            ticker_filter: Optional ticker symbol filter (case-insensitive partial match)
            user_id: Optional user ID to filter alerts by associated tickers
            
        Returns:
            Total number of alerts matching the filter
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Build query with optional filters
            query = """
                SELECT COUNT(*) FROM alerts a
                INNER JOIN tickers t ON a.ticker_id = t.id
                WHERE t.is_active = 1
            """
            
            params = []
            where_clauses = []
            
            if user_id is not None:
                where_clauses.append("t.user_id = ?")
                params.append(user_id)
            
            if ticker_filter:
                where_clauses.append("a.ticker_symbol LIKE ?")
                params.append(f"%{ticker_filter}%")
            
            if where_clauses:
                query += " AND " + " AND ".join(where_clauses)
            
            cursor.execute(query, params)
            
            count = cursor.fetchone()[0]
            return count
            
        finally:
            conn.close()
    
    def get_by_ticker(self, ticker_id: int) -> List[Dict]:
        """
        Get alerts for a specific ticker.
        
        Args:
            ticker_id: ID of the ticker
            
        Returns:
            List of alert dictionaries for the ticker
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    a.id,
                    a.ticker_id,
                    a.ticker_symbol,
                    a.alert_type,
                    a.signal_date,
                    a.price,
                    a.created_at
                FROM alerts a
                INNER JOIN tickers t ON a.ticker_id = t.id
                WHERE a.ticker_id = ? AND t.is_active = 1
                ORDER BY a.signal_date DESC, a.id DESC
            """, (ticker_id,))
            
            alerts = [dict(row) for row in cursor.fetchall()]
            return alerts
            
        finally:
            conn.close()
    
    def update_for_ticker(self, ticker_id: int, ticker_symbol: str, alerts: List[Dict]) -> None:
        """
        Update alerts for a specific ticker.
        Deletes existing alerts and inserts new ones in a transaction.
        
        Args:
            ticker_id: ID of the ticker
            ticker_symbol: Symbol of the ticker
            alerts: List of alert dictionaries to insert
                    Each dict should have: alert_type, signal_date, price
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Start transaction
            cursor.execute("BEGIN TRANSACTION")
            
            # Delete existing alerts for this ticker
            cursor.execute("DELETE FROM alerts WHERE ticker_id = ?", (ticker_id,))
            
            # Insert new alerts
            for alert in alerts:
                cursor.execute("""
                    INSERT INTO alerts (
                        ticker_id,
                        ticker_symbol,
                        alert_type,
                        signal_date,
                        price,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    ticker_id,
                    ticker_symbol,
                    alert['alert_type'],
                    alert['signal_date'],
                    alert['price'],
                    datetime.now().isoformat()  # Local time instead of UTC
                ))
            
            # Commit transaction
            conn.commit()
            
        except Exception as e:
            # Rollback on error
            conn.rollback()
            raise e
            
        finally:
            conn.close()
    
    def delete_for_ticker(self, ticker_id: int) -> int:
        """
        Delete all alerts for a specific ticker.
        
        Args:
            ticker_id: ID of the ticker
            
        Returns:
            Number of alerts deleted
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM alerts WHERE ticker_id = ?", (ticker_id,))
            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count
            
        finally:
            conn.close()
    
    def delete_all(self) -> int:
        """
        Delete all alerts.
        
        Returns:
            Number of alerts deleted
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM alerts")
            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count
            
        finally:
            conn.close()
    
    def bulk_insert(self, alerts: List[Dict]) -> int:
        """
        Bulk insert alerts.
        
        Args:
            alerts: List of alert dictionaries to insert
                    Each dict should have: ticker_id, ticker_symbol, alert_type, signal_date, price
                    
        Returns:
            Number of alerts inserted
        """
        if not alerts:
            return 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("BEGIN TRANSACTION")
            
            for alert in alerts:
                cursor.execute("""
                    INSERT INTO alerts (
                        ticker_id,
                        ticker_symbol,
                        alert_type,
                        signal_date,
                        price
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    alert['ticker_id'],
                    alert['ticker_symbol'],
                    alert['alert_type'],
                    alert['signal_date'],
                    alert['price']
                ))
            
            conn.commit()
            return len(alerts)
            
        except Exception as e:
            conn.rollback()
            raise e
            
        finally:
            conn.close()
