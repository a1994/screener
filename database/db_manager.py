"""Database manager for SQLite database operations."""

import sqlite3
import logging
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and initialization."""
    
    def __init__(self, db_path: str):
        """
        Initialize DatabaseManager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_db_directory()
    
    def _ensure_db_directory(self):
        """Ensure database directory exists."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """
        Get database connection with context manager.
        
        Yields:
            sqlite3.Connection: Database connection
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")
            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode = WAL")
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def init_db(self):
        """Initialize database with schema."""
        with self.get_connection() as conn:
            # Create tickers table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tickers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT UNIQUE NOT NULL,
                    added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_updated DATETIME,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            # Create indexes for tickers
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tickers_symbol 
                ON tickers(symbol)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tickers_is_active 
                ON tickers(is_active)
            """)
            
            # Create price_cache table (for future use)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS price_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker_id INTEGER NOT NULL,
                    date DATE NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume INTEGER,
                    cached_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ticker_id) REFERENCES tickers(id) ON DELETE CASCADE,
                    UNIQUE(ticker_id, date)
                )
            """)
            
            # Create index for price_cache
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_price_cache_ticker_date 
                ON price_cache(ticker_id, date)
            """)
            
            # Create alerts table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker_id INTEGER NOT NULL,
                    ticker_symbol TEXT NOT NULL,
                    alert_type TEXT NOT NULL CHECK(alert_type IN ('LONG_OPEN', 'LONG_CLOSE', 'SHORT_OPEN', 'SHORT_CLOSE')),
                    signal_date DATE NOT NULL,
                    price REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ticker_id) REFERENCES tickers(id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes for alerts
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_alerts_ticker_id 
                ON alerts(ticker_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_alerts_signal_date 
                ON alerts(signal_date DESC)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_alerts_created_at 
                ON alerts(created_at DESC)
            """)
            
            logger.info("Database initialized successfully")


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def init_db(db_path: str = "data/screener.db"):
    """
    Initialize global database manager.
    
    Args:
        db_path: Path to SQLite database file
    """
    global _db_manager
    _db_manager = DatabaseManager(db_path)
    _db_manager.init_db()


def get_db_connection():
    """
    Get database connection from global manager.
    
    Returns:
        Context manager for database connection
        
    Raises:
        RuntimeError: If database not initialized
    """
    if _db_manager is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _db_manager.get_connection()
