#!/usr/bin/env python3
"""
Quick mobile test for the stock screener - simplified chart display.
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.mobile_responsive import inject_mobile_css, mobile_friendly_columns, mobile_alert_card

def generate_sample_data():
    """Generate sample stock data for testing."""
    dates = pd.date_range(start='2025-10-01', end='2025-12-18', freq='D')
    dates = dates[dates.dayofweek < 5]  # Remove weekends
    
    np.random.seed(42)
    price = 100
    prices = []
    volumes = []
    
    for _ in dates:
        price += np.random.normal(0, 2)
        price = max(50, min(200, price))  # Keep price reasonable
        prices.append(price)
        volumes.append(np.random.randint(1000000, 10000000))
    
    return pd.DataFrame({
        'date': dates,
        'open': [p + np.random.normal(0, 0.5) for p in prices],
        'high': [p + abs(np.random.normal(2, 1)) for p in prices],
        'low': [p - abs(np.random.normal(2, 1)) for p in prices],
        'close': prices,
        'volume': volumes
    })

def create_mobile_chart(df):
    """Create a mobile-optimized chart matching the main app."""
    # Match the main app subplot configuration
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,  # Match main app spacing
        row_heights=[0.70, 0.30],  # Match main app ratio
        subplot_titles=('AAPL - Price & Indicators', 'Volume'),
        specs=[[{"secondary_y": False}], [{"secondary_y": False}]]
    )
    
    # Add candlestick
    fig.add_trace(go.Candlestick(
        x=df['date'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='AAPL Price',
        increasing_line_color='#26a69a',
        decreasing_line_color='#ef5350'
    ), row=1, col=1)
    
    # Color volume bars by price change (like main app)
    colors = ['#ef5350' if row['close'] < row['open'] else '#26a69a' 
              for _, row in df.iterrows()]
    
    # Add volume bars with improved visibility
    fig.add_trace(go.Bar(
        x=df['date'],
        y=df['volume'],
        name='Volume',
        marker_color=colors,
        opacity=0.8,
        showlegend=False,
        hovertemplate='<b>%{x}</b><br>Volume: %{y:,.0f}<extra></extra>'
    ), row=2, col=1)
    
    # Match main app layout with improved legend
    fig.update_layout(
        title=dict(
            text='AAPL - Mobile Chart Test',
            font=dict(size=18, color='#333'),
            x=0.5,
            y=0.98
        ),
        xaxis_rangeslider_visible=False,
        hovermode='x unified',
        height=580,  # Match main app height with lower legend
        template='plotly_white',
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.18,  # Match main app legend position
            xanchor='center',
            x=0.5,
            font=dict(size=10, color='#333333'),  # Larger, darker text
            bgcolor='rgba(248,249,250,0.98)',  # Light gray background
            bordercolor='#dee2e6',
            borderwidth=1,
            itemsizing='constant',
            itemwidth=30,
            tracegroupgap=10
        ),
        margin=dict(l=50, r=50, t=80, b=140),  # Match main app margins
        font=dict(size=11),
        autosize=True
    )
    
    # Update axes with better formatting
    fig.update_xaxes(title_text="Date", row=2, col=1, title_font_size=12, tickfont_size=10)
    fig.update_yaxes(title_text="Price ($)", row=1, col=1, title_font_size=12, tickfont_size=10)
    fig.update_yaxes(title_text="Volume", row=2, col=1, title_font_size=12, tickfont_size=10)
    
    return fig

def main():
    """Main mobile test interface."""
    
    st.set_page_config(
        page_title="Mobile Chart Test",
        page_icon="📱",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Inject mobile CSS
    inject_mobile_css()
    
    st.title("📱 Mobile Responsiveness Test")
    st.markdown("**Test the mobile experience of charts and components**")
    
    # Mobile-friendly columns test
    st.subheader("1. Column Layout Test")
    col1, col2, col3 = mobile_friendly_columns(3)
    
    with col1:
        st.button("Button 1", width='stretch')
    with col2:
        st.selectbox("Period", ["1D", "1W", "1M"])
    with col3:
        st.button("Refresh", width='stretch')
    
    st.markdown("---")
    
    # Chart test
    st.subheader("2. Chart Responsiveness Test")
    
    # Generate sample data
    df = generate_sample_data()
    
    # Create and display mobile chart
    fig = create_mobile_chart(df)
    
    st.markdown('<div class="mobile-scroll">', unsafe_allow_html=True)
    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
            'toImageButtonOptions': {
                'format': 'png',
                'filename': 'mobile_test_chart',
                'height': 550,
                'width': 800,
                'scale': 1
            }
        }
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Alert cards test
    st.subheader("3. Alert Cards Test")
    
    sample_alerts = [
        {"ticker": "AAPL", "type": "LONG_OPEN", "price": "175.25", "date": "2025-12-18"},
        {"ticker": "MSFT", "type": "SHORT_OPEN", "price": "420.15", "date": "2025-12-17"},
        {"ticker": "GOOGL", "type": "LONG_CLOSE", "price": "2850.75", "date": "2025-12-16"},
    ]
    
    for alert in sample_alerts:
        mobile_alert_card(
            ticker=alert["ticker"],
            alert_type=alert["type"],
            price=alert["price"],
            date=alert["date"]
        )
    
    st.markdown("---")
    
    # Data table test
    st.subheader("4. Data Table Test")
    
    sample_data = pd.DataFrame({
        'Symbol': ['AAPL', 'MSFT', 'GOOGL', 'TSLA'],
        'Price': ['$175.25', '$420.15', '$2850.75', '$245.80'],
        'Change': ['+2.3%', '-0.5%', '+1.8%', '+5.2%'],
        'Volume': ['45.2M', '28.7M', '12.3M', '85.1M'],
        'Signal': ['🟢 LONG', '🟠 SHORT', '🔴 CLOSE', '🟢 LONG']
    })
    
    st.markdown('<div class="mobile-scroll">', unsafe_allow_html=True)
    st.dataframe(sample_data, width='stretch', height=200)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Mobile instructions
    st.subheader("5. Mobile Testing Instructions")
    
    st.info("""
    **📱 How to test mobile view:**
    
    **Option 1 - Browser DevTools:**
    1. Press F12 to open developer tools
    2. Click the device toggle button (📱)
    3. Select different mobile devices from dropdown
    4. Test iPhone, Android, iPad sizes
    
    **Option 2 - Manual Resize:**
    1. Drag your browser window to make it narrow
    2. Test different widths (320px, 480px, 768px)
    
    **Option 3 - Real Device:**
    1. Open this URL on your phone/tablet
    2. Test touch interactions and scrolling
    
    **What to check:**
    - ✅ Charts fit the screen width
    - ✅ Buttons are touch-friendly (44px minimum)
    - ✅ Text is readable without zooming
    - ✅ Tables scroll horizontally if needed
    - ✅ Layout stacks vertically on narrow screens
    """)
    
    # Performance info
    st.success("""
    **✨ Mobile Optimizations Applied:**
    - Responsive CSS for all screen sizes
    - Touch-friendly button sizes
    - Optimized chart dimensions
    - Horizontal scrolling for tables
    - Compressed layouts for mobile
    - Fast loading and efficient rendering
    """)

if __name__ == "__main__":
    main()