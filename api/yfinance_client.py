"""API client for yfinance data source."""

import yfinance as yf
import logging
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)


class YFinanceClient:
    """Client for Yahoo Finance data via yfinance."""
    
    def __init__(self):
        """
        Initialize yfinance client.
        No API key required for yfinance.
        """
        self.request_count = 0
        self.last_request_time = None
        
    def get_historical_prices(self, symbol: str, period: str = 'max', retry_count: int = 3) -> Optional[List[Dict]]:
        """
        Fetch historical prices for a ticker using yfinance.
        
        Args:
            symbol: Ticker symbol (e.g., 'AAPL', 'TSLA')
            period: Data period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            retry_count: Number of retry attempts
            
        Returns:
            List of price dictionaries with keys: date, open, high, low, close, volume
            None if request fails after retries
        """
        for attempt in range(retry_count):
            try:
                # Create ticker object
                ticker = yf.Ticker(symbol)
                
                # Fetch historical data
                hist_data = ticker.history(period=period)
                self.request_count += 1
                self.last_request_time = datetime.now()
                
                # Check if data exists
                if hist_data.empty:
                    logger.error(f"No historical data found for {symbol}")
                    return None
                
                # Convert to our standard format
                normalized = []
                for date, row in hist_data.iterrows():
                    normalized.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'open': float(row['Open']),
                        'high': float(row['High']),
                        'low': float(row['Low']),
                        'close': float(row['Close']),
                        'volume': int(row['Volume']) if pd.notna(row['Volume']) else 0
                    })
                
                logger.info(f"Fetched {len(normalized)} price records for {symbol}")
                return normalized
                
            except Exception as e:
                logger.error(f"Error fetching {symbol}, attempt {attempt + 1}/{retry_count}: {e}")
                if attempt < retry_count - 1:
                    continue
                return None
        
        return None
    
    def get_ticker_info(self, symbol: str) -> Optional[Dict]:
        """
        Get ticker information (company name, sector, etc.).
        
        Args:
            symbol: Ticker symbol
            
        Returns:
            Dictionary with ticker info or None if not found
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Check if ticker is valid (yfinance returns empty dict for invalid tickers)
            if not info or 'symbol' not in info:
                return None
                
            return {
                'symbol': info.get('symbol', symbol),
                'name': info.get('longName', info.get('shortName', 'Unknown')),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'market_cap': info.get('marketCap'),
                'currency': info.get('currency', 'USD')
            }
            
        except Exception as e:
            logger.error(f"Error getting info for {symbol}: {e}")
            return None
    
    def validate_ticker(self, symbol: str) -> bool:
        """
        Validate if a ticker symbol exists.
        
        Args:
            symbol: Ticker symbol to validate
            
        Returns:
            True if ticker exists, False otherwise
        """
        try:
            ticker = yf.Ticker(symbol)
            hist_data = ticker.history(period='1d')
            return not hist_data.empty
        except Exception:
            return False
    
    def get_request_stats(self) -> Dict:
        """
        Get API request statistics.
        
        Returns:
            Dictionary with request count and last request time
        """
        return {
            'request_count': self.request_count,
            'last_request_time': self.last_request_time,
            'rate_limited': False  # yfinance has no enforced rate limits
        }