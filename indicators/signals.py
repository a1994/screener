"""Trading signal generation based on Pine Script strategy."""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class SignalGenerator:
    """Generates trading signals based on technical indicators."""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize signal generator with indicator data.
        
        Args:
            df: DataFrame with all calculated indicators
        """
        self.df = df.copy()
    
    def generate_all_signals(self) -> pd.DataFrame:
        """
        Generate all trading signals with proper position tracking.
        Ensures that OPEN and CLOSE signals are balanced (can't close without opening).
        
        Returns:
            DataFrame with signal columns added
        """
        try:
            # First detect raw conditions
            long_open_conditions = self._detect_long_open()
            long_close_conditions = self._detect_long_close()
            short_open_conditions = self._detect_short_open()
            short_close_conditions = self._detect_short_close()
            
            # Now apply state-based logic
            self._apply_position_tracking(
                long_open_conditions,
                long_close_conditions,
                short_open_conditions,
                short_close_conditions
            )
            
            logger.info(f"Generated signals: {self.get_signal_counts()}")
            return self.df
            
        except Exception as e:
            logger.error(f"Error generating signals: {e}")
            raise
    
    def _apply_position_tracking(
        self,
        long_open_cond: pd.Series,
        long_close_cond: pd.Series,
        short_open_cond: pd.Series,
        short_close_cond: pd.Series
    ):
        """
        Apply position tracking logic to ensure balanced signals.
        
        Rules:
        - Can only CLOSE a position that was OPENED
        - Can't open LONG while LONG is already open
        - Can't open SHORT while SHORT is already open
        - Opening LONG automatically closes SHORT (if open)
        - Opening SHORT automatically closes LONG (if open)
        """
        # Initialize signal columns
        self.df['long_open'] = False
        self.df['long_close'] = False
        self.df['short_open'] = False
        self.df['short_close'] = False
        
        # Position state: None, 'LONG', or 'SHORT'
        position = None
        
        for i in range(len(self.df)):
            # Check for LONG OPEN signal
            if long_open_cond.iloc[i] and position != 'LONG':
                self.df.loc[self.df.index[i], 'long_open'] = True
                # If SHORT was open, close it first
                if position == 'SHORT':
                    self.df.loc[self.df.index[i], 'short_close'] = True
                position = 'LONG'
                continue
            
            # Check for LONG CLOSE signal (only if LONG is open)
            if long_close_cond.iloc[i] and position == 'LONG':
                self.df.loc[self.df.index[i], 'long_close'] = True
                position = None
                continue
            
            # Check for SHORT OPEN signal
            if short_open_cond.iloc[i] and position != 'SHORT':
                self.df.loc[self.df.index[i], 'short_open'] = True
                # If LONG was open, close it first
                if position == 'LONG':
                    self.df.loc[self.df.index[i], 'long_close'] = True
                position = 'SHORT'
                continue
            
            # Check for SHORT CLOSE signal (only if SHORT is open)
            if short_close_cond.iloc[i] and position == 'SHORT':
                self.df.loc[self.df.index[i], 'short_close'] = True
                position = None
                continue
    
    def _detect_long_open(self) -> pd.Series:
        """
        Detect Long OPEN signals.
        
        All 5 conditions must be TRUE:
        - MACD > MACD Signal (condition6a)
        - Close > Gann HiLo (condition8)
        - RSI > RSI MA (condition11)
        - Close > Supertrend (condition2)
        - Close > Previous High (condition5)
        """
        return (
            (self.df['macd'] > self.df['macd_signal']) &
            (self.df['close'] > self.df['gann_hilo']) &
            (self.df['rsi'] > self.df['rsi_ma']) &
            (self.df['close'] > self.df['supertrend']) &
            (self.df['close'] > self.df['high'].shift(1))
        ).fillna(False)
    
    def _detect_long_close(self) -> pd.Series:
        """
        Detect Long CLOSE signals.
        
        Any of 3 conditions triggers exit:
        - Close < Gann HiLo (condition_exit6)
        - MACD < MACD Signal (condition_exit5)
        - Price in Ichimoku Cloud (candleinthecloud)
        """
        # Check if price is in Ichimoku cloud
        in_cloud = self._is_in_ichimoku_cloud()
        
        return (
            (self.df['close'] < self.df['gann_hilo']) |
            (self.df['macd'] < self.df['macd_signal']) |
            in_cloud
        ).fillna(False)
    
    def _detect_short_open(self) -> pd.Series:
        """
        Detect Short OPEN signals.
        
        All 6 conditions must be TRUE:
        - MACD < MACD Signal (condition6sa)
        - MACD < Previous MACD (condition7s)
        - Close < Gann HiLo (condition8s)
        - RSI < RSI MA (condition11s)
        - Close < Supertrend (condition2s)
        - Close < Previous Low (condition5s)
        """
        return (
            (self.df['macd'] < self.df['macd_signal']) &
            (self.df['macd'] < self.df['macd'].shift(1)) &
            (self.df['close'] < self.df['gann_hilo']) &
            (self.df['rsi'] < self.df['rsi_ma']) &
            (self.df['close'] < self.df['supertrend']) &
            (self.df['close'] < self.df['low'].shift(1))
        ).fillna(False)
    
    def _detect_short_close(self) -> pd.Series:
        """
        Detect Short CLOSE signals.
        
        Any of 3 conditions triggers exit:
        - Close > Gann HiLo (condition_exit6s)
        - MACD > MACD Signal (condition_exit5s)
        - Price in Ichimoku Cloud (candleinthecloud)
        """
        in_cloud = self._is_in_ichimoku_cloud()
        
        return (
            (self.df['close'] > self.df['gann_hilo']) |
            (self.df['macd'] > self.df['macd_signal']) |
            in_cloud
        ).fillna(False)
    
    def _is_in_ichimoku_cloud(self) -> pd.Series:
        """
        Check if price is within Ichimoku cloud.
        
        Returns:
            Boolean series indicating if price is in cloud
        """
        span_a = self.df['ichimoku_span_a']
        span_b = self.df['ichimoku_span_b']
        close = self.df['close']
        
        # Price is in cloud if it's between Span A and Span B
        return (
            ((close < span_a) & (close > span_b)) |
            ((close > span_a) & (close < span_b))
        ).fillna(False)
    
    def get_signal_counts(self) -> Dict[str, int]:
        """
        Get count of each signal type.
        
        Returns:
            Dictionary with signal counts
        """
        return {
            'long_open': int(self.df['long_open'].sum()) if 'long_open' in self.df.columns else 0,
            'long_close': int(self.df['long_close'].sum()) if 'long_close' in self.df.columns else 0,
            'short_open': int(self.df['short_open'].sum()) if 'short_open' in self.df.columns else 0,
            'short_close': int(self.df['short_close'].sum()) if 'short_close' in self.df.columns else 0
        }
    
    def get_signal_dates(self) -> Dict[str, List[str]]:
        """
        Get dates for each signal type.
        
        Returns:
            Dictionary with lists of signal dates
        """
        return {
            'long_open': self.df[self.df['long_open']]['date'].dt.strftime('%Y-%m-%d').tolist(),
            'long_close': self.df[self.df['long_close']]['date'].dt.strftime('%Y-%m-%d').tolist(),
            'short_open': self.df[self.df['short_open']]['date'].dt.strftime('%Y-%m-%d').tolist(),
            'short_close': self.df[self.df['short_close']]['date'].dt.strftime('%Y-%m-%d').tolist()
        }
    
    def get_dataframe(self) -> pd.DataFrame:
        """
        Get DataFrame with signals.
        
        Returns:
            DataFrame with signals
        """
        return self.df
    
    def add_signal_labels(self) -> pd.DataFrame:
        """
        Add a combined 'signal' column with text labels.
        Priority: LONG OPEN > SHORT OPEN > LONG CLOSE > SHORT CLOSE > HOLD
        
        Returns:
            DataFrame with 'signal' column added
        """
        def get_signal_label(row):
            if row.get('long_open', False):
                return 'LONG OPEN'
            elif row.get('short_open', False):
                return 'SHORT OPEN'
            elif row.get('long_close', False):
                return 'LONG CLOSE'
            elif row.get('short_close', False):
                return 'SHORT CLOSE'
            else:
                return 'HOLD'
        
        self.df['signal'] = self.df.apply(get_signal_label, axis=1)
        return self.df
