"""Ticker validation utilities."""

import re
from typing import Tuple, Optional, List, Dict
from config import MAX_TICKER_LENGTH


def validate_ticker(symbol: str) -> Tuple[bool, Optional[str]]:
    """
    Validate ticker symbol format.
    
    Rules:
    - 1-10 characters (supports longer international tickers)
    - Alphanumeric plus dots, hyphens, and caret (for tickers like BRK.B, BRK-A, or ^NSEI)
    - Not empty after strip
    
    Args:
        symbol: Ticker symbol to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not symbol or not symbol.strip():
        return False, "Ticker cannot be empty"
    
    symbol = symbol.strip().upper()
    
    # Check length (allowing dots, hyphens, and caret)
    symbol_without_separators = symbol.replace('.', '').replace('-', '').replace('^', '')
    if len(symbol_without_separators) < 1:
        return False, "Ticker too short"
    if len(symbol_without_separators) > MAX_TICKER_LENGTH:
        return False, f"Ticker symbol too long (max {MAX_TICKER_LENGTH} characters excluding dots/hyphens/caret)"
    
    # Check for valid characters (alphanumeric + dots + hyphens + caret)
    if not re.match(r'^[A-Z0-9.\-^]+$', symbol):
        return False, "Ticker contains invalid characters (only letters, numbers, dots, hyphens, and ^ allowed)"
    
    return True, None


def normalize_ticker(symbol: str) -> str:
    """
    Normalize ticker symbol.
    
    Args:
        symbol: Ticker symbol
        
    Returns:
        Normalized symbol (uppercase, stripped)
    """
    return symbol.strip().upper()


def parse_tickers(input_string: str) -> List[str]:
    """
    Parse comma-separated ticker string.
    
    Args:
        input_string: Comma-separated ticker symbols
        
    Returns:
        List of normalized ticker symbols
    """
    if not input_string or not input_string.strip():
        return []
    
    # Split by comma, strip whitespace, normalize, and remove duplicates
    tickers = [normalize_ticker(t) for t in input_string.split(',')]
    # Filter out empty strings
    tickers = [t for t in tickers if t]
    # Remove duplicates while preserving order
    seen = set()
    unique_tickers = []
    for ticker in tickers:
        if ticker not in seen:
            seen.add(ticker)
            unique_tickers.append(ticker)
    
    return unique_tickers


def check_duplicates(tickers: List[str], existing_symbols: List[str]) -> Tuple[List[str], List[str]]:
    """
    Check for duplicates against existing tickers.
    
    Args:
        tickers: List of ticker symbols to check
        existing_symbols: List of existing ticker symbols in database
        
    Returns:
        Tuple of (new_tickers, existing_tickers)
    """
    existing_set = set(existing_symbols)
    new = []
    existing = []
    
    for ticker in tickers:
        if ticker in existing_set:
            existing.append(ticker)
        else:
            new.append(ticker)
    
    return (new, existing)
