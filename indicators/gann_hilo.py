"""Gann HiLo Activator indicator implementation."""

import pandas as pd
import numpy as np
from typing import Tuple


def calculate_gann_hilo(df: pd.DataFrame, fast_period: int = 13, slow_period: int = 21) -> pd.DataFrame:
    """
    Calculate Gann HiLo Activator based on Pine Script implementation.
    
    Uses SMA of highs and lows to determine trend and support/resistance levels.
    
    Args:
        df: DataFrame with columns: high, low, close
        fast_period: HIGH period for SMA (default 13)
        slow_period: LOW period for SMA (default 21)
        
    Returns:
        DataFrame with gann_hilo and gann_direction columns
    """
    df = df.copy()
    
    # Calculate SMA of highs and lows (matching Pine Script)
    sma_high = df['high'].rolling(window=fast_period).mean()
    sma_low = df['low'].rolling(window=slow_period).mean()
    
    # Initialize gann_hilo series and direction
    gann_hilo = pd.Series(index=df.index, dtype=float)
    direction = np.zeros(len(df))
    
    # Initialize first value
    if len(df) > 0:
        gann_hilo.iloc[0] = df['close'].iloc[0]
        direction[0] = 1
    
    # Calculate Gann HiLo values matching Pine Script logic:
    # direction = 1 if close > sma_high[prev], -1 if close < sma_low[prev], else keep prev
    # value = sma_low if direction==1, sma_high if direction==-1
    for i in range(1, len(df)):
        prev_direction = direction[i-1]
        
        # Determine direction based on previous SMA levels
        if pd.notna(sma_high.iloc[i-1]) and df['close'].iloc[i] > sma_high.iloc[i-1]:
            # Close broke above SMA of highs - switch to uptrend
            direction[i] = 1
        elif pd.notna(sma_low.iloc[i-1]) and df['close'].iloc[i] < sma_low.iloc[i-1]:
            # Close broke below SMA of lows - switch to downtrend
            direction[i] = -1
        else:
            # No breakout - keep previous direction
            direction[i] = prev_direction
        
        # Set Gann HiLo value based on current direction
        if direction[i] == 1:
            # Uptrend: use SMA of lows as support
            gann_hilo.iloc[i] = sma_low.iloc[i] if pd.notna(sma_low.iloc[i]) else gann_hilo.iloc[i-1]
        else:
            # Downtrend: use SMA of highs as resistance
            gann_hilo.iloc[i] = sma_high.iloc[i] if pd.notna(sma_high.iloc[i]) else gann_hilo.iloc[i-1]
    
    df['gann_hilo'] = gann_hilo
    df['gann_direction'] = direction
    
    return df


def get_gann_trend(df: pd.DataFrame) -> pd.Series:
    """
    Get Gann HiLo trend direction.
    
    Args:
        df: DataFrame with gann_direction column
        
    Returns:
        Series with trend: 1 for uptrend, -1 for downtrend
    """
    if 'gann_direction' not in df.columns:
        return pd.Series(index=df.index, dtype=int)
    
    return df['gann_direction']
