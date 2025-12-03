"""Tests for display formatting utilities."""

import pytest
from utils import format_date, format_datetime, format_number, format_count


class TestFormatDate:
    """Test date formatting function."""
    
    def test_valid_date(self):
        """Test formatting of valid ISO date."""
        assert format_date("2025-01-20") == "2025-01-20"
        assert format_date("2025-12-31") == "2025-12-31"
    
    def test_datetime_string(self):
        """Test formatting of datetime string (should extract date)."""
        assert format_date("2025-01-20T14:30:00") == "2025-01-20"
    
    def test_none_value(self):
        """Test formatting of None value."""
        assert format_date(None) == "N/A"
    
    def test_empty_string(self):
        """Test formatting of empty string."""
        assert format_date("") == "N/A"
    
    def test_custom_default(self):
        """Test custom default value."""
        assert format_date(None, default="Unknown") == "Unknown"
    
    def test_invalid_format(self):
        """Test formatting of invalid date format."""
        assert format_date("not-a-date") == "N/A"


class TestFormatDatetime:
    """Test datetime formatting function."""
    
    def test_valid_datetime(self):
        """Test formatting of valid ISO datetime."""
        assert format_datetime("2025-01-20T14:30:00") == "2025-01-20 14:30"
    
    def test_none_value(self):
        """Test formatting of None value."""
        assert format_datetime(None) == "N/A"
    
    def test_custom_default(self):
        """Test custom default value."""
        assert format_datetime(None, default="Unknown") == "Unknown"


class TestFormatNumber:
    """Test number formatting function."""
    
    def test_integer(self):
        """Test formatting of integer."""
        assert format_number(1234) == "1,234.00"
    
    def test_float(self):
        """Test formatting of float."""
        assert format_number(1234.56) == "1,234.56"
    
    def test_large_number(self):
        """Test formatting of large number."""
        assert format_number(1234567.89) == "1,234,567.89"
    
    def test_decimals(self):
        """Test custom decimal places."""
        assert format_number(123.456, decimals=0) == "123"
        assert format_number(123.456, decimals=1) == "123.5"
        assert format_number(123.456, decimals=3) == "123.456"
    
    def test_none_value(self):
        """Test formatting of None value."""
        assert format_number(None) == "N/A"
    
    def test_custom_default(self):
        """Test custom default value."""
        assert format_number(None, default="Unknown") == "Unknown"


class TestFormatCount:
    """Test count formatting function."""
    
    def test_small_count(self):
        """Test formatting of small count."""
        assert format_count(123) == "123"
    
    def test_large_count(self):
        """Test formatting of large count."""
        assert format_count(1234) == "1,234"
        assert format_count(1234567) == "1,234,567"
    
    def test_zero(self):
        """Test formatting of zero."""
        assert format_count(0) == "0"
