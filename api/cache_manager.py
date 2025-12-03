"""Cache manager for price data."""

import logging
from typing import List, Dict, Optional
from datetime import datetime, date
import pandas as pd

from database import get_db_connection

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching of historical price data."""
    
    def get_cached_data(self, ticker_id: int) -> Optional[pd.DataFrame]:
        """
        Retrieve cached price data for a ticker.
        
        Args:
            ticker_id: Database ticker ID
            
        Returns:
            DataFrame with columns: date, open, high, low, close, volume
            None if no cached data exists
        """
        try:
            with get_db_connection() as conn:
                query = """
                    SELECT date, open, high, low, close, volume
                    FROM price_cache
                    WHERE ticker_id = ?
                    ORDER BY date ASC
                """
                cursor = conn.execute(query, (ticker_id,))
                rows = cursor.fetchall()
                
                if not rows:
                    return None
                
                # Convert to DataFrame
                data = []
                for row in rows:
                    data.append({
                        'date': row['date'],
                        'open': row['open'],
                        'high': row['high'],
                        'low': row['low'],
                        'close': row['close'],
                        'volume': row['volume']
                    })
                
                df = pd.DataFrame(data)
                df['date'] = pd.to_datetime(df['date'])
                
                logger.info(f"Retrieved {len(df)} cached records for ticker_id {ticker_id}")
                return df
                
        except Exception as e:
            logger.error(f"Error retrieving cache for ticker_id {ticker_id}: {e}")
            return None
    
    def save_to_cache(self, ticker_id: int, price_data: List[Dict]) -> bool:
        """
        Save price data to cache with upsert logic.
        
        Args:
            ticker_id: Database ticker ID
            price_data: List of price dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        if not price_data:
            logger.warning(f"No data to cache for ticker_id {ticker_id}")
            return False
        
        try:
            with get_db_connection() as conn:
                # Use REPLACE to handle upserts (SQLite)
                for item in price_data:
                    conn.execute("""
                        INSERT OR REPLACE INTO price_cache 
                        (ticker_id, date, open, high, low, close, volume, cached_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        ticker_id,
                        item['date'],
                        item['open'],
                        item['high'],
                        item['low'],
                        item['close'],
                        item['volume'],
                        datetime.now().isoformat()
                    ))
                
                logger.info(f"Cached {len(price_data)} records for ticker_id {ticker_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving cache for ticker_id {ticker_id}: {e}")
            return False
    
    def is_cache_valid(self, ticker_id: int) -> bool:
        """
        Check if cache exists and is valid.
        
        Historical data is always valid (immutable).
        Today's data needs refresh.
        
        Args:
            ticker_id: Database ticker ID
            
        Returns:
            True if cache exists and is valid
        """
        try:
            with get_db_connection() as conn:
                # Check if we have any cached data
                cursor = conn.execute("""
                    SELECT COUNT(*) as count, MAX(date) as latest_date
                    FROM price_cache
                    WHERE ticker_id = ?
                """, (ticker_id,))
                
                row = cursor.fetchone()
                
                if not row or row['count'] == 0:
                    return False
                
                # Check if latest date is recent
                latest_date_str = row['latest_date']
                if not latest_date_str:
                    return False
                
                latest_date = datetime.fromisoformat(latest_date_str).date()
                today = date.today()
                
                # If latest date is today or yesterday (considering market hours/weekends),
                # consider cache valid
                days_old = (today - latest_date).days
                
                if days_old <= 1:
                    logger.debug(f"Cache valid for ticker_id {ticker_id} (latest: {latest_date})")
                    return True
                else:
                    logger.debug(f"Cache stale for ticker_id {ticker_id} (latest: {latest_date}, {days_old} days old)")
                    return False
                    
        except Exception as e:
            logger.error(f"Error checking cache validity for ticker_id {ticker_id}: {e}")
            return False
    
    def update_today_only(self, ticker_id: int, price_data: List[Dict]) -> bool:
        """
        Update only today's price data in cache.
        
        Args:
            ticker_id: Database ticker ID
            price_data: List of price dictionaries
            
        Returns:
            True if successful
        """
        if not price_data:
            return False
        
        try:
            with get_db_connection() as conn:
                # Get today's date
                today = date.today().isoformat()
                
                # Find today's data in the input
                today_data = [item for item in price_data if item['date'] == today]
                
                if not today_data:
                    logger.debug(f"No data for today in update for ticker_id {ticker_id}")
                    return False
                
                # Update today's record
                for item in today_data:
                    conn.execute("""
                        INSERT OR REPLACE INTO price_cache 
                        (ticker_id, date, open, high, low, close, volume, cached_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        ticker_id,
                        item['date'],
                        item['open'],
                        item['high'],
                        item['low'],
                        item['close'],
                        item['volume'],
                        datetime.now().isoformat()
                    ))
                
                logger.info(f"Updated today's data for ticker_id {ticker_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating today's cache for ticker_id {ticker_id}: {e}")
            return False
    
    def clear_cache(self, ticker_id: int) -> bool:
        """
        Clear cached data for a ticker.
        
        Args:
            ticker_id: Database ticker ID
            
        Returns:
            True if successful
        """
        try:
            with get_db_connection() as conn:
                conn.execute("DELETE FROM price_cache WHERE ticker_id = ?", (ticker_id,))
                logger.info(f"Cleared cache for ticker_id {ticker_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error clearing cache for ticker_id {ticker_id}: {e}")
            return False
