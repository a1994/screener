"""
Alerts tab component for displaying trading signals dashboard.
Shows paginated, sortable list of alerts with refresh functionality.
"""

import streamlit as st
from typing import Optional
import math

from database.alert_repository import AlertRepository
from database.theme_repository import ThemeRepository
from alerts.refresher import AlertRefresher
from config.settings import DATABASE_PATH
from utils.mobile_responsive import mobile_friendly_columns, mobile_alert_card, mobile_metric_card


def render_alerts_tab(user_id: int = 1):
    """Render the Alerts tab with alert dashboard for a specific user.
    
    Args:
        user_id: User ID to filter alerts by
    """
    
    st.header("📊 Trading Alerts Dashboard")
    st.markdown("Monitor trading signals across all your tickers in one place.")
    
    # Initialize repositories
    alert_repo = AlertRepository(DATABASE_PATH)
    theme_repo = ThemeRepository()
    
    # Initialize session state for pagination, sorting, and filtering
    if 'alert_page' not in st.session_state:
        st.session_state.alert_page = 1
    if 'alert_sort_order' not in st.session_state:
        st.session_state.alert_sort_order = 'DESC'
    if 'alert_ticker_filter' not in st.session_state:
        st.session_state.alert_ticker_filter = ''
    if 'alert_theme_filter' not in st.session_state:
        st.session_state.alert_theme_filter = ''
    
    # Get user themes for dropdown
    user_themes = theme_repo.get_user_themes(user_id)
    theme_options = ["All Themes"] + [theme['name'] for theme in user_themes]
    
    # Controls row - mobile responsive
    col1, col2, col3, col4 = mobile_friendly_columns(4)
    
    with col1:
        # Sort order selector
        sort_option = st.selectbox(
            'Sort by Date',
            options=['Latest First', 'Oldest First'],
            index=0 if st.session_state.alert_sort_order == 'DESC' else 1,
            key='alert_sort_selector'
        )
        
        # Update sort order in session state
        new_sort_order = 'DESC' if sort_option == 'Latest First' else 'ASC'
        if new_sort_order != st.session_state.alert_sort_order:
            st.session_state.alert_sort_order = new_sort_order
            st.session_state.alert_page = 1  # Reset to first page
            st.rerun()
    
    with col2:
        # Theme filter dropdown
        current_theme_index = 0
        if st.session_state.alert_theme_filter and st.session_state.alert_theme_filter in theme_options:
            current_theme_index = theme_options.index(st.session_state.alert_theme_filter)
        
        selected_theme = st.selectbox(
            'Filter by Theme',
            options=theme_options,
            index=current_theme_index,
            key='alert_theme_selector',
            help='Select theme to filter alerts, or "All Themes" to show all'
        )
        
        # Update theme filter and clear ticker filter when theme changes
        if selected_theme != st.session_state.alert_theme_filter:
            st.session_state.alert_theme_filter = selected_theme
            st.session_state.alert_ticker_filter = ''  # Clear ticker filter when theme changes
            st.session_state.alert_page = 1  # Reset to first page
            st.rerun()
    
    with col3:
        # Ticker filter input (only show if "All Themes" is selected)
        if st.session_state.alert_theme_filter == "All Themes" or not st.session_state.alert_theme_filter:
            ticker_filter = st.text_input(
                'Filter by Ticker',
                value=st.session_state.alert_ticker_filter,
                placeholder='e.g., AAPL, MSFT',
                help='Enter ticker symbol to filter alerts'
            )
            
            # Update filter in session state
            if ticker_filter != st.session_state.alert_ticker_filter:
                st.session_state.alert_ticker_filter = ticker_filter
                st.session_state.alert_page = 1  # Reset to first page
                st.rerun()
        else:
            st.markdown(f"**Selected Theme:** `{st.session_state.alert_theme_filter}`")
    
    with col4:
        # Refresh All button
        if st.button('🔄 Refresh Alerts', type='primary', use_container_width=True, key='alerts_refresh_btn'):
            # Get selected theme ID if theme is selected
            selected_theme_id = None
            if st.session_state.alert_theme_filter and st.session_state.alert_theme_filter != "All Themes":
                for theme in user_themes:
                    if theme['name'] == st.session_state.alert_theme_filter:
                        selected_theme_id = theme['id']
                        break
            _refresh_user_alerts(user_id, selected_theme_id)
    
    st.markdown("---")
    
    # Get alerts with pagination, sorting, and filtering
    page_size = 20
    try:
        # Determine theme_id for filtering
        theme_id = None
        if st.session_state.alert_theme_filter and st.session_state.alert_theme_filter != "All Themes":
            for theme in user_themes:
                if theme['name'] == st.session_state.alert_theme_filter:
                    theme_id = theme['id']
                    break
        
        alerts = alert_repo.get_all(
            page=st.session_state.alert_page,
            page_size=page_size,
            sort_order=st.session_state.alert_sort_order,
            ticker_filter=st.session_state.alert_ticker_filter or None,
            user_id=user_id,
            theme_id=theme_id
        )
        total_count = alert_repo.get_total_count(
            ticker_filter=st.session_state.alert_ticker_filter or None,
            user_id=user_id,
            theme_id=theme_id
        )
    except Exception as e:
        st.error(f"Error loading alerts: {str(e)}")
        return
    
    # Display alerts
    if not alerts:
        st.info("📭 No alerts for current user yet. Add tickers to your dashboard and refresh alerts.")
        return
    
    # Alert summary metrics
    _display_alert_metrics(alerts, total_count)
    
    st.markdown("---")
    
    # Alert table
    _display_alert_table(alerts)
    
    st.markdown("---")
    
    # Pagination controls
    _display_pagination(total_count, page_size)


def _display_alert_metrics(alerts: list, total_count: int):
    """Display alert summary metrics."""
    
    # Count by alert type from all alerts (not just current page)
    alert_repo = AlertRepository(DATABASE_PATH)
    
    # Get counts for all alerts matching current filters
    try:
        all_alerts = alert_repo.get_all(
            page=1, 
            page_size=10000,  # Get all for counting
            sort_order=st.session_state.alert_sort_order,
            ticker_filter=st.session_state.alert_ticker_filter or None,
            user_id=1  # Current user
        )
        
        long_open = sum(1 for a in all_alerts if a['alert_type'] == 'LONG_OPEN')
        long_close = sum(1 for a in all_alerts if a['alert_type'] == 'LONG_CLOSE')
        short_open = sum(1 for a in all_alerts if a['alert_type'] == 'SHORT_OPEN')
        short_close = sum(1 for a in all_alerts if a['alert_type'] == 'SHORT_CLOSE')
        
    except Exception:
        # Fallback to current page counts
        long_open = sum(1 for a in alerts if a['alert_type'] == 'LONG_OPEN')
        long_close = sum(1 for a in alerts if a['alert_type'] == 'LONG_CLOSE')
        short_open = sum(1 for a in alerts if a['alert_type'] == 'SHORT_OPEN')
        short_close = sum(1 for a in alerts if a['alert_type'] == 'SHORT_CLOSE')
    
    # Display metrics with cleaner styling
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📊 Total Alerts", total_count)
    
    with col2:
        st.metric("🟢 Long Open", long_open)
    
    with col3:
        st.metric("🔴 Long Close", long_close)
    
    with col4:
        st.metric("🟠 Short Open", short_open)
    
    with col5:
        st.metric("🟣 Short Close", short_close)


