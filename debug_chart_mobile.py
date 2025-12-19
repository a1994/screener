#!/usr/bin/env python3
"""
Simple chart test for mobile debugging
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def test_simple_chart():
    """Create a very simple chart to test mobile rendering."""
    
    st.title("📱 Simple Chart Test")
    
    # Generate simple test data
    dates = pd.date_range(start='2025-12-01', end='2025-12-18', freq='D')
    np.random.seed(42)
    
    prices = []
    price = 100
    for _ in dates:
        price += np.random.normal(0, 1)
        prices.append(price)
    
    df = pd.DataFrame({
        'date': dates,
        'price': prices
    })
    
    st.write(f"Data shape: {df.shape}")
    st.write("Sample data:")
    st.dataframe(df.head())
    
    # Create very simple line chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['price'],
        mode='lines',
        name='Price',
        line=dict(color='blue', width=2)
    ))
    
    fig.update_layout(
        title="Simple Price Chart",
        height=300,
        template='plotly_white',
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False
    )
    
    try:
        st.plotly_chart(fig, use_container_width=True, height=300)
        st.success("✅ Simple chart rendered successfully!")
    except Exception as e:
        st.error(f"Chart error: {str(e)}")
    
    # Test with Streamlit native chart
    st.subheader("Streamlit Native Chart:")
    try:
        st.line_chart(df.set_index('date')['price'])
        st.success("✅ Streamlit native chart works!")
    except Exception as e:
        st.error(f"Native chart error: {str(e)}")

if __name__ == "__main__":
    st.set_page_config(
        page_title="Chart Test",
        page_icon="📊",
        layout="wide"
    )
    test_simple_chart()