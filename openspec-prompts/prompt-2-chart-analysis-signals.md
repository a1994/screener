# OpenSpec Prompt 2: Chart Analysis & Trading Signal Visualization

## Context
Building on the ticker management infrastructure from Proposal 1, this proposal covers the interactive chart analysis system. The application will fetch historical price data from Financial Modeling Prep API, calculate technical indicators (MACD, RSI, Gann HiLo, Supertrend, Ichimoku Cloud), generate trading signals (Long OPEN/CLOSE, Short OPEN/CLOSE), and display them on interactive candlestick charts with EMAs and volume analysis.

## Problem Statement
Traders need a visual interface to:
1. Select a ticker from their watchlist and load its historical price data
2. View an interactive candlestick chart with key technical indicators
3. Identify trading signal events (entry/exit points) directly on the chart
4. Analyze volume patterns with moving average cloud visualization
5. Understand complete historical signal context, not just recent signals

The solution must handle API rate limits, implement intelligent caching, and calculate signals across the entire historical dataset for comprehensive analysis.

## Requirements

### 1. Data Fetching & API Integration

#### Financial Modeling Prep API
- **Endpoint**: `https://financialmodelingprep.com/stable/historical-price-eod/full`
- **Parameters**:
  - `symbol`: Ticker symbol (e.g., TSLA)
  - `apikey`: `MpWngYwXg4WMCz4sQzz5byJzB8SGekBt`
- **Response Format**: JSON array of OHLCV data
  ```json
  [
    {
      "date": "2025-11-20",
      "open": 150.25,
      "high": 152.80,
      "low": 149.50,
      "close": 151.75,
      "volume": 12500000
    }
  ]
  ```

