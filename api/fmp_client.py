"""API client for Financial Modeling Prep data source."""

import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime
import time

from config import FMP_API_KEY, FMP_BASE_URL

logger = logging.getLogger(__name__)


class FMPClient:
    """Client for Financial Modeling Prep API."""
    
    def __init__(self, api_key: str = FMP_API_KEY, base_url: str = FMP_BASE_URL):
        """
        Initialize FMP client.
        
        Args:
            api_key: FMP API key
            base_url: Base URL for FMP API
        """
        self.api_key = api_key
        self.base_url = base_url
        self.request_count = 0
        self.last_request_time = None
        
    def get_historical_prices(self, symbol: str, retry_count: int = 3) -> Optional[List[Dict]]:
        """
        Fetch historical EOD prices for a ticker.
        
        Args:
            symbol: Ticker symbol
            retry_count: Number of retry attempts
            
        Returns:
            List of price dictionaries with keys: date, open, high, low, close, volume
            None if request fails after retries
        """
        url = f"{self.base_url}/historical-price-eod/full"
        params = {
            'symbol': symbol,
            'apikey': self.api_key
        }
        
        for attempt in range(retry_count):
            try:
                # Rate limiting - wait if needed
                self._rate_limit_check()
                
                # Make request
                response = requests.get(url, params=params, timeout=30)
                self.request_count += 1
                self.last_request_time = datetime.now()
                
                # Handle response
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if data is valid (API returns a list directly)
                    if not data or not isinstance(data, list):
                        logger.error(f"No historical data for {symbol}")
                        return None
                    
                    # Normalize data structure
                    normalized = []
                    for item in data:
                        normalized.append({
                            'date': item.get('date'),
                            'open': item.get('open'),
                            'high': item.get('high'),
                            'low': item.get('low'),
                            'close': item.get('close'),
                            'volume': item.get('volume')
                        })
                    
                    logger.info(f"Fetched {len(normalized)} price records for {symbol}")
                    return normalized
                    
                elif response.status_code == 429:
                    # Rate limit exceeded
                    logger.warning(f"Rate limit exceeded, attempt {attempt + 1}/{retry_count}")
                    if attempt < retry_count - 1:
                        wait_time = (2 ** attempt) * 2  # Exponential backoff
                        time.sleep(wait_time)
                        continue
                    return None
                    
                elif response.status_code == 404:
                    # Invalid ticker
                    logger.error(f"Ticker {symbol} not found (404)")
                    return None
                    
                else:
                    # Other error
                    logger.error(f"API error {response.status_code}: {response.text}")
                    if attempt < retry_count - 1:
                        wait_time = (2 ** attempt)  # Exponential backoff
                        time.sleep(wait_time)
                        continue
                    return None
                    
            except requests.exceptions.Timeout:
                logger.error(f"Request timeout for {symbol}, attempt {attempt + 1}/{retry_count}")
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)
                    continue
                return None
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed for {symbol}: {e}, attempt {attempt + 1}/{retry_count}")
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)
                    continue
                return None
                
            except Exception as e:
                logger.error(f"Unexpected error fetching {symbol}: {e}")
                return None
        
        return None
    
    def _rate_limit_check(self):
        """Check rate limiting and wait if necessary."""
        if self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            # Minimum 0.5 seconds between requests (conservative)
            if elapsed < 0.5:
                time.sleep(0.5 - elapsed)
    
    def get_request_stats(self) -> Dict:
        """
        Get API request statistics.
        
        Returns:
            Dictionary with request count and last request time
        """
        return {
            'request_count': self.request_count,
            'last_request_time': self.last_request_time
        }
