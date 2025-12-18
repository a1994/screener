"""Migration script to switch from FMP to yfinance API."""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from api.fmp_client import FMPClient
from api.yfinance_client import YFinanceClient
# Note: Database imports removed for standalone testing
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def compare_api_responses(symbol: str = 'AAPL'):
    """Compare responses between FMP and yfinance for validation."""
    print(f"\n=== Comparing API responses for {symbol} ===")
    
    # Test FMP
    try:
        fmp_client = FMPClient()
        fmp_data = fmp_client.get_historical_prices(symbol)
        fmp_count = len(fmp_data) if fmp_data else 0
        print(f"FMP: {fmp_count} records")
        if fmp_data:
            print(f"FMP Latest: {fmp_data[0]}")
    except Exception as e:
        print(f"FMP Error: {e}")
        fmp_count = 0
    
    # Test yfinance
    try:
        yf_client = YFinanceClient()
        yf_data = yf_client.get_historical_prices(symbol)
        yf_count = len(yf_data) if yf_data else 0
        print(f"yfinance: {yf_count} records")
        if yf_data:
            print(f"yfinance Latest: {yf_data[-1]}")  # yfinance is chronological
            
        # Test ticker info (bonus feature)
        ticker_info = yf_client.get_ticker_info(symbol)
        if ticker_info:
            print(f"Ticker Info: {ticker_info['name']} ({ticker_info['sector']})")
            
    except Exception as e:
        print(f"yfinance Error: {e}")
        yf_count = 0
    
    print(f"Data difference: {abs(yf_count - fmp_count)} records")
    return fmp_count, yf_count


def test_multiple_tickers():
    """Test multiple tickers to compare APIs."""
    print("\n=== Testing Multiple Tickers ===")
    
    # Test common tickers
    test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
    
    yf_client = YFinanceClient()
    
    for symbol in test_symbols:
        print(f"\nTesting {symbol}...")
        
        # Test yfinance
        data = yf_client.get_historical_prices(symbol, period='1y')
        if data:
            print(f"  ✅ {symbol}: {len(data)} records")
        else:
            print(f"  ❌ {symbol}: No data")
            
        # Test validation
        is_valid = yf_client.validate_ticker(symbol)
        print(f"  Valid: {is_valid}")
        
        # Test ticker info
        info = yf_client.get_ticker_info(symbol)
        if info:
            print(f"  Company: {info['name']}")
            print(f"  Sector: {info['sector']}")
        else:
            print(f"  No company info available")


def migration_checklist():
    """Print migration checklist."""
    print("\n" + "="*50)
    print("MIGRATION CHECKLIST")
    print("="*50)
    
    checklist = [
        "✅ Install yfinance: pip install yfinance>=0.2.18",
        "✅ Create YFinanceClient class",
        "⏳ Update api/__init__.py imports",
        "⏳ Update components/chart_analysis.py",
        "⏳ Update alerts/generator.py", 
        "⏳ Update components/alerts_tab.py",
        "⏳ Remove FMP_API_KEY from config/settings.py",
        "⏳ Update config/__init__.py exports",
        "⏳ Test all components work",
        "⏳ Optional: Remove api/fmp_client.py",
    ]
    
    for item in checklist:
        print(f"  {item}")
    
    print("\nBENEFITS:")
    print("  🚀 No rate limits (vs 250/day FMP)")
    print("  🔑 No API key management needed")
    print("  ⚡ Faster batch operations")
    print("  📊 Additional ticker info available")
    print("  💰 Completely free")


if __name__ == "__main__":
    print("Stock Screener API Migration Tool")
    print("FMP → yfinance")
    
    # Compare single ticker
    compare_api_responses('AAPL')
    
    # Test multiple tickers
    test_multiple_tickers()
    
    # Show checklist
    migration_checklist()