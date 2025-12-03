"""Tests for ticker validation and parsing utilities."""

import pytest
from utils import validate_ticker, normalize_ticker, parse_tickers, check_duplicates


class TestValidateTicker:
    """Test ticker validation function."""
    
    def test_valid_tickers(self):
        """Test validation of valid ticker symbols."""
        assert validate_ticker("AAPL")[0] is True
        assert validate_ticker("MSFT")[0] is True
        assert validate_ticker("GOOGL")[0] is True
        assert validate_ticker("A")[0] is True
        assert validate_ticker("BRK.B")[0] is True
    
    def test_invalid_empty(self):
        """Test validation of empty ticker."""
        is_valid, error = validate_ticker("")
        assert is_valid is False
        assert "empty" in error.lower()
    
    def test_invalid_too_long(self):
        """Test validation of ticker too long."""
        is_valid, error = validate_ticker("TOOLONG")
        assert is_valid is False
        assert "too long" in error.lower()
    
    def test_invalid_characters(self):
        """Test validation of ticker with invalid characters."""
        is_valid, error = validate_ticker("AA$PL")
        assert is_valid is False
        assert "invalid characters" in error.lower()
    
    def test_lowercase_handled(self):
        """Test that lowercase tickers are validated correctly."""
        assert validate_ticker("aapl")[0] is True


class TestNormalizeTicker:
    """Test ticker normalization function."""
    
    def test_uppercase_conversion(self):
        """Test conversion to uppercase."""
        assert normalize_ticker("aapl") == "AAPL"
        assert normalize_ticker("MsFt") == "MSFT"
    
    def test_whitespace_removal(self):
        """Test removal of whitespace."""
        assert normalize_ticker("  AAPL  ") == "AAPL"
        assert normalize_ticker(" MSFT ") == "MSFT"
    
    def test_combined_normalization(self):
        """Test combined normalization."""
        assert normalize_ticker("  aapl  ") == "AAPL"


class TestParseTickers:
    """Test ticker parsing function."""
    
    def test_single_ticker(self):
        """Test parsing single ticker."""
        result = parse_tickers("AAPL")
        assert result == ["AAPL"]
    
    def test_multiple_tickers(self):
        """Test parsing multiple comma-separated tickers."""
        result = parse_tickers("AAPL, MSFT, GOOGL")
        assert result == ["AAPL", "MSFT", "GOOGL"]
    
    def test_deduplication(self):
        """Test deduplication of tickers."""
        result = parse_tickers("AAPL, MSFT, AAPL")
        assert result == ["AAPL", "MSFT"]
    
    def test_empty_string(self):
        """Test parsing empty string."""
        result = parse_tickers("")
        assert result == []
    
    def test_whitespace_handling(self):
        """Test handling of whitespace."""
        result = parse_tickers("  AAPL  ,  MSFT  ")
        assert result == ["AAPL", "MSFT"]
    
    def test_lowercase_conversion(self):
        """Test conversion to uppercase."""
        result = parse_tickers("aapl, msft")
        assert result == ["AAPL", "MSFT"]


class TestCheckDuplicates:
    """Test duplicate checking function."""
    
    def test_no_duplicates(self):
        """Test when no duplicates exist."""
        new, existing = check_duplicates(["AAPL", "MSFT"], ["GOOGL", "AMZN"])
        assert new == ["AAPL", "MSFT"]
        assert existing == []
    
    def test_all_duplicates(self):
        """Test when all tickers are duplicates."""
        new, existing = check_duplicates(["AAPL", "MSFT"], ["AAPL", "MSFT", "GOOGL"])
        assert new == []
        assert existing == ["AAPL", "MSFT"]
    
    def test_mixed_duplicates(self):
        """Test with mix of new and duplicate tickers."""
        new, existing = check_duplicates(["AAPL", "MSFT", "GOOGL"], ["AAPL", "AMZN"])
        assert new == ["MSFT", "GOOGL"]
        assert existing == ["AAPL"]
    
    def test_empty_input(self):
        """Test with empty ticker list."""
        new, existing = check_duplicates([], ["AAPL", "MSFT"])
        assert new == []
        assert existing == []
    
    def test_empty_existing(self):
        """Test with empty existing list."""
        new, existing = check_duplicates(["AAPL", "MSFT"], [])
        assert new == ["AAPL", "MSFT"]
        assert existing == []
