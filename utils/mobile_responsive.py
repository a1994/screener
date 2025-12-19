"""
Mobile responsive utilities for Streamlit app - DISABLED
All mobile responsive features have been reverted to ensure stability.
"""

import streamlit as st


def inject_mobile_css():
    """Inject minimal CSS - mobile responsive disabled."""
    # No mobile CSS modifications - keeping original desktop experience
    pass


def setup_mobile_app():
    """Setup mobile app configuration - DISABLED."""
    # No mobile-specific configuration
    pass


def mobile_friendly_columns(num_cols: int, mobile_stack: bool = True):
    """
    Create standard column layouts.
    
    Args:
        num_cols: Number of columns
        mobile_stack: Ignored - no mobile modifications
    
    Returns:
        Streamlit columns object
    """
    return st.columns(num_cols)


def mobile_friendly_form():
    """Create standard form - no mobile modifications."""
    return st.form


def mobile_metric_card(title: str, value: str, delta: str = None, help_text: str = None):
    """
    Create a standard metric card.
    
    Args:
        title: Metric title
        value: Metric value
        delta: Change indicator (optional)
        help_text: Help tooltip (optional)
    """
    st.metric(
        label=title,
        value=value,
        delta=delta,
        help=help_text
    )


def mobile_alert_card(ticker: str, alert_type: str, price: str, date: str):
    """
    Create a standard alert card.
    
    Args:
        ticker: Stock ticker symbol
        alert_type: Type of alert
        price: Price at alert
        date: Alert date
    """
    # Standard alert display
    alert_emoji = {
        'LONG_OPEN': '🟢',
        'LONG_CLOSE': '🔴', 
        'SHORT_OPEN': '🟠',
        'SHORT_CLOSE': '🔵'
    }.get(alert_type, '📊')
    
    st.info(f"{alert_emoji} **{ticker}** - {alert_type} at ${price} on {date}")


def mobile_data_table(df, height=300):
    """Display standard data table - no mobile modifications."""
    return st.dataframe(df, height=height, use_container_width=True)


def mobile_scroll_container():
    """Return standard container - no mobile scroll modifications."""
    return st.container()