#!/usr/bin/env python3
"""Test volume data availability."""

import yfinance as yf
import pandas as pd

def test_volume_data():
    """Test if volume data is available for AAPL."""
    try:
        ticker = yf.Ticker('AAPL')
        data = ticker.history(period='5d')
        
        print(f"AAPL Data Shape: {data.shape}")
        print(f"Columns: {list(data.columns)}")
        print("\nLast 3 rows:")
        print(data[['Open', 'High', 'Low', 'Close', 'Volume']].tail(3))
        
        print(f"\nVolume stats:")
        print(f"Min volume: {data['Volume'].min():,.0f}")
        print(f"Max volume: {data['Volume'].max():,.0f}")
        print(f"Zero volume days: {(data['Volume'] == 0).sum()}")
        
        if len(data) > 0 and 'Volume' in data.columns:
            print("\n✅ Volume data is available!")
            return True
        else:
            print("\n❌ No volume data found!")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_volume_data()