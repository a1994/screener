#!/usr/bin/env python3
"""Debug script to diagnose AAPL theme addition issue."""

from database import init_db, TickerRepository, ThemeRepository
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

def debug_aapl_theme_issue():
    """Debug the AAPL theme addition issue."""
    
    # Initialize database
    init_db()
    
    # Initialize repositories
    ticker_repo = TickerRepository()
    theme_repo = ThemeRepository()
    
    test_user_id = 1
    
    print("🐛 Debugging AAPL Theme Addition Issue")
    print("=" * 45)
    
    # 1. Check if AAPL exists
    aapl_ticker = ticker_repo.get_by_symbol('AAPL', test_user_id)
    if aapl_ticker:
        print(f"✅ AAPL exists: ID = {aapl_ticker['id']}")
        ticker_id = aapl_ticker['id']
    else:
        print("❌ AAPL does not exist, creating it...")
        ticker_id = ticker_repo.add_ticker('AAPL', test_user_id)
        print(f"✅ Created AAPL: ID = {ticker_id}")
    
    # 2. Get available themes
    themes = theme_repo.get_user_themes(test_user_id)
    print(f"\n📋 Available themes for user {test_user_id}:")
    for theme in themes:
        print(f"   - {theme['name']} (ID: {theme['id']})")
    
    if not themes:
        print("❌ No themes found, creating a test theme...")
        theme_id = theme_repo.create_theme(test_user_id, "Debug Theme")
        print(f"✅ Created Debug Theme: ID = {theme_id}")
    else:
        theme_id = themes[0]['id']
        theme_name = themes[0]['name']
        print(f"\n🎯 Using theme: {theme_name} (ID: {theme_id})")
    
    # 3. Check if AAPL is already in this theme
    is_in_theme = theme_repo.is_ticker_in_theme(ticker_id, theme_id)
    print(f"\n🔍 Is AAPL already in theme? {is_in_theme}")
    
    # 4. Try to add AAPL to theme (debug version)
    print(f"\n🔧 Attempting to add AAPL (ID: {ticker_id}) to theme (ID: {theme_id})...")
    
    try:
        success = theme_repo.add_ticker_to_theme(ticker_id, theme_id)
        print(f"✅ add_ticker_to_theme result: {success}")
        
        if not success:
            print("❌ Addition failed, checking possible causes...")
            
            # Check if ticker exists by querying database directly
            from database import get_db_connection
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT symbol FROM tickers WHERE id = ? AND user_id = ?", (ticker_id, test_user_id))
                ticker_check = cursor.fetchone()
                print(f"   Ticker {ticker_id} exists: {ticker_check is not None}")
                
                # Check if theme exists
                cursor.execute("SELECT name FROM themes WHERE id = ? AND user_id = ?", (theme_id, test_user_id))
                theme_check = cursor.fetchone()
                print(f"   Theme {theme_id} exists: {theme_check is not None}")
            
            # Check database connection
            from database import get_db_connection
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    print("   Database connection: OK")
            except Exception as e:
                print(f"   Database connection: ERROR - {e}")
        
    except Exception as e:
        print(f"❌ Exception during addition: {e}")
    
    # 5. Verify final state
    final_check = theme_repo.is_ticker_in_theme(ticker_id, theme_id)
    print(f"\n🏁 Final check - Is AAPL in theme? {final_check}")
    
    # 6. Show all tickers in theme
    theme_tickers = theme_repo.get_tickers_by_theme(theme_id, test_user_id)
    print(f"\n📊 All tickers in theme:")
    for ticker in theme_tickers:
        print(f"   - {ticker['symbol']} (ID: {ticker['id']})")

if __name__ == "__main__":
    debug_aapl_theme_issue()