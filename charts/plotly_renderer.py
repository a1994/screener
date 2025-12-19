"""Plotly chart renderer for price and indicator visualization."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ChartRenderer:
    """Renders interactive charts with Plotly."""
    
    def __init__(self, df: pd.DataFrame, symbol: str):
        """
        Initialize renderer.
        
        Args:
            df: DataFrame with price, indicators, and signals
            symbol: Ticker symbol for chart title
        """
        self.df = df.copy()
        self.symbol = symbol
        
        # Ensure date is datetime
        if 'date' in self.df.columns:
            self.df['date'] = pd.to_datetime(self.df['date'])
    
    def render_full_chart(self) -> go.Figure:
        """
        Render complete chart with all indicators and signals.
        
        Returns:
            Plotly Figure object
        """
        # Create subplots: main price chart (70%) and volume (30%)
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.75, 0.25],
            subplot_titles=(f'{self.symbol} - Price & Indicators', 'Volume')
        )
        
        # Add candlestick chart
        self._add_candlesticks(fig)
        
        # Add EMAs
        self._add_emas(fig)
        
        # Add Gann HiLo
        self._add_gann_hilo(fig)
        
        # Add Supertrend
        self._add_supertrend(fig)
        
        # Add Ichimoku Cloud
        self._add_ichimoku_cloud(fig)
        
        # Add signal markers
        self._add_signal_markers(fig)
        
        # Add volume subplot
        self._add_volume(fig)
        
        # Update layout
        self._update_layout(fig)
        
        return fig
    
    def _add_candlesticks(self, fig: go.Figure):
        """Add candlestick chart."""
        fig.add_trace(
            go.Candlestick(
                x=self.df['date'],
                open=self.df['open'],
                high=self.df['high'],
                low=self.df['low'],
                close=self.df['close'],
                name='Price',
                increasing_line_color='#26a69a',
                decreasing_line_color='#ef5350'
            ),
            row=1, col=1
        )
    
    def _add_emas(self, fig: go.Figure):
        """Add EMA lines."""
        colors = {
            'ema_8': '#2196F3',   # Blue
            'ema_21': '#FF9800',  # Orange
            'ema_50': '#9C27B0'   # Purple
        }
        
        for ema_col, color in colors.items():
            if ema_col in self.df.columns:
                period = ema_col.split('_')[1]
                fig.add_trace(
                    go.Scatter(
                        x=self.df['date'],
                        y=self.df[ema_col],
                        name=f'EMA {period}',
                        line=dict(color=color, width=2),
                        opacity=0.9,
                        showlegend=True
                    ),
                    row=1, col=1
                )
    
    def _add_gann_hilo(self, fig: go.Figure):
        """Add Gann HiLo line."""
        if 'gann_hilo' in self.df.columns:
            fig.add_trace(
                go.Scatter(
                    x=self.df['date'],
                    y=self.df['gann_hilo'],
                    name='Gann HiLo',
                    line=dict(color='#00BCD4', width=2, dash='dash'),
                    opacity=0.8,
                    showlegend=True
                ),
                row=1, col=1
            )
    
    def _add_supertrend(self, fig: go.Figure):
        """Add Supertrend line."""
        if 'supertrend' in self.df.columns:
            # Color by direction: green for up, red for down
            df_up = self.df[self.df['supertrend_direction'] == 1].copy() if 'supertrend_direction' in self.df.columns else self.df
            df_down = self.df[self.df['supertrend_direction'] == -1].copy() if 'supertrend_direction' in self.df.columns else pd.DataFrame()
            
            if len(df_up) > 0:
                fig.add_trace(
                    go.Scatter(
                        x=df_up['date'],
                        y=df_up['supertrend'],
                        name='Supertrend Up',
                        line=dict(color='#4CAF50', width=1.5),
                        mode='lines',
                        showlegend=True
                    ),
                    row=1, col=1
                )
            
            if len(df_down) > 0:
                fig.add_trace(
                    go.Scatter(
                        x=df_down['date'],
                        y=df_down['supertrend'],
                        name='Supertrend Down',
                        line=dict(color='#F44336', width=1.5),
                        mode='lines',
                        showlegend=True
                    ),
                    row=1, col=1
                )
    
    def _add_ichimoku_cloud(self, fig: go.Figure):
        """Add Ichimoku Cloud."""
        if 'ichimoku_span_a' in self.df.columns and 'ichimoku_span_b' in self.df.columns:
            # Add Span A
            fig.add_trace(
                go.Scatter(
                    x=self.df['date'],
                    y=self.df['ichimoku_span_a'],
                    name='Ichimoku Span A',
                    line=dict(color='rgba(0,0,0,0)'),
                    showlegend=False,
                    hoverinfo='skip'
                ),
                row=1, col=1
            )
            
            # Add Span B and fill
            fig.add_trace(
                go.Scatter(
                    x=self.df['date'],
                    y=self.df['ichimoku_span_b'],
                    name='Ichimoku Cloud',
                    fill='tonexty',
                    fillcolor='rgba(156, 39, 176, 0.1)',
                    line=dict(color='rgba(0,0,0,0)'),
                    showlegend=True,
                    hoverinfo='skip'
                ),
                row=1, col=1
            )
    
    def _add_signal_markers(self, fig: go.Figure):
        """Add signal markers on chart."""
        # Long OPEN - Bright Lime Green with black border (distinct from candle green)
        if 'long_open' in self.df.columns:
            long_open = self.df[self.df['long_open'] == True]
            if len(long_open) > 0:
                fig.add_trace(
                    go.Scatter(
                        x=long_open['date'],
                        y=long_open['low'] * 0.99,  # Slightly below candle
                        mode='markers',
                        name='🟢 Long OPEN',
                        marker=dict(
                            symbol='triangle-up',
                            size=16,
                            color='#00FF00',  # Bright lime green
                            line=dict(color='#000000', width=2)  # Black border
                        )
                    ),
                    row=1, col=1
                )
        
        # Long CLOSE - Bright Magenta/Pink with black border (distinct from candle red)
        if 'long_close' in self.df.columns:
            long_close = self.df[self.df['long_close'] == True]
            if len(long_close) > 0:
                fig.add_trace(
                    go.Scatter(
                        x=long_close['date'],
                        y=long_close['high'] * 1.01,  # Slightly above candle
                        mode='markers',
                        name='🔴 Long CLOSE',
                        marker=dict(
                            symbol='triangle-down',
                            size=16,
                            color='#FF00FF',  # Bright magenta
                            line=dict(color='#000000', width=2)  # Black border
                        )
                    ),
                    row=1, col=1
                )
        
        # Short OPEN - Bright Orange/Yellow with black border
        if 'short_open' in self.df.columns:
            short_open = self.df[self.df['short_open'] == True]
            if len(short_open) > 0:
                fig.add_trace(
                    go.Scatter(
                        x=short_open['date'],
                        y=short_open['high'] * 1.01,
                        mode='markers',
                        name='🟠 Short OPEN',
                        marker=dict(
                            symbol='triangle-down',
                            size=16,
                            color='#FFA500',  # Bright orange
                            line=dict(color='#000000', width=2)  # Black border
                        )
                    ),
                    row=1, col=1
                )
        
        # Short CLOSE - Bright Cyan/Aqua with black border
        if 'short_close' in self.df.columns:
            short_close = self.df[self.df['short_close'] == True]
            if len(short_close) > 0:
                fig.add_trace(
                    go.Scatter(
                        x=short_close['date'],
                        y=short_close['low'] * 0.99,
                        mode='markers',
                        name='🔵 Short CLOSE',
                        marker=dict(
                            symbol='triangle-up',
                            size=16,
                            color='#00FFFF',  # Bright cyan
                            line=dict(color='#000000', width=2)  # Black border
                        )
                    ),
                    row=1, col=1
                )
    
    def _add_volume(self, fig: go.Figure):
        """Add volume subplot with MA and cloud."""
        if 'volume' not in self.df.columns:
            # Add placeholder volume if missing
            logger.warning(f"No volume data for {self.symbol}, adding placeholder")
            self.df['volume'] = 1000000  # Default volume
        
        # Ensure volume is not zero (some data sources have zero volume)
        self.df['volume'] = self.df['volume'].replace(0, 1000)
        
        # Color volume bars by price change
        colors = ['#ef5350' if row['close'] < row['open'] else '#26a69a' 
                  for _, row in self.df.iterrows()]
        
        # Add volume bars
        fig.add_trace(
            go.Bar(
                x=self.df['date'],
                y=self.df['volume'],
                name='Volume',
                marker_color=colors,
                opacity=0.8,
                showlegend=False,
                hovertemplate='<b>%{x}</b><br>Volume: %{y:,.0f}<extra></extra>'
            ),
            row=2, col=1
        )
        
        # Add volume MA
        if 'volume_ma' in self.df.columns:
            fig.add_trace(
                go.Scatter(
                    x=self.df['date'],
                    y=self.df['volume_ma'],
                    name='Volume MA',
                    line=dict(color='#FFC107', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(255, 193, 7, 0.1)'
                ),
                row=2, col=1
            )
    
    def _update_layout(self, fig: go.Figure):
        """Update chart layout and styling."""
        fig.update_layout(
            title=dict(
                text=f'{self.symbol} - Technical Analysis',
                font=dict(size=20, color='#333'),
                x=0.5
            ),
            xaxis_rangeslider_visible=False,
            hovermode='x unified',
            height=600,
            template='plotly_white',
            showlegend=True,
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='center',
                x=0.5,
                font=dict(size=12)
            ),
            margin=dict(l=60, r=60, t=80, b=60),
            font=dict(size=12),
            autosize=True
        )
        
        # Add mobile-responsive legend configuration via JavaScript
        # This will be applied by the browser based on screen size
        fig.add_annotation(
            text="",  # Empty text, just used to inject mobile CSS
            showarrow=False,
            xref="paper", yref="paper",
            x=0, y=0,
            xanchor="left", yanchor="bottom",
            font=dict(size=1, color="rgba(0,0,0,0)"),  # Invisible
            bgcolor="rgba(0,0,0,0)",  # Transparent
            bordercolor="rgba(0,0,0,0)"  # Transparent
        )
        
        # Remove non-trading days (weekends) from both x-axes to make chart smooth
        # This removes gaps where markets are closed
        rangebreaks = [
            dict(bounds=["sat", "mon"]),  # Hide weekends (Saturday to Monday)
        ]
        
        # Update x-axes with rangebreaks to hide non-trading days
        fig.update_xaxes(rangebreaks=rangebreaks, row=1, col=1)
        fig.update_xaxes(title_text='Date', rangebreaks=rangebreaks, row=2, col=1)
        
        # Update y-axes
        fig.update_yaxes(title_text='Price', row=1, col=1)
        fig.update_yaxes(title_text='Volume', row=2, col=1)
