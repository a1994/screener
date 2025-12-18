"""API module for data fetching."""

from .fmp_client import FMPClient
from .yfinance_client import YFinanceClient
from .cache_manager import CacheManager

# Primary client (can switch between FMP and yfinance)
DataClient = YFinanceClient  # Change this to switch APIs

__all__ = ['FMPClient', 'YFinanceClient', 'DataClient', 'CacheManager']
