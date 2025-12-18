"""Updated configuration settings for yfinance migration."""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Database settings
DATABASE_PATH = os.getenv('DATABASE_PATH', str(BASE_DIR / 'data' / 'screener.db'))

# Pagination settings
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200

# Ticker validation settings
MAX_TICKER_LENGTH = 10
MIN_TICKER_LENGTH = 1

# Bulk operations settings
MAX_BULK_INSERT_SIZE = 1000

# API settings (yfinance - no key required!)
# Note: FMP settings removed, yfinance is free and unlimited

# Cache settings
CACHE_EXPIRY_HOURS = 24  # Only for today's data
MAX_CACHE_AGE_DAYS = 365  # Clean up old cached data

# Chart settings
DEFAULT_CHART_PERIOD = '1y'  # Default chart period

# Technical indicator settings
MACD_SETTINGS = {'fast': 12, 'slow': 26, 'signal': 9}
RSI_SETTINGS = {'period': 14}
SUPERTREND_SETTINGS = {'period': 10, 'multiplier': 3.0}
ICHIMOKU_SETTINGS = {'conversion': 9, 'base': 26, 'span_b': 52, 'displacement': 26}
GANN_HILO_SETTINGS = {'fast': 13, 'slow': 21}
EMA_PERIODS = [8, 21, 50]

# Volume settings
VOLUME_MA_PERIOD = 20

# App settings
APP_TITLE = "Stock Screener - Technical Analysis Dashboard"
APP_ICON = "📈"
PAGE_CONFIG = {
    'page_title': APP_TITLE,
    'page_icon': APP_ICON,
    'layout': 'wide',
    'initial_sidebar_state': 'expanded'
}

# Date format
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"