"""Technical indicator calculator."""

import pandas as pd
import pandas_ta as ta
import logging
from typing import Optional

from .gann_hilo import calculate_gann_hilo
from config import (
    MACD_SETTINGS,
    RSI_SETTINGS,
    SUPERTREND_SETTINGS,
    ICHIMOKU_SETTINGS,
    GANN_HILO_SETTINGS,
    EMA_PERIODS,
    VOLUME_MA_PERIOD
)

logger = logging.getLogger(__name__)


class IndicatorCalculator:
    """Calculates all technical indicators for a price dataset."""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize calculator with price data.
        
        Args:
            df: DataFrame with columns: date, open, high, low, close, volume
        """
        self.df = df.copy()
        self.df['date'] = pd.to_datetime(self.df['date'])
        self.df = self.df.sort_values('date').reset_index(drop=True)
        
    def calculate_all(self) -> pd.DataFrame:
        """
        Calculate all indicators.
        
        Returns:
            DataFrame with all indicators added as columns
        """
        try:
            # Calculate each indicator
            self._calculate_macd()
            self._calculate_rsi()
            self._calculate_supertrend()
            self._calculate_ichimoku()
            self._calculate_gann_hilo()
            self._calculate_emas()
            self._calculate_volume_ma()
            
            logger.info(f"Calculated all indicators for {len(self.df)} records")
            return self.df
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            raise
    
    def _calculate_macd(self):
        """Calculate MACD indicator."""
        macd = ta.macd(
            self.df['close'],
            fast=MACD_SETTINGS['fast'],
            slow=MACD_SETTINGS['slow'],
            signal=MACD_SETTINGS['signal']
        )
        
        if macd is not None:
            self.df['macd'] = macd[f"MACD_{MACD_SETTINGS['fast']}_{MACD_SETTINGS['slow']}_{MACD_SETTINGS['signal']}"]
            self.df['macd_signal'] = macd[f"MACDs_{MACD_SETTINGS['fast']}_{MACD_SETTINGS['slow']}_{MACD_SETTINGS['signal']}"]
            self.df['macd_hist'] = macd[f"MACDh_{MACD_SETTINGS['fast']}_{MACD_SETTINGS['slow']}_{MACD_SETTINGS['signal']}"]
        else:
            logger.warning("MACD calculation returned None")
            self.df['macd'] = None
            self.df['macd_signal'] = None
            self.df['macd_hist'] = None
    
    def _calculate_rsi(self):
        """Calculate RSI indicator with moving average."""
        rsi = ta.rsi(self.df['close'], length=RSI_SETTINGS['period'])
        
        if rsi is not None:
            self.df['rsi'] = rsi
            # Calculate RSI moving average
            self.df['rsi_ma'] = self.df['rsi'].rolling(window=14).mean()
        else:
            logger.warning("RSI calculation returned None")
            self.df['rsi'] = None
            self.df['rsi_ma'] = None
    
    def _calculate_supertrend(self):
        """Calculate Supertrend indicator."""
        supertrend = ta.supertrend(
            self.df['high'],
            self.df['low'],
            self.df['close'],
            length=SUPERTREND_SETTINGS['period'],
            multiplier=SUPERTREND_SETTINGS['multiplier']
        )
        
        if supertrend is not None:
            self.df['supertrend'] = supertrend[f"SUPERT_{SUPERTREND_SETTINGS['period']}_{SUPERTREND_SETTINGS['multiplier']}"]
            self.df['supertrend_direction'] = supertrend[f"SUPERTd_{SUPERTREND_SETTINGS['period']}_{SUPERTREND_SETTINGS['multiplier']}"]
        else:
            logger.warning("Supertrend calculation returned None")
            self.df['supertrend'] = None
            self.df['supertrend_direction'] = None
    
    def _calculate_ichimoku(self):
        """Calculate Ichimoku Cloud indicator."""
        ichimoku = ta.ichimoku(
            self.df['high'],
            self.df['low'],
            self.df['close'],
            tenkan=ICHIMOKU_SETTINGS['conversion'],
            kijun=ICHIMOKU_SETTINGS['base'],
            senkou=ICHIMOKU_SETTINGS['span_b']
        )
        
        if ichimoku is not None and len(ichimoku) > 0:
            # Get column names from ichimoku result
            # pandas-ta uses kijun (base) value for ISB column name, not senkou
            conv = ICHIMOKU_SETTINGS['conversion']
            base = ICHIMOKU_SETTINGS['base']
            
            self.df['ichimoku_conversion'] = ichimoku[0][f"ITS_{conv}"]
            self.df['ichimoku_base'] = ichimoku[0][f"IKS_{base}"]
            self.df['ichimoku_span_a'] = ichimoku[0][f"ISA_{conv}"]
            self.df['ichimoku_span_b'] = ichimoku[0][f"ISB_{base}"]
            
            # Shift span A and B forward by displacement (26 periods default)
            displacement = ICHIMOKU_SETTINGS.get('displacement', 26)
            self.df['ichimoku_span_a'] = self.df['ichimoku_span_a'].shift(displacement)
            self.df['ichimoku_span_b'] = self.df['ichimoku_span_b'].shift(displacement)
        else:
            logger.warning("Ichimoku calculation returned None")
            self.df['ichimoku_conversion'] = None
            self.df['ichimoku_base'] = None
            self.df['ichimoku_span_a'] = None
            self.df['ichimoku_span_b'] = None
    
    def _calculate_gann_hilo(self):
        """Calculate custom Gann HiLo Activator."""
        self.df = calculate_gann_hilo(
            self.df,
            fast_period=GANN_HILO_SETTINGS['fast'],
            slow_period=GANN_HILO_SETTINGS['slow']
        )
    
    def _calculate_emas(self):
        """Calculate EMAs for specified periods."""
        for period in EMA_PERIODS:
            ema = ta.ema(self.df['close'], length=period)
            if ema is not None:
                self.df[f'ema_{period}'] = ema
            else:
                logger.warning(f"EMA{period} calculation returned None")
                self.df[f'ema_{period}'] = None
    
    def _calculate_volume_ma(self):
        """Calculate Volume Moving Average."""
        self.df['volume_ma'] = self.df['volume'].rolling(window=VOLUME_MA_PERIOD).mean()
    
    def get_dataframe(self) -> pd.DataFrame:
        """
        Get the DataFrame with all indicators.
        
        Returns:
            DataFrame with indicators
        """
        return self.df
