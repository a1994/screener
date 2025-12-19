"""Chart Analysis component for the stock screener."""

import streamlit as st
import pandas as pd
import logging
from typing import Optional

from database import TickerRepository
from api import DataClient, CacheManager
from indicators import IndicatorCalculator, SignalGenerator
from charts import ChartRenderer
from utils.mobile_responsive import mobile_friendly_columns, mobile_metric_card

logger = logging.getLogger(__name__)


def render_chart_analysis(user_id: int = 1):
    """
    Render Chart Analysis tab with ticker selection and chart display for a specific user.
    
    Args:
        user_id: User ID to filter tickers by
    """
    st.subheader("📈 Chart Analysis & Trading Signals")
    
    # Get active tickers from database - always fetch fresh to ensure new tickers appear
    try:
        repo = TickerRepository()
        
        # Always fetch fresh ticker list from database to ensure new tickers appear
        active_symbols = repo.get_active_tickers(user_id=user_id)
        
        if not active_symbols:
            st.info("No tickers available. Please add tickers in the Dashboard tab first.")
            return
        
        # Ticker selection and date range
        col1, col2, col3 = st.columns([2, 2, 1])
        
        # Generate a unique key based on ticker count to force selectbox refresh
        ticker_key = f"ticker_select_{len(active_symbols)}"
        
        with col1:
            selected_symbol = st.selectbox(
                "Select Ticker",
                options=sorted(active_symbols),
                key=ticker_key,
                help="Choose a ticker to analyze"
            )
        
        with col2:
            date_range = st.selectbox(
                "Date Range",
                options=['3 months', '6 months', '1 year', '2 years', 'All data'],
                index=0,  # Default to 3 months
                help="Select how much historical data to display"
            )
        
        with col3:
            load_button = st.button("📈 Load Chart", type="primary", key="chart_load_btn")
        
        # Load and display chart
        if load_button and selected_symbol:
            with st.spinner(f"Loading chart for {selected_symbol}..."):
                # Add mobile-friendly container
                st.markdown('<div class="mobile-scroll">', unsafe_allow_html=True)
                _load_and_display_chart(selected_symbol, repo, date_range, user_id)
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Show instructions if no chart loaded
        if not load_button:
            st.markdown("""
            ### How to use:
            1. **Select a ticker** from the dropdown
            2. **Choose date range** (default: 3 months for faster loading)
               - Use longer ranges to see more historical context
               - Indicators are calculated on full dataset for accuracy
            3. Click **Load Chart** to fetch data and generate analysis
            4. **Interact with the chart**: zoom, pan, hover for details
            
            ### Features:
            - **Candlestick chart** with OHLC data
            - **EMAs (8, 21, 50)** for trend identification
            - **Gann HiLo Activator** (cyan dashed line)
            - **Supertrend** (green/red based on direction)
            - **Ichimoku Cloud** (purple fill)
            - **Trading signals** marked with triangles:
              - 🟢 **Green ▲**: Long OPEN
              - 🔴 **Red ▼**: Long CLOSE
              - 🟠 **Orange ▼**: Short OPEN
              - 🔵 **Cyan ▲**: Short CLOSE
            - **Volume subplot** with 20-day MA
            
            💡 **Tip**: Start with 3 months view for quick analysis, then zoom out if needed.
            """)
    
    except Exception as e:
        st.error(f"Error loading Chart Analysis: {str(e)}")
        logger.error(f"Chart Analysis error: {e}", exc_info=True)


def _load_and_display_chart(symbol: str, repo: TickerRepository, date_range: str = '3 months', user_id: int = 1):
    """
    Load data, calculate indicators, and display chart.
    
    Args:
        symbol: Ticker symbol
        repo: TickerRepository instance
        date_range: Date range for data
        user_id: User ID to filter tickers by
    """
    try:
        # Get ticker from database
        ticker = repo.get_by_symbol(symbol, user_id=user_id)
        if not ticker:
            st.error(f"Ticker {symbol} not found in database for current user")
            return
        
        ticker_id = ticker['id']
        
        # Initialize clients
        data_client = DataClient()
        cache_manager = CacheManager()
        
        # Check cache first
        cached_df = cache_manager.get_cached_data(ticker_id)
        
        if cached_df is not None and cache_manager.is_cache_valid(ticker_id):
            st.success(f"✅ Using cached data for {symbol}")
            df = cached_df
        else:
            # Fetch from API
            st.info(f"Fetching data from yfinance for {symbol}...")
            price_data = data_client.get_historical_prices(symbol, period='max')
            
            if not price_data:
                st.error(f"Failed to fetch data for {symbol}. Please check if the ticker is valid.")
                return
            
            # Convert to DataFrame
            df = pd.DataFrame(price_data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
            
            # Save to cache
            cache_manager.save_to_cache(ticker_id, price_data)
            
            # Update ticker's last_updated timestamp
            repo.update_last_updated(ticker_id)
            
            st.success(f"✅ Fetched {len(df)} price records")
        
        # Calculate indicators on full dataset (needed for accuracy)
        with st.spinner("Calculating technical indicators..."):
            calculator = IndicatorCalculator(df)
            df_with_indicators = calculator.calculate_all()
        
        st.success("✅ Indicators calculated")
        
        # Generate signals on full dataset
        with st.spinner("Generating trading signals..."):
            signal_generator = SignalGenerator(df_with_indicators)
            df_with_signals = signal_generator.generate_all_signals()
            df_with_labels = signal_generator.add_signal_labels()
        
        st.success("✅ Signals generated")
        
        # Filter data by date range for display
        from datetime import datetime, timedelta
        
        today = datetime.now()
        if date_range == '3 months':
            cutoff_date = today - timedelta(days=90)
        elif date_range == '6 months':
            cutoff_date = today - timedelta(days=180)
        elif date_range == '1 year':
            cutoff_date = today - timedelta(days=365)
        elif date_range == '2 years':
            cutoff_date = today - timedelta(days=730)
        else:  # 'All data'
            cutoff_date = df_with_labels['date'].min()
        
        # Filter dataframe
        df_filtered = df_with_labels[df_with_labels['date'] >= cutoff_date].copy()
        
        if len(df_filtered) == 0:
            st.warning(f"No data available for the selected date range ({date_range})")
            return
        
        st.info(f"📊 Displaying {len(df_filtered)} bars ({date_range})")
        
        # Get signal counts for the filtered period
        signal_counts = {
            'long_open': int(df_filtered['long_open'].sum()),
            'long_close': int(df_filtered['long_close'].sum()),
            'short_open': int(df_filtered['short_open'].sum()),
            'short_close': int(df_filtered['short_close'].sum())
        }
        
        # Display signal metrics (for filtered period)
        _display_signal_metrics(signal_counts)
        
        # Render chart with filtered data
        with st.spinner("Rendering chart..."):
            renderer = ChartRenderer(df_filtered, symbol)
            fig = renderer.render_full_chart()

        # Display chart with standard configuration
        st.plotly_chart(
            fig, 
            use_container_width=True,
            config={
                'displayModeBar': True,
                'displaylogo': False,
                'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
                'toImageButtonOptions': {
                    'format': 'png',
                    'filename': f'{symbol}_chart',
                    'height': 600,
                    'width': 1000,
                    'scale': 1
                }
            }
        )        # Display recent signals table (from filtered data)
        _display_recent_signals(df_filtered, symbol)
        
    except Exception as e:
        st.error(f"Error processing {symbol}: {str(e)}")
        logger.error(f"Error in _load_and_display_chart for {symbol}: {e}", exc_info=True)


def _display_signal_metrics(signal_counts: dict):
    """
    Display signal count metrics.
    
    Args:
        signal_counts: Dictionary with signal counts
    """
    st.markdown("### 📊 Signal Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🟢 Long OPEN",
            value=signal_counts.get('long_open', 0),
            help="Number of Long entry signals"
        )
    
    with col2:
        st.metric(
            label="🔴 Long CLOSE",
            value=signal_counts.get('long_close', 0),
            help="Number of Long exit signals"
        )
    
    with col3:
        st.metric(
            label="🟠 Short OPEN",
            value=signal_counts.get('short_open', 0),
            help="Number of Short entry signals"
        )
    
    with col4:
        st.metric(
            label="🔵 Short CLOSE",
            value=signal_counts.get('short_close', 0),
            help="Number of Short exit signals"
        )
    
    st.markdown("---")


def _display_recent_signals(df: pd.DataFrame, symbol: str):
    """
    Display table of recent signals with mobile optimization.
    
    Args:
        df: DataFrame with signals (filtered by date range)
        symbol: Ticker symbol
    """
    st.markdown("### 📋 Recent Signals (All in selected period)")
    
    # Filter rows with any signal
    signal_cols = ['long_open', 'long_close', 'short_open', 'short_close']
    df_signals = df[df[signal_cols].any(axis=1)].copy()
    
    if len(df_signals) == 0:
        st.info(f"No signals generated for {symbol} in the selected date range")
        return
    
    # Sort by date descending (latest first) - show ALL signals
    df_recent = df_signals.sort_values('date', ascending=False).copy()
    
    # Add mobile-friendly table container
    st.markdown('<div class="mobile-scroll">', unsafe_allow_html=True)
    
    # Create display DataFrame
    display_df = pd.DataFrame({
        'Date': df_recent['date'].dt.strftime('%Y-%m-%d'),
        'Close': df_recent['close'].round(2),
        'Long OPEN': df_recent['long_open'].map({True: '🟢', False: ''}),
        'Long CLOSE': df_recent['long_close'].map({True: '🔴', False: ''}),
        'Short OPEN': df_recent['short_open'].map({True: '🟠', False: ''}),
        'Short CLOSE': df_recent['short_close'].map({True: '🔵', False: ''})
    })
    
    # Display table with mobile optimization
    st.dataframe(
        display_df,
        width='stretch',
        hide_index=True,
        height=300  # Reduced height for mobile
    )
    
    # Close mobile-friendly container
    st.markdown('</div>', unsafe_allow_html=True)
