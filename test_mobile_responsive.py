#!/usr/bin/env python3
"""
Test mobile responsive features for the stock screener app.
"""

import streamlit as st
from utils.mobile_responsive import (
    inject_mobile_css, 
    mobile_friendly_columns, 
    mobile_metric_card, 
    mobile_alert_card,
    mobile_data_table,
    mobile_navigation_menu,
    mobile_progress_indicator
)

def test_mobile_components():
    """Test mobile responsive components."""
    
    st.title("📱 Mobile Responsive Test Page")
    
    # Inject mobile CSS
    inject_mobile_css()
    
    st.markdown("---")
    
    # Test 1: Mobile-friendly columns
    st.subheader("1. Mobile-Friendly Column Layouts")
    
    # 4-column layout that stacks on mobile
    col1, col2, col3, col4 = mobile_friendly_columns(4)
    
    with col1:
        st.button("Button 1", use_container_width=True)
    with col2:
        st.button("Button 2", use_container_width=True)
    with col3:
        st.button("Button 3", use_container_width=True)
    with col4:
        st.button("Button 4", use_container_width=True)
    
    st.markdown("---")
    
    # Test 2: Mobile metric cards
    st.subheader("2. Mobile-Optimized Metric Cards")
    
    col1, col2 = mobile_friendly_columns(2)
    
    with col1:
        mobile_metric_card("Total Tickers", "42", "+5", "Active tickers in portfolio")
        mobile_metric_card("Alerts Today", "8", "+3", "New alerts generated")
    
    with col2:
        mobile_metric_card("Portfolio Value", "$12,450", "+2.3%", "Current market value")
        mobile_metric_card("Success Rate", "73%", "+1.2%", "Signal accuracy")
    
    st.markdown("---")
    
    # Test 3: Mobile alert cards
    st.subheader("3. Mobile-Friendly Alert Cards")
    
    sample_alerts = [
        {"ticker": "AAPL", "type": "LONG_OPEN", "price": "175.25", "date": "2025-12-18"},
        {"ticker": "MSFT", "type": "SHORT_OPEN", "price": "420.15", "date": "2025-12-18"},
        {"ticker": "GOOGL", "type": "LONG_CLOSE", "price": "2850.75", "date": "2025-12-17"},
    ]
    
    for alert in sample_alerts:
        mobile_alert_card(
            ticker=alert["ticker"],
            alert_type=alert["type"], 
            price=alert["price"],
            date=alert["date"]
        )
    
    st.markdown("---")
    
    # Test 4: Mobile navigation
    st.subheader("4. Mobile Navigation Menu")
    
    nav_options = ["Dashboard", "Add Tickers", "Chart Analysis", "Alerts", "Settings"]
    selected = mobile_navigation_menu(nav_options, key="test_nav")
    st.write(f"Selected: {selected}")
    
    st.markdown("---")
    
    # Test 5: Mobile progress indicator
    st.subheader("5. Mobile Progress Indicator")
    
    mobile_progress_indicator(7, 10, "Processing alerts...")
    
    st.markdown("---")
    
    # Test 6: Form inputs
    st.subheader("6. Mobile-Friendly Form Inputs")
    
    # Text input
    ticker_input = st.text_input("Enter Ticker Symbol", placeholder="e.g., AAPL")
    
    # Select boxes
    col1, col2 = mobile_friendly_columns(2)
    with col1:
        theme = st.selectbox("Select Theme", ["Tech Stocks", "Blue Chips", "Growth"])
    with col2:
        period = st.selectbox("Time Period", ["1D", "1W", "1M", "3M", "1Y"])
    
    # Buttons
    col1, col2, col3 = mobile_friendly_columns(3)
    with col1:
        if st.button("Add Ticker", use_container_width=True):
            st.success("Ticker added!")
    with col2:
        if st.button("Refresh Data", use_container_width=True):
            st.info("Refreshing...")
    with col3:
        if st.button("Generate Alerts", use_container_width=True):
            st.warning("Processing...")
    
    st.markdown("---")
    
    # Test 7: Data display
    st.subheader("7. Mobile Data Display")
    
    import pandas as pd
    
    # Sample data
    sample_data = pd.DataFrame({
        'Symbol': ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN'],
        'Price': ['$175.25', '$420.15', '$2850.75', '$245.80', '$3125.50'],
        'Change': ['+2.3%', '-0.5%', '+1.8%', '+5.2%', '-1.1%'],
        'Volume': ['45.2M', '28.7M', '12.3M', '85.1M', '22.9M']
    })
    
    mobile_data_table(sample_data, max_rows_mobile=3)
    
    st.markdown("---")
    
    # Test 8: Responsive info boxes
    st.subheader("8. Mobile Info Display")
    
    st.info("📱 **Mobile Tip**: This app is optimized for mobile devices. Rotate your device for the best experience!")
    st.success("✅ **Responsive Design**: Layout adapts automatically to your screen size.")
    st.warning("⚠️ **Performance**: Some features may load slower on mobile networks.")
    st.error("❌ **Limitations**: Advanced charting works best on desktop browsers.")
    
    # Footer info
    st.markdown("---")
    st.markdown(
        """
        ### 📱 Mobile Optimization Features:
        - **Responsive Layout**: Automatically adapts to screen size
        - **Touch-Friendly**: Large buttons and touch targets
        - **Readable Text**: Optimized font sizes and spacing
        - **Fast Loading**: Compressed assets and efficient rendering
        - **Offline Support**: Key features work without internet
        - **Swipe Navigation**: Natural mobile gestures
        
        **Best viewed on**: Mobile browsers, tablets, desktop
        """
    )

if __name__ == "__main__":
    test_mobile_components()