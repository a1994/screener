"""Tests for database operations."""

import pytest
import sqlite3
import tempfile
import os
from pathlib import Path

from database import DatabaseManager, TickerRepository, init_db, get_db_connection


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    # Create temporary file
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Initialize database
    init_db(path)
    
    yield path
    
    # Cleanup
    try:
        os.unlink(path)
    except:
        pass


@pytest.fixture
def db_manager(temp_db):
    """Create a DatabaseManager instance for testing."""
    return DatabaseManager(temp_db)


@pytest.fixture
def repo(db_manager):
    """Create a TickerRepository instance for testing."""
    with db_manager.get_connection() as conn:
        yield TickerRepository(conn)


class TestDatabaseManager:
    """Test DatabaseManager class."""
    
    def test_init_db(self, temp_db):
        """Test database initialization."""
        # Check that tables exist
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            
            # Check tickers table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tickers'")
            assert cursor.fetchone() is not None
            
            # Check price_cache table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='price_cache'")
            assert cursor.fetchone() is not None
    
    def test_connection_context_manager(self, db_manager):
        """Test connection context manager."""
        with db_manager.get_connection() as conn:
            assert conn is not None
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            assert cursor.fetchone()[0] == 1


class TestTickerRepository:
    """Test TickerRepository class."""
    
    def test_add_ticker(self, temp_db):
        """Test adding a single ticker."""
        init_db(temp_db)
        repo = TickerRepository()
        
        ticker_id = repo.add_ticker("AAPL")
        assert ticker_id is not None
        assert ticker_id > 0
    
    def test_add_duplicate_ticker(self, temp_db):
        """Test adding duplicate ticker."""
        init_db(temp_db)
        repo = TickerRepository()
        
        # Add first time
        ticker_id1 = repo.add_ticker("AAPL")
        assert ticker_id1 is not None
        
        # Try to add duplicate
        ticker_id2 = repo.add_ticker("AAPL")
        assert ticker_id2 is None
    
    def test_bulk_add(self, temp_db):
        """Test bulk adding tickers."""
        init_db(temp_db)
        repo = TickerRepository()
        
        symbols = ["AAPL", "MSFT", "GOOGL"]
        result = repo.bulk_add(symbols)
        
        assert result['added'] == 3
        assert result['failed'] == 0
        assert len(result['errors']) == 0
    
    def test_get_all(self, temp_db):
        """Test getting all tickers."""
        init_db(temp_db)
        repo = TickerRepository()
        
        # Add some tickers
        repo.bulk_add(["AAPL", "MSFT", "GOOGL"])
        
        # Get all
        tickers, total = repo.get_all()
        
        assert len(tickers) == 3
        assert total == 3
    
    def test_get_all_pagination(self, temp_db):
        """Test pagination."""
        init_db(temp_db)
        repo = TickerRepository()
        
        # Add 10 tickers
        symbols = [f"TICK{i}" for i in range(10)]
        repo.bulk_add(symbols)
        
        # Get page 1 (5 items)
        tickers, total = repo.get_all(page=1, page_size=5)
        
        assert len(tickers) == 5
        assert total == 10
    
    def test_search(self, temp_db):
        """Test search functionality."""
        init_db(temp_db)
        repo = TickerRepository()
        
        # Add tickers
        repo.bulk_add(["AAPL", "AMZN", "MSFT", "GOOGL"])
        
        # Search for 'A'
        tickers, total = repo.search("A")
        
        assert len(tickers) == 2  # AAPL, AMZN
        assert total == 2
    
    def test_get_by_symbol(self, temp_db):
        """Test getting ticker by symbol."""
        init_db(temp_db)
        repo = TickerRepository()
        
        # Add ticker
        repo.add_ticker("AAPL")
        
        # Get by symbol
        ticker = repo.get_by_symbol("AAPL")
        
        assert ticker is not None
        assert ticker['symbol'] == "AAPL"
    
    def test_delete(self, temp_db):
        """Test soft delete."""
        init_db(temp_db)
        repo = TickerRepository()
        
        # Add ticker
        ticker_id = repo.add_ticker("AAPL")
        
        # Delete
        assert repo.delete(ticker_id) is True
        
        # Verify soft delete
        tickers, total = repo.get_all()
        assert len(tickers) == 0
    
    def test_bulk_delete(self, temp_db):
        """Test bulk delete."""
        init_db(temp_db)
        repo = TickerRepository()
        
        # Add tickers
        repo.bulk_add(["AAPL", "MSFT", "GOOGL"])
        
        # Get IDs
        tickers, _ = repo.get_all()
        ticker_ids = [t['id'] for t in tickers[:2]]
        
        # Bulk delete
        deleted_count = repo.bulk_delete(ticker_ids)
        
        assert deleted_count == 2
        
        # Verify
        tickers, total = repo.get_all()
        assert len(tickers) == 1
    
    def test_get_active_tickers(self, temp_db):
        """Test getting active ticker symbols."""
        init_db(temp_db)
        repo = TickerRepository()
        
        # Add tickers
        repo.bulk_add(["AAPL", "MSFT", "GOOGL"])
        
        # Get active
        symbols = repo.get_active_tickers()
        
        assert len(symbols) == 3
        assert "AAPL" in symbols
        assert "MSFT" in symbols
        assert "GOOGL" in symbols
