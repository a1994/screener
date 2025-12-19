"""
Alert refresh logic with progress tracking and rate limiting.
Handles bulk regeneration of alerts for all tickers.
"""

import time
from typing import List, Dict, Callable, Optional

from database.alert_repository import AlertRepository
from database.ticker_repository import TickerRepository
from alerts.generator import AlertGenerator


class AlertRefresher:
    """
    Handles bulk refresh of alerts with progress tracking and rate limiting.
    """
    
    def __init__(
        self, 
        db_path: str,
        rate_limit_ms: int = 500
    ):
        """
        Initialize the AlertRefresher.
        
        Args:
            db_path: Path to the SQLite database
            rate_limit_ms: Milliseconds to wait between API calls (default 500) - not needed for yfinance
        """
        self.generator = AlertGenerator()
        self.alert_repository = AlertRepository(db_path)
        self.ticker_repository = TickerRepository()
        self.rate_limit_ms = rate_limit_ms
    
    def refresh_all(
        self, 
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        user_id: Optional[int] = None,
        theme_id: Optional[int] = None
    ) -> Dict:
        """
        Refresh alerts for tickers with progress tracking.
        
        Args:
            progress_callback: Optional callback function(current, total, ticker_symbol)
                              Called after each ticker is processed
            user_id: Optional user ID to filter tickers by. If None, processes all users' tickers
            theme_id: Optional theme ID to filter tickers by theme. If None, processes all tickers
                              
        Returns:
            Dictionary with refresh statistics:
                - total_tickers: Total tickers processed
                - successful: Number of successful generations
                - failed: Number of failed generations
                - total_alerts: Total alerts generated
                - errors: List of error dictionaries {ticker_symbol, error}
        """
        # Get tickers (without pagination by setting large page_size)
        all_tickers, total_count = self.ticker_repository.get_all(page=1, page_size=10000, user_id=user_id, theme_id=theme_id)
        total = len(all_tickers)
        
        if total == 0:
            return {
                'total_tickers': 0,
                'successful': 0,
                'failed': 0,
                'total_alerts': 0,
                'errors': []
            }
        
        results = []
        errors = []
        
        for idx, ticker in enumerate(all_tickers):
            # Call progress callback
            if progress_callback:
                progress_callback(idx + 1, total, ticker['symbol'])
            
            # Generate alerts for this ticker
            result = self.generator.generate_for_ticker(
                ticker['id'],
                ticker['symbol']
            )
            
            results.append(result)
            
            # If successful, update database
            if result['success']:
                try:
                    self.alert_repository.update_for_ticker(
                        ticker['id'],
                        ticker['symbol'],
                        result['alerts']
                    )
                except Exception as e:
                    errors.append({
                        'ticker_symbol': ticker['symbol'],
                        'error': f"Database update failed: {str(e)}"
                    })
            else:
                errors.append({
                    'ticker_symbol': ticker['symbol'],
                    'error': result['error']
                })
            
            # Rate limiting (except for last ticker)
            if idx < total - 1:
                time.sleep(self.rate_limit_ms / 1000.0)
        
        # Calculate statistics
        stats = self.generator.get_generation_stats(results)
        stats['errors'] = errors
        
        return stats
    
    def refresh_ticker(
        self, 
        ticker_id: int, 
        ticker_symbol: str
    ) -> Dict:
        """
        Refresh alerts for a single ticker.
        
        Args:
            ticker_id: ID of the ticker
            ticker_symbol: Symbol of the ticker
            
        Returns:
            Dictionary with:
                - success: bool
                - ticker_symbol: str
                - alert_count: int (number of alerts generated)
                - error: str (if success=False)
        """
        # Generate alerts
        result = self.generator.generate_for_ticker(ticker_id, ticker_symbol)
        
        if not result['success']:
            return {
                'success': False,
                'ticker_symbol': ticker_symbol,
                'alert_count': 0,
                'error': result['error']
            }
        
        # Update database
        try:
            self.alert_repository.update_for_ticker(
                ticker_id,
                ticker_symbol,
                result['alerts']
            )
            
            return {
                'success': True,
                'ticker_symbol': ticker_symbol,
                'alert_count': len(result['alerts']),
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'ticker_symbol': ticker_symbol,
                'alert_count': 0,
                'error': f"Database update failed: {str(e)}"
            }
    
    def get_refresh_summary(self, stats: Dict) -> str:
        """
        Get human-readable summary of refresh results.
        
        Args:
            stats: Statistics dictionary from refresh_all()
            
        Returns:
            Summary string
        """
        total = stats['total_tickers']
        success = stats['successful']
        failed = stats['failed']
        alerts = stats['total_alerts']
        
        summary = f"Processed {total} ticker(s): {success} successful, {failed} failed. "
        summary += f"Generated {alerts} alert(s)."
        
        if stats['errors']:
            summary += f"\n\nErrors ({len(stats['errors'])}):"
            for error in stats['errors'][:5]:  # Show first 5 errors
                summary += f"\n- {error['ticker_symbol']}: {error['error']}"
            
            if len(stats['errors']) > 5:
                summary += f"\n... and {len(stats['errors']) - 5} more"
        
        return summary
