"""
Alert generation logic.
Generates alerts for tickers by reusing SignalGenerator and applying deduplication.
"""

from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime

from api.fmp_client import FMPClient
from api.cache_manager import CacheManager
from indicators.calculator import IndicatorCalculator
from indicators.signals import SignalGenerator
from alerts.deduplicator import AlertDeduplicator


class AlertGenerator:
    """
    Generates alerts for tickers by calculating indicators and signals.
    Reuses existing signal generation logic and applies deduplication rules.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the AlertGenerator.
        
        Args:
            api_key: Financial Modeling Prep API key
        """
        self.fmp_client = FMPClient(api_key)
        self.cache_manager = CacheManager()
        self.deduplicator = AlertDeduplicator()
    
    def generate_for_ticker(
        self, 
        ticker_id: int, 
        ticker_symbol: str
    ) -> Dict:
        """
        Generate alerts for a specific ticker.
        
        Args:
            ticker_id: ID of the ticker
            ticker_symbol: Symbol of the ticker
            
        Returns:
            Dictionary with:
                - success: bool
                - ticker_id: int
                - ticker_symbol: str
                - alerts: List of alert dictionaries
                - error: str (if success=False)
        """
        try:
            # Check cache first
            cached_df = self.cache_manager.get_cached_data(ticker_id)
            
            if cached_df is not None and self.cache_manager.is_cache_valid(ticker_id):
                # Use cached data
                df = cached_df
            else:
                # Fetch from API
                price_data = self.fmp_client.get_historical_prices(ticker_symbol)
                
                if not price_data:
                    return {
                        'success': False,
                        'ticker_id': ticker_id,
                        'ticker_symbol': ticker_symbol,
                        'alerts': [],
                        'error': 'No price data available from API'
                    }
                
                # Convert to DataFrame
                df = pd.DataFrame(price_data)
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date').reset_index(drop=True)
                
                # Save to cache
                self.cache_manager.save_to_cache(ticker_id, price_data)
            
            # Calculate indicators
            calculator = IndicatorCalculator(df)
            df_with_indicators = calculator.calculate_all()
            
            # Generate signals
            signal_generator = SignalGenerator(df_with_indicators)
            df_with_signals = signal_generator.generate_all_signals()
            df_with_labels = signal_generator.add_signal_labels()
            
            # Deduplicate to max 2 alerts
            alerts = self.deduplicator.deduplicate(df_with_labels)
            
            return {
                'success': True,
                'ticker_id': ticker_id,
                'ticker_symbol': ticker_symbol,
                'alerts': alerts,
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'ticker_id': ticker_id,
                'ticker_symbol': ticker_symbol,
                'alerts': [],
                'error': str(e)
            }
    
    def generate_for_all_tickers(
        self, 
        tickers: List[Dict]
    ) -> List[Dict]:
        """
        Generate alerts for all tickers.
        
        Args:
            tickers: List of ticker dictionaries with 'id' and 'symbol' keys
            
        Returns:
            List of result dictionaries (same format as generate_for_ticker)
        """
        results = []
        
        for ticker in tickers:
            result = self.generate_for_ticker(
                ticker['id'], 
                ticker['symbol']
            )
            results.append(result)
        
        return results
    
    def get_generation_stats(self, results: List[Dict]) -> Dict:
        """
        Calculate statistics from generation results.
        
        Args:
            results: List of result dictionaries from generate_for_ticker
            
        Returns:
            Dictionary with statistics:
                - total: Total tickers processed
                - success: Number of successful generations
                - failed: Number of failed generations
                - total_alerts: Total alerts generated
        """
        total = len(results)
        success = sum(1 for r in results if r['success'])
        failed = total - success
        total_alerts = sum(len(r['alerts']) for r in results if r['success'])
        
        return {
            'total_tickers': total,
            'successful': success,
            'failed': failed,
            'total_alerts': total_alerts
        }
