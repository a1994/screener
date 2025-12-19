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
    
    def _migrate_database(self, conn):
        """Migrate existing database to support user system."""
        try:
            # Check if user_id column exists in tickers table
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(tickers)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'user_id' not in columns:
                logger.info("Migrating database to support multi-user system...")
                
                # Check if tickers table has existing data
                cursor.execute("SELECT COUNT(*) FROM tickers")
                existing_count = cursor.fetchone()[0]
                
                if existing_count > 0:
                    logger.info(f"Found {existing_count} existing tickers, migrating...")
                    
                    # Create backup of existing data
                    cursor.execute("""
                        CREATE TEMP TABLE tickers_backup AS 
                        SELECT * FROM tickers
                    """)
                    
                    # Drop the existing table
                    cursor.execute("DROP TABLE tickers")
                    
                    # Create new table with proper schema (will be created in init_db)
                    # For now, just add the user_id column with proper handling
                    cursor.execute("""
                        CREATE TABLE tickers (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            symbol TEXT NOT NULL,
                            user_id INTEGER NOT NULL DEFAULT 1,
                            added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                            last_updated DATETIME,
                            is_active BOOLEAN DEFAULT 1,
                            UNIQUE(symbol, user_id)
                        )
                    """)
                    
                    # Migrate data back, assigning all existing tickers to user_id = 1
                    cursor.execute("""
                        INSERT INTO tickers (id, symbol, added_date, last_updated, is_active, user_id)
                        SELECT id, symbol, added_date, last_updated, is_active, 1 
                        FROM tickers_backup
                    """)
                    
                    logger.info("Data migration completed successfully")
                else:
                    # No existing data, just add the column
                    conn.execute("ALTER TABLE tickers ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1")
                
                # Create indexes
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_tickers_user_id 
                    ON tickers(user_id)
                """)
                
                logger.info("Database migration completed successfully")
                
        except Exception as e:
            logger.error(f"Migration error: {e}")
            # Continue with initialization even if migration fails
    
    def init_db(self):
        """Initialize database with schema."""
        with self.get_connection() as conn:
            # Run migrations first
            self._migrate_database(conn)
            # Create users table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            # Create default admin user if no users exist
            conn.execute("""
                INSERT OR IGNORE INTO users (id, username, display_name) 
                VALUES (1, 'admin', 'Default User')
            """)
            
            # Create themes table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS themes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    UNIQUE(user_id, name)
                )
            """)
            
            # Create tickers table with user_id
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tickers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    user_id INTEGER NOT NULL DEFAULT 1,
                    added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_updated DATETIME,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    UNIQUE(symbol, user_id)
                )
            """)
            
            # Create indexes for users
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_username 
                ON users(username)
            """)
            
            # Create ticker_themes junction table (many-to-many)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ticker_themes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker_id INTEGER NOT NULL,
                    theme_id INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ticker_id) REFERENCES tickers(id) ON DELETE CASCADE,
                    FOREIGN KEY (theme_id) REFERENCES themes(id) ON DELETE CASCADE,
                    UNIQUE(ticker_id, theme_id)
                )
            """)
            
            # Create indexes for tickers
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tickers_symbol_user 
                ON tickers(symbol, user_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tickers_user_id 
                ON tickers(user_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tickers_is_active 
                ON tickers(is_active)
            """)
            
            # Create indexes for themes
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_themes_user_id 
                ON themes(user_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_themes_name 
                ON themes(name)
            """)
            
            # Create indexes for ticker_themes
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_ticker_themes_ticker_id 
                ON ticker_themes(ticker_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_ticker_themes_theme_id 
                ON ticker_themes(theme_id)
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
