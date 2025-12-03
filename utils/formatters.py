"""Formatting utilities for display."""

from datetime import datetime
from typing import Optional


def format_date(date_str: Optional[str], default: str = "N/A") -> str:
    """
    Format ISO date string for display.
    
    Args:
        date_str: ISO format date string
        default: Default value if date is None
        
    Returns:
        Formatted date string (e.g., "2025-11-20")
    """
    if not date_str:
        return default
    
    try:
        # Parse ISO format
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%Y-%m-%d")
    except (ValueError, AttributeError):
        return default


def format_datetime(date_str: Optional[str], default: str = "N/A") -> str:
    """
    Format ISO datetime string for display.
    
    Args:
        date_str: ISO format datetime string
        default: Default value if date is None
        
    Returns:
        Formatted datetime string (e.g., "2025-11-20 14:30")
    """
    if not date_str:
        return default
    
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, AttributeError):
        return default


def format_number(num: Optional[float], decimals: int = 2, default: str = "N/A") -> str:
    """
    Format number for display.
    
    Args:
        num: Number to format
        decimals: Number of decimal places
        default: Default value if num is None
        
    Returns:
        Formatted number string
    """
    if num is None:
        return default
    
    try:
        return f"{num:,.{decimals}f}"
    except (ValueError, TypeError):
        return default


def format_count(count: int) -> str:
    """
    Format count with thousand separators.
    
    Args:
        count: Count to format
        
    Returns:
        Formatted count string (e.g., "1,234")
    """
    return f"{count:,}"