#### Caching Strategy
- **Cache Storage**: Use SQLite `price_cache` table (from Proposal 1)
- **Caching Logic**:
  - Check if data exists for ticker + date
  - If date < today AND data exists in cache → use cached data (EOD data doesn't change)
  - If date == today → fetch fresh data from API (intraday updates)
  - If no cache → fetch from API and store
- **Cache Key**: `(ticker_id, date)`
- **Cache Expiry**: Never expire for historical dates, refresh today's data on each request
- **Implementation**: Create `PriceDataCache` class with methods:
  - `get_cached_data(ticker_id: int, start_date: date, end_date: date) -> pd.DataFrame`
  - `fetch_and_cache(symbol: str, ticker_id: int) -> pd.DataFrame`
  - `is_cache_valid(ticker_id: int, date: date) -> bool`

#### Error Handling
- API failures: Retry with exponential backoff (3 attempts)
- Rate limiting: Track API call count, implement queue if needed
- Invalid ticker symbols: Display user-friendly error message
- Network timeouts: 30-second timeout, show loading spinner

### 2. Technical Indicator Calculations

#### Library Choice
- **Primary**: `pandas-ta` (comprehensive, actively maintained)
- **Fallback**: `ta-lib` (if pandas-ta missing specific indicators)
- **Custom**: Gann HiLo Activator (implement from Pine Script logic)

#### Indicators to Calculate

##### A. MACD (Moving Average Convergence Divergence)
```python
# pandas-ta
df.ta.macd(close='close', fast=12, slow=26, signal=9, append=True)
# Adds columns: MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9
```
- **Purpose**: Momentum indicator for signal generation
- **Parameters**: Fast=12, Slow=26, Signal=9 (standard)

##### B. RSI (Relative Strength Index)
```python
df.ta.rsi(close='close', length=14, append=True)
# Adds column: RSI_14
```
- **Purpose**: Momentum strength measurement
- **Parameters**: Length=14
- **Additional**: Calculate RSI moving average (SMA of RSI, length=14)

##### C. Supertrend
```python
df.ta.supertrend(high='high', low='low', close='close', 
                 length=10, multiplier=3.0, append=True)
# Adds columns: SUPERT_10_3.0, SUPERTd_10_3.0, SUPERTl_10_3.0, SUPERTs_10_3.0
```
- **Purpose**: Trend direction confirmation
- **Parameters**: ATR Length=10, Multiplier=3.0

##### D. Ichimoku Cloud
```python
df.ta.ichimoku(high='high', low='low', close='close',
               tenkan=9, kijun=26, senkou=52, append=True)
# Adds: ITS_9, IKS_26, ICS_26, ISA_9, ISB_26
```
- **Purpose**: Support/resistance, cloud-based exit logic
- **Parameters**: Conversion=9, Base=26, Lagging Span B=52, Displacement=26
- **Key Logic**: Check if price enters cloud (between Senkou Span A and B)

##### E. Gann HiLo Activator (Custom Implementation)
Based on Pine Script logic:
```python
def calculate_gann_hilo(df, high_period=13, low_period=21):
    """
    Gann HiLo Activator calculation from Pine Script
    
    Logic:
    - If close > SMA(high, high_period)[1]: HLv = 1 (uptrend)
    - If close < SMA(low, low_period)[1]: HLv = -1 (downtrend)
    - HiLo line = SMA(high, high_period) if HLv=-1, else SMA(low, low_period)
    """
    sma_high = df['high'].rolling(window=high_period).mean()
    sma_low = df['low'].rolling(window=low_period).mean()
    
    # Determine direction
    hld = np.where(df['close'] > sma_high.shift(1), 1, 
                   np.where(df['close'] < sma_low.shift(1), -1, 0))
    
    # Get last non-zero value
    hlv = pd.Series(hld).replace(0, np.nan).fillna(method='ffill').fillna(0)
    
    # Calculate HiLo line
    hilo = np.where(hlv == -1, sma_high, sma_low)
    
    return pd.Series(hilo, index=df.index)

df['gann_hilo'] = calculate_gann_hilo(df, high_period=13, low_period=21)
```
- **Purpose**: Dynamic support/resistance level
- **Parameters**: High Period=13, Low Period=21

##### F. Exponential Moving Averages (EMAs)
```python
df['ema_8'] = df['close'].ewm(span=8, adjust=False).mean()
df['ema_21'] = df['close'].ewm(span=21, adjust=False).mean()
df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
```
- **Purpose**: Trend identification and chart overlay

##### G. Volume Moving Average
```python
df['volume_ma_20'] = df['volume'].rolling(window=20).mean()
```
- **Purpose**: Volume cloud visualization (fill between volume and volume MA)

### 3. Trading Signal Generation

#### Signal Logic (from stock-breakout-prompt.md and pine-script)

##### Long Entry (Long OPEN)
**All 5 conditions must be TRUE:**
1. `macd_line > macd_signal` (MACD crossing above signal)
2. `close > gann_hilo` (Price above Gann HiLo)
3. `rsi > rsi_ma` (RSI above its moving average)
4. `close > supertrend` (Price above Supertrend)
5. `close > high[previous_bar]` (Current close above previous high)

```python
def detect_long_open(df):
    conditions = (
        (df['MACD_12_26_9'] > df['MACDs_12_26_9']) &  # condition6a
        (df['close'] > df['gann_hilo']) &  # condition8
        (df['RSI_14'] > df['rsi_ma']) &  # condition11
        (df['close'] > df['SUPERT_10_3.0']) &  # condition2
        (df['close'] > df['high'].shift(1))  # condition5
    )
    return conditions
```

##### Long Exit (Long CLOSE)
**ANY 1 condition triggers exit:**
1. `macd_line < macd_signal` (MACD crosses below signal)
2. `close < gann_hilo` (Price drops below Gann HiLo)
3. Price enters Ichimoku cloud (between ISA_9 and ISB_26)

```python
def detect_long_close(df):
    # Check if price is in cloud
    in_cloud = (
        ((df['close'] < df['ISA_9'].shift(26)) & (df['close'] > df['ISB_26'].shift(26))) |
        ((df['close'] > df['ISA_9'].shift(26)) & (df['close'] < df['ISB_26'].shift(26)))
    )
    
    conditions = (
        (df['close'] < df['gann_hilo']) |  # condition_exit6
        (df['MACD_12_26_9'] < df['MACDs_12_26_9']) |  # condition_exit5
        in_cloud
    )
    return conditions
```

##### Short Entry (Short OPEN)
**All 6 conditions must be TRUE:**
1. `macd_line < macd_signal` (MACD crossing below signal)
2. `macd_line < macd_line[previous_bar]` (MACD momentum falling)
3. `close < gann_hilo` (Price below Gann HiLo)
4. `rsi < rsi_ma` (RSI below its moving average)
5. `close < supertrend` (Price below Supertrend)
6. `close < low[previous_bar]` (Current close below previous low)

```python
def detect_short_open(df):
    conditions = (
        (df['MACD_12_26_9'] < df['MACDs_12_26_9']) &  # condition6sa
        (df['MACD_12_26_9'] < df['MACD_12_26_9'].shift(1)) &  # condition7s
        (df['close'] < df['gann_hilo']) &  # condition8s
        (df['RSI_14'] < df['rsi_ma']) &  # condition11s
        (df['close'] < df['SUPERT_10_3.0']) &  # condition2s
        (df['close'] < df['low'].shift(1))  # condition5s
    )
    return conditions
```

##### Short Exit (Short CLOSE)
**ANY 1 condition triggers exit:**
1. `macd_line > macd_signal` (MACD crosses above signal)
2. `close > gann_hilo` (Price breaks above Gann HiLo)
3. Price enters Ichimoku cloud

```python
def detect_short_close(df):
    in_cloud = (
        ((df['close'] < df['ISA_9'].shift(26)) & (df['close'] > df['ISB_26'].shift(26))) |
        ((df['close'] > df['ISA_9'].shift(26)) & (df['close'] < df['ISB_26'].shift(26)))
    )
    
    conditions = (
        (df['close'] > df['gann_hilo']) |  # condition_exit6s
        (df['MACD_12_26_9'] > df['MACDs_12_26_9']) |  # condition_exit5s
        in_cloud
    )
    return conditions
```

#### Signal DataFrame Structure
After calculation, create a signals DataFrame:
```python
signals_df = pd.DataFrame({
    'date': df['date'],
    'long_open': detect_long_open(df),
    'long_close': detect_long_close(df),
    'short_open': detect_short_open(df),
    'short_close': detect_short_close(df)
})
```

### 4. Interactive Chart Visualization

#### Charting Library
- **Choice**: Plotly (`plotly.graph_objects`) for interactivity
- **Chart Type**: Candlestick chart with multiple subplots

#### Chart Layout
```
+----------------------------------+
|   Main Chart: Candlesticks       |
|   + EMA 8, 21, 50                |
|   + Gann HiLo line               |
|   + Supertrend line              |
|   + Ichimoku Cloud (fill)        |
|   + Signal markers               |
|   (70% height)                   |
+----------------------------------+
|   Volume Subplot                 |
|   + Volume bars                  |
|   + Volume MA 20 (line)          |
|   + Volume Cloud (fill)          |
|   (30% height)                   |
+----------------------------------+
```

#### Implementation Details

##### Candlestick Chart
```python
import plotly.graph_objects as go
from plotly.subplots import make_subplots

fig = make_subplots(
    rows=2, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.03,
    row_heights=[0.7, 0.3],
    subplot_titles=('Price Chart', 'Volume')
)

# Candlesticks
fig.add_trace(
    go.Candlestick(
        x=df['date'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='OHLC'
    ),
    row=1, col=1
)
```

##### EMA Overlays
```python
# EMA 8 (fast, typically green)
fig.add_trace(
    go.Scatter(x=df['date'], y=df['ema_8'], 
               mode='lines', name='EMA 8',
               line=dict(color='green', width=1)),
    row=1, col=1
)

# EMA 21 (medium, typically orange)
fig.add_trace(
    go.Scatter(x=df['date'], y=df['ema_21'], 
               mode='lines', name='EMA 21',
               line=dict(color='orange', width=1)),
    row=1, col=1
)

# EMA 50 (slow, typically red)
fig.add_trace(
    go.Scatter(x=df['date'], y=df['ema_50'], 
               mode='lines', name='EMA 50',
               line=dict(color='red', width=1.5)),
    row=1, col=1
)
```

##### Gann HiLo & Supertrend
```python
# Gann HiLo
fig.add_trace(
    go.Scatter(x=df['date'], y=df['gann_hilo'],
               mode='lines', name='Gann HiLo',
               line=dict(color='blue', width=2, dash='dash')),
    row=1, col=1
)

# Supertrend (color based on direction)
fig.add_trace(
    go.Scatter(x=df['date'], y=df['SUPERT_10_3.0'],
               mode='lines', name='Supertrend',
               line=dict(color='purple', width=2)),
    row=1, col=1
)
```

##### Ichimoku Cloud
```python
# Senkou Span A (Leading Span A)
fig.add_trace(
    go.Scatter(x=df['date'], y=df['ISA_9'].shift(26),
               mode='lines', name='Senkou Span A',
               line=dict(color='green', width=1),
               showlegend=False),
    row=1, col=1
)

# Senkou Span B (Leading Span B)
fig.add_trace(
    go.Scatter(x=df['date'], y=df['ISB_26'].shift(26),
               mode='lines', name='Senkou Span B',
               line=dict(color='red', width=1),
               fill='tonexty',  # Fill to previous trace (cloud effect)
               fillcolor='rgba(200, 200, 200, 0.2)'),
    row=1, col=1
)
```

##### Trading Signal Markers
```python
# Filter signals
long_open_dates = df[signals_df['long_open']]['date']
long_open_prices = df[signals_df['long_open']]['low'] * 0.99  # Below candle

long_close_dates = df[signals_df['long_close']]['date']
long_close_prices = df[signals_df['long_close']]['high'] * 1.01  # Above candle

short_open_dates = df[signals_df['short_open']]['date']
short_open_prices = df[signals_df['short_open']]['high'] * 1.01

short_close_dates = df[signals_df['short_close']]['date']
short_close_prices = df[signals_df['short_close']]['low'] * 0.99

# Long OPEN (green triangle up)
fig.add_trace(
    go.Scatter(
        x=long_open_dates,
        y=long_open_prices,
        mode='markers',
        name='Long OPEN',
        marker=dict(symbol='triangle-up', size=12, color='lime'),
        hovertemplate='<b>Long OPEN</b><br>Date: %{x}<br>Price: %{y:.2f}<extra></extra>'
    ),
    row=1, col=1
)

# Long CLOSE (red triangle down)
fig.add_trace(
    go.Scatter(
        x=long_close_dates,
        y=long_close_prices,
        mode='markers',
        name='Long CLOSE',
        marker=dict(symbol='triangle-down', size=12, color='red'),
        hovertemplate='<b>Long CLOSE</b><br>Date: %{x}<br>Price: %{y:.2f}<extra></extra>'
    ),
    row=1, col=1
)

# Short OPEN (orange triangle down)
fig.add_trace(
    go.Scatter(
        x=short_open_dates,
        y=short_open_prices,
        mode='markers',
        name='Short OPEN',
        marker=dict(symbol='triangle-down', size=12, color='orange'),
        hovertemplate='<b>Short OPEN</b><br>Date: %{x}<br>Price: %{y:.2f}<extra></extra>'
    ),
    row=1, col=1
)

# Short CLOSE (cyan triangle up)
fig.add_trace(
    go.Scatter(
        x=short_close_dates,
        y=short_close_prices,
        mode='markers',
        name='Short CLOSE',
        marker=dict(symbol='triangle-up', size=12, color='cyan'),
        hovertemplate='<b>Short CLOSE</b><br>Date: %{x}<br>Price: %{y:.2f}<extra></extra>'
    ),
    row=1, col=1
)
```

##### Volume Subplot with MA Cloud
```python
# Volume bars (color based on price change)
colors = ['green' if close > open else 'red' 
          for close, open in zip(df['close'], df['open'])]

fig.add_trace(
    go.Bar(x=df['date'], y=df['volume'],
           name='Volume',
           marker=dict(color=colors),
           showlegend=False),
    row=2, col=1
)

# Volume MA 20
fig.add_trace(
    go.Scatter(x=df['date'], y=df['volume_ma_20'],
               mode='lines', name='Volume MA 20',
               line=dict(color='blue', width=2)),
    row=2, col=1
)

# Volume Cloud (fill between volume and volume MA)
fig.add_trace(
    go.Scatter(x=df['date'], y=df['volume'],
               mode='lines', name='Volume',
               line=dict(width=0),
               fill='tonexty',
               fillcolor='rgba(0, 100, 255, 0.2)',
               showlegend=False),
    row=2, col=1
)
```

##### Chart Configuration
```python
fig.update_layout(
    title=f'{symbol} - Technical Analysis',
    xaxis_title='Date',
    yaxis_title='Price',
    xaxis2_title='Date',
    yaxis2_title='Volume',
    height=800,
    hovermode='x unified',
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
)

fig.update_xaxes(rangeslider_visible=False)  # Disable range slider
st.plotly_chart(fig, use_container_width=True)
```

### 5. Chart Analysis Tab UI

#### Streamlit Layout
```python
with tab1:  # Chart Analysis Tab
    st.title("📈 Chart Analysis")
    
    # Ticker selection dropdown
    tickers = get_all_tickers()  # From database
    
    if not tickers:
        st.warning("No tickers found. Please add tickers in the Dashboard tab.")
    else:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            selected_ticker = st.selectbox(
                "Select Ticker",
                options=tickers,
                index=0
            )
        
        with col2:
            if st.button("Load Chart", type="primary"):
                st.session_state.load_chart = True
        
        # Display loading status
        if st.session_state.get('load_chart', False):
            with st.spinner(f'Loading data for {selected_ticker}...'):
                # Fetch and cache data
                df = fetch_price_data(selected_ticker)
                
                if df is not None and not df.empty:
                    # Calculate indicators
                    df = calculate_all_indicators(df)
                    
                    # Generate signals
                    signals = generate_signals(df)
                    
                    # Render chart
                    render_chart(df, signals, selected_ticker)
                    
                    # Display signal summary
                    st.subheader("Signal Summary")
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Long OPEN", signals['long_open'].sum())
                    col2.metric("Long CLOSE", signals['long_close'].sum())
                    col3.metric("Short OPEN", signals['short_open'].sum())
                    col4.metric("Short CLOSE", signals['short_close'].sum())
                else:
                    st.error(f"Failed to load data for {selected_ticker}")
```

### 6. Code Organization

#### New Modules
```
screener/
├── api/
│   ├── __init__.py
│   ├── fmp_client.py (Financial Modeling Prep API client)
│   └── cache_manager.py (Caching logic)
├── indicators/
│   ├── __init__.py
│   ├── calculator.py (All indicator calculations)
│   ├── gann_hilo.py (Custom Gann HiLo implementation)
│   └── signals.py (Signal detection logic)
├── charts/
│   ├── __init__.py
│   ├── plotly_renderer.py (Plotly chart generation)
│   └── formatters.py (Data formatting for charts)
└── components/
    ├── chart_analysis.py (Chart Analysis tab UI)
    └── ...
```

#### Key Classes

##### FMPClient (api/fmp_client.py)
```python
class FMPClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://financialmodelingprep.com/stable"
        
    def fetch_historical_eod(self, symbol: str) -> Dict:
        """Fetch end-of-day historical data"""
        
    def _retry_request(self, url: str, max_retries: int = 3) -> Response:
        """Retry logic with exponential backoff"""
```

##### IndicatorCalculator (indicators/calculator.py)
```python
class IndicatorCalculator:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        
    def calculate_all(self) -> pd.DataFrame:
        """Calculate all indicators and return enriched DataFrame"""
        
    def calculate_macd(self) -> pd.DataFrame:
    def calculate_rsi(self) -> pd.DataFrame:
    def calculate_supertrend(self) -> pd.DataFrame:
    def calculate_ichimoku(self) -> pd.DataFrame:
    def calculate_gann_hilo(self) -> pd.DataFrame:
    def calculate_emas(self) -> pd.DataFrame:
    def calculate_volume_ma(self) -> pd.DataFrame:
```

##### SignalDetector (indicators/signals.py)
```python
class SignalDetector:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        
    def detect_all_signals(self) -> pd.DataFrame:
        """Detect all signal types across entire dataset"""
        
    def detect_long_open(self) -> pd.Series:
    def detect_long_close(self) -> pd.Series:
    def detect_short_open(self) -> pd.Series:
    def detect_short_close(self) -> pd.Series:
```

##### ChartRenderer (charts/plotly_renderer.py)
```python
class ChartRenderer:
    def __init__(self, df: pd.DataFrame, signals: pd.DataFrame, symbol: str):
        self.df = df
        self.signals = signals
        self.symbol = symbol
        
    def render(self) -> go.Figure:
        """Generate complete Plotly figure"""
        
    def _add_candlesticks(self, fig, row):
    def _add_emas(self, fig, row):
    def _add_indicators(self, fig, row):
    def _add_signals(self, fig, row):
    def _add_volume(self, fig, row):
```

## Technical Constraints
- Pandas 1.5+, NumPy 1.24+
- pandas-ta 0.3.14+ or ta-lib 0.4.24+
- Plotly 5.17+
- Requests 2.31+ (for API calls)
- Calculate indicators for entire historical dataset (typically 1-5 years of daily data)
- Chart rendering should handle 1000+ data points without performance degradation
- API caching must prevent redundant calls for same ticker on same day

## Success Criteria
1. Chart loads with all indicators in <3 seconds for cached data
2. Signal calculations are accurate (100% match with Pine Script logic)
3. All 4 signal types (Long OPEN/CLOSE, Short OPEN/CLOSE) are correctly identified
4. Cache hit rate >90% for repeated ticker views
5. Charts are interactive (zoom, pan, hover tooltips work correctly)
6. Volume cloud is visually distinct and informative
7. Signal markers are clearly visible and positioned correctly on candles

## Non-Goals (Out of Scope)
- Real-time/intraday data updates (EOD data only)
- Backtesting functionality (signal generation only)
- Multiple timeframe analysis (daily only)
- Custom indicator parameters (use defaults from Pine Script)
- Export chart as image (Plotly has built-in export)

## Dependencies on Other Proposals
- **Depends on Proposal 1**: Requires ticker database and retrieval functions
- **Required by Proposal 3**: Signals generated here will be used for alert system

## Reference Materials
- Financial Modeling Prep API Docs: https://site.financialmodelingprep.com/developer/docs
- pandas-ta Documentation: https://github.com/twopirllc/pandas-ta
- Plotly Candlestick Charts: https://plotly.com/python/candlestick-charts/
- Pine Script Reference (attached): `pine-script` file
- Strategy Explanation (attached): `stock-breakout-prompt.md`

## Open Questions
1. Should we support date range selection for chart display (e.g., last 6 months, 1 year, all-time)?
2. Do we need to display indicator values in a separate table below the chart?
3. Should we add a "Download Data" button to export OHLC + indicators as CSV?
4. Maximum historical data to fetch? (Suggest 5 years for comprehensive analysis)

---

**Next Steps After Approval:**
- Detailed technical specification
- Pine Script to Python signal logic mapping verification
- API integration test plan
- Chart rendering performance benchmarks
- Implementation task breakdown