def _display_alert_table(alerts: list):
    """Display alerts in a clean formatted table."""
    
    # Custom CSS for table styling
    st.markdown("""
    <style>
    .alerts-table {
        width: 100%;
        max-width: 100%;
        margin-top: 1rem;
    }
    .alert-row {
        display: grid;
        grid-template-columns: minmax(80px, 1fr) minmax(120px, 1.5fr) minmax(120px, 1.5fr) minmax(100px, 1.2fr) minmax(140px, 1.8fr);
        gap: 1rem;
        padding: 0.75rem 1rem;
        border-bottom: 1px solid #333;
        background: transparent;
        color: white;
        align-items: center;
        width: 100%;
    }
    .alert-header {
        display: grid;
        grid-template-columns: minmax(80px, 1fr) minmax(120px, 1.5fr) minmax(120px, 1.5fr) minmax(100px, 1.2fr) minmax(140px, 1.8fr);
        gap: 1rem;
        padding: 1rem;
        font-weight: bold;
        color: white;
        background: transparent;
        border-bottom: 2px solid #666;
        width: 100%;
    }
    .ticker-cell {
        color: #4ade80;
        font-weight: 600;
        font-family: monospace;
    }
    .alert-type {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-weight: 500;
    }
    .long-open { color: #4ade80; }
    .long-close { color: #f87171; }
    .short-open { color: #fb923c; }
    .short-close { color: #a78bfa; }
    .price-cell {
        font-family: monospace;
        font-weight: 500;
    }
    .date-cell {
        font-size: 0.9rem;
        color: #d1d5db;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("## Recent Alerts")
    
    # Table container
    st.markdown('<div class="alerts-table">', unsafe_allow_html=True)
    
    # Header row
    st.markdown("""
    <div class="alert-header">
        <div>Ticker</div>
        <div>Alert Type</div>
        <div>Signal Date</div>
        <div>Price</div>
        <div>Created</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Alert rows
    for alert in alerts:
        # Format alert type with emoji and color
        alert_type = alert['alert_type']
        if alert_type == 'LONG_OPEN':
            type_display = '<span class="long-open">🟢 Long Open</span>'
        elif alert_type == 'LONG_CLOSE':
            type_display = '<span class="long-close">🔴 Long Close</span>'
        elif alert_type == 'SHORT_OPEN':
            type_display = '<span class="short-open">🟠 Short Open</span>'
        elif alert_type == 'SHORT_CLOSE':
            type_display = '<span class="short-close">🟣 Short Close</span>'
        else:
            type_display = f'<span>{alert_type}</span>'
        
        # Format price
        price_display = f"${alert['price']:.2f}"
        
        # Format dates
        signal_date = alert['signal_date']
        created_date = alert['created_at'][:16] if len(alert['created_at']) > 16 else alert['created_at']
        
        st.markdown(f"""
        <div class="alert-row">
            <div class="ticker-cell">{alert['ticker_symbol']}</div>
            <div class="alert-type">{type_display}</div>
            <div class="date-cell">{signal_date}</div>
            <div class="price-cell">{price_display}</div>
            <div class="date-cell">{created_date}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)


def _display_pagination(total_count: int, page_size: int):
    """Display pagination controls."""
    
    total_pages = math.ceil(total_count / page_size)
    
    if total_pages <= 1:
        return
    
    col1, col2, col3, col4, col5 = st.columns([2, 1, 2, 1, 2])
    
    with col1:
        if st.button('⏮️ First', disabled=(st.session_state.alert_page == 1), key='alerts_first_btn'):
            st.session_state.alert_page = 1
            st.rerun()
    
    with col2:
        if st.button('◀️ Prev', disabled=(st.session_state.alert_page == 1), key='alerts_prev_btn'):
            st.session_state.alert_page -= 1
            st.rerun()
    
    with col3:
        st.markdown(
            f"<div style='text-align: center; padding: 8px;'>Page {st.session_state.alert_page} of {total_pages}</div>",
            unsafe_allow_html=True
        )
    
    with col4:
        if st.button('Next ▶️', disabled=(st.session_state.alert_page == total_pages), key='alerts_next_btn'):
            st.session_state.alert_page += 1
            st.rerun()
    
    with col5:
        if st.button('Last ⏭️', disabled=(st.session_state.alert_page == total_pages), key='alerts_last_btn'):
            st.session_state.alert_page = total_pages
            st.rerun()


def _refresh_user_alerts(user_id: int, theme_id: Optional[int] = None):
    """Refresh alerts for current user's tickers with progress tracking.
    
    Args:
        user_id: User ID to refresh alerts for
        theme_id: Optional theme ID to filter tickers by theme
    """
    
    # Create refresher
    refresher = AlertRefresher(DATABASE_PATH)
    
    # Progress container
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    def progress_callback(current: int, total: int, ticker_symbol: str):
        """Update progress bar and status text."""
        progress = current / total
        progress_bar.progress(progress)
        status_text.text(f"Processing {current}/{total}: {ticker_symbol}")
    
    # Run refresh
    try:
        stats = refresher.refresh_all(progress_callback=progress_callback, user_id=user_id, theme_id=theme_id)
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        # Show results
        summary = refresher.get_refresh_summary(stats)
        
        if stats['failed'] == 0:
            st.success(f"✅ {summary}")
        else:
            st.warning(f"⚠️ {summary}")
        
        # Reset to first page
        st.session_state.alert_page = 1
        
        # Rerun to show updated alerts
        st.rerun()
        
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"Error refreshing alerts: {str(e)}")
