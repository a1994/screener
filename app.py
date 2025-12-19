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
from components.user_management import render_user_selector, render_user_info_sidebar, get_current_user_id, initialize_user_system




def init_app() -> None:
    """Initialize the application and database."""
    # Initialize database
    db_path = Path(DATABASE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        init_db(str(db_path))
        
        # Initialize user system after database is ready
        initialize_user_system()
        
        # Initialize session state for user-specific ticker list
        # This will be updated when user changes in render_user_selector
        if 'active_tickers' not in st.session_state:
            st.session_state.active_tickers = []
        
    except Exception as e:
        st.error(f"Error initializing database: {str(e)}")
        st.stop()


def render_sidebar() -> None:
    """Render sidebar with stats and info."""
    with st.sidebar:
        st.title(f"{APP_ICON} Stock Screener")
        st.markdown("---")
        
        # Display user-specific stats
        st.subheader("📊 Statistics")
        try:
            current_user_id = get_current_user_id()
            repo = TickerRepository()
            render_ticker_stats(repo, user_id=current_user_id)
        except Exception as e:
            st.error(f"Error loading stats: {str(e)}")
        
        # Render user info
        render_user_info_sidebar()
        
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
    
    # Add full-width CSS to eliminate black spaces
    st.markdown("""
    <style>
    /* Remove default Streamlit padding and margins */
    .main > div {
        max-width: 100%;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    
    /* Full width container */
    .stApp > .main {
        max-width: 100%;
    }
    
    /* Remove default container constraints */
    .block-container {
        max-width: 100%;
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    
    /* Ensure tabs use full width */
    .stTabs {
        width: 100%;
    }
    
    /* Full width for tab content */
    .stTabContent {
        padding: 1rem 0;
    }
    
    /* Dark theme improvements */
    .stApp {
        background-color: #0E1117;
    }
    
    /* Remove sidebar padding when collapsed */
    .css-1d391kg {
        padding-left: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Render user selector in top-right area
    current_user_id = render_user_selector()
    
    # Update active tickers for current user
    repo = TickerRepository()
    st.session_state.active_tickers = repo.get_active_tickers(current_user_id)
    
    # Render sidebar
    render_sidebar()
    
    # Main content area
    st.title(f"{APP_ICON} {APP_TITLE}")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📈 Chart Analysis", "🔔 Alerts", "📋 Dashboard"])
    
    with tab1:
        render_chart_analysis(user_id=current_user_id)
    
    with tab2:
        try:
            render_alerts_tab(user_id=current_user_id)
        except Exception as e:
            st.error(f"Error loading alerts: {str(e)}")
            st.exception(e)
    
    with tab3:
        try:
            repo = TickerRepository()
            
            # Dashboard (user-specific)
            render_dashboard(repo, user_id=current_user_id)
        
        except Exception as e:
            st.error(f"Error loading dashboard: {str(e)}")
            st.exception(e)


if __name__ == "__main__":
    main()
