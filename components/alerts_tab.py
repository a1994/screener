"""
Alerts tab component for displaying trading signals dashboard.
Shows paginated, sortable list of alerts with refresh functionality.
"""

import streamlit as st
from typing import Optional
import math

from database.alert_repository import AlertRepository
from alerts.refresher import AlertRefresher
from config.settings import DATABASE_PATH, FMP_API_KEY


def render_alerts_tab():
    """Render the Alerts tab with alert dashboard."""
    
    st.header("📊 Trading Alerts Dashboard")
    st.markdown("Monitor trading signals across all your tickers in one place.")
    
    # Initialize repository
    alert_repo = AlertRepository(DATABASE_PATH)
    
    # Initialize session state for pagination and sorting
    if 'alert_page' not in st.session_state:
        st.session_state.alert_page = 1
    if 'alert_sort_order' not in st.session_state:
        st.session_state.alert_sort_order = 'DESC'
    
    # Controls row
    col1, col2, col3 = st.columns([2, 2, 3])
    
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
        # Refresh All button
        if st.button('🔄 Refresh All Alerts', type='primary', use_container_width=True):
            _refresh_all_alerts()
    
    with col3:
        st.empty()  # Spacer
    
    st.markdown("---")
    
    # Get alerts with pagination
    page_size = 20
    try:
        alerts = alert_repo.get_all(
            page=st.session_state.alert_page,
            page_size=page_size,
            sort_order=st.session_state.alert_sort_order
        )
        total_count = alert_repo.get_total_count()
    except Exception as e:
        st.error(f"Error loading alerts: {str(e)}")
        return
    
    # Display alerts
    if not alerts:
        st.info("📭 No alerts yet. Add tickers to your dashboard and refresh alerts.")
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
    
    # Count by alert type
    long_open = sum(1 for a in alerts if a['alert_type'] == 'LONG_OPEN')
    long_close = sum(1 for a in alerts if a['alert_type'] == 'LONG_CLOSE')
    short_open = sum(1 for a in alerts if a['alert_type'] == 'SHORT_OPEN')
    short_close = sum(1 for a in alerts if a['alert_type'] == 'SHORT_CLOSE')
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Alerts", total_count)
    
    with col2:
        st.metric("🟢 Long Open", long_open)
    
    with col3:
        st.metric("🔴 Long Close", long_close)
    
    with col4:
        st.metric("🟠 Short Open", short_open)
    
    with col5:
        st.metric("🟣 Short Close", short_close)


def _display_alert_table(alerts: list):
    """Display alerts in a formatted table."""
    
    st.subheader("Recent Alerts")
    
    # Create table header
    header_cols = st.columns([2, 2, 3, 2, 2])
    headers = ['Ticker', 'Alert Type', 'Signal Date', 'Price', 'Created']
    
    for col, header in zip(header_cols, headers):
        col.markdown(f"**{header}**")
    
    st.markdown("---")
    
    # Display each alert
    for alert in alerts:
        cols = st.columns([2, 2, 3, 2, 2])
        
        # Ticker symbol
        cols[0].markdown(f"`{alert['ticker_symbol']}`")
        
        # Alert type with color coding
        alert_type = alert['alert_type']
        if alert_type == 'LONG_OPEN':
            cols[1].markdown("🟢 **Long Open**")
        elif alert_type == 'LONG_CLOSE':
            cols[1].markdown("🔴 Long Close")
        elif alert_type == 'SHORT_OPEN':
            cols[1].markdown("🟠 **Short Open**")
        elif alert_type == 'SHORT_CLOSE':
            cols[1].markdown("🟣 Short Close")
        
        # Signal date
        cols[2].markdown(alert['signal_date'])
        
        # Price
        cols[3].markdown(f"${alert['price']:.2f}")
        
        # Created at (show date only)
        created_date = alert['created_at'].split(' ')[0] if ' ' in alert['created_at'] else alert['created_at']
        cols[4].markdown(created_date)
        
        st.markdown("")  # Add spacing


def _display_pagination(total_count: int, page_size: int):
    """Display pagination controls."""
    
    total_pages = math.ceil(total_count / page_size)
    
    if total_pages <= 1:
        return
    
    col1, col2, col3, col4, col5 = st.columns([2, 1, 2, 1, 2])
    
    with col1:
        if st.button('⏮️ First', disabled=(st.session_state.alert_page == 1)):
            st.session_state.alert_page = 1
            st.rerun()
    
    with col2:
        if st.button('◀️ Prev', disabled=(st.session_state.alert_page == 1)):
            st.session_state.alert_page -= 1
            st.rerun()
    
    with col3:
        st.markdown(
            f"<div style='text-align: center; padding: 8px;'>Page {st.session_state.alert_page} of {total_pages}</div>",
            unsafe_allow_html=True
        )
    
    with col4:
        if st.button('Next ▶️', disabled=(st.session_state.alert_page == total_pages)):
            st.session_state.alert_page += 1
            st.rerun()
    
    with col5:
        if st.button('Last ⏭️', disabled=(st.session_state.alert_page == total_pages)):
            st.session_state.alert_page = total_pages
            st.rerun()


def _refresh_all_alerts():
    """Refresh alerts for all tickers with progress tracking."""
    
    # Create refresher
    refresher = AlertRefresher(FMP_API_KEY, DATABASE_PATH)
    
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
        stats = refresher.refresh_all(progress_callback=progress_callback)
        
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
