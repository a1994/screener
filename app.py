"""
Stock Screener - Technical Analysis Dashboard
Main Streamlit application entry point
"""

import streamlit as st
from pathlib import Path

# Import configuration
from config import APP_TITLE, APP_ICON, PAGE_CONFIG, DATABASE_PATH

# Import database
from database import init_db, get_db_connection, TickerRepository

# Import components
from components import render_ticker_input, render_dashboard, render_ticker_stats, render_chart_analysis
from components.alerts_tab import render_alerts_tab


def init_app() -> None:
    """Initialize the application and database."""
    # Configure page
    st.set_page_config(**PAGE_CONFIG)
    
    # Initialize database
    db_path = Path(DATABASE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        init_db(str(db_path))
    except Exception as e:
        st.error(f"Error initializing database: {str(e)}")
        st.stop()


def render_sidebar() -> None:
    """Render sidebar with stats and info."""
    with st.sidebar:
        st.title(f"{APP_ICON} Stock Screener")
        st.markdown("---")
        
        # Display stats
        st.subheader("📊 Statistics")
        try:
            repo = TickerRepository()
            render_ticker_stats(repo)
        except Exception as e:
            st.error(f"Error loading stats: {str(e)}")
        
        st.markdown("---")
        
        # About section
        with st.expander("ℹ️ About"):
            st.markdown("""
            **Stock Screener** is a technical analysis dashboard for tracking 
            and analyzing stock tickers.
            
            **Features:**
            - Ticker management (add, search, delete)
            - Interactive charts with EMAs
            - Trading signals (Long/Short)
            - Alert system
            
            **Technical Indicators:**
            - MACD, RSI, Supertrend
            - Ichimoku Cloud, Gann HiLo
            - EMAs (8, 21, 50)
            """)
        
        # Help section
        with st.expander("❓ Help"):
            st.markdown("""
            **Getting Started:**
            1. Go to "Dashboard" tab
            2. Add tickers using any input method
            3. View and manage your ticker list
            
            **Adding Tickers:**
            - **Manual Entry:** Add one ticker at a time
            - **Comma-Separated:** Add multiple tickers (e.g., AAPL, MSFT, GOOGL)
            - **CSV Upload:** Upload a CSV file with a 'symbol' or 'ticker' column
            
            **Managing Tickers:**
            - Use search to filter tickers
            - Sort by symbol or date
            - Select and delete multiple tickers
            - Export tickers to CSV
            """)


def main():
    """Main application function."""
    # Initialize app
    init_app()
    
    # Render sidebar
    render_sidebar()
    
    # Main content area
    st.title(f"{APP_ICON} {APP_TITLE}")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📈 Chart Analysis", "🔔 Alerts", "📋 Dashboard"])
    
    with tab1:
        render_chart_analysis()
    
    with tab2:
        try:
            render_alerts_tab()
        except Exception as e:
            st.error(f"Error loading alerts: {str(e)}")
            st.exception(e)
    
    with tab3:
        try:
            repo = TickerRepository()
            
            # Add ticker section (collapsible)
            with st.expander("➕ Add Tickers", expanded=False):
                render_ticker_input(repo)
            
            st.markdown("---")
            
            # Dashboard
            render_dashboard(repo)
        
        except Exception as e:
            st.error(f"Error loading dashboard: {str(e)}")
            st.exception(e)


if __name__ == "__main__":
    main()
