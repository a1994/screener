# Design: Chart Analysis & Trading Signal Visualization

## Context
This is the core analytical engine of the stock screener. It transforms raw price data into actionable trading signals by calculating multiple technical indicators and applying a confluence-based strategy derived from Pine Script. The system must handle real-time user interactions while maintaining data freshness through intelligent caching.

**Constraints:**
- Financial Modeling Prep API: 250 requests/day (free tier)
- EOD data only (no intraday)
- Must match Pine Script signal logic exactly
- Local SQLite for caching (no external cache server)
- Streamlit rerun model (stateless between interactions)

## Goals / Non-Goals

**Goals:**
- Accurate technical indicator calculations matching industry standards
- Precise signal generation matching provided Pine Script strategy
- Fast chart loading through aggressive caching
- Interactive, professional-grade charts
- Complete historical signal analysis (not just recent)

**Non-Goals:**
- Real-time/intraday data updates
- Backtesting engine with P&L calculations
- Multiple timeframe analysis (daily only)
- Custom indicator parameters (use Pine Script defaults)
- Automated trading execution

## Decisions

### Decision 1: Financial Modeling Prep API Over Yahoo Finance
**Choice:** Use Financial Modeling Prep (FMP) API instead of yfinance

**Rationale:**
- More reliable for production use
- Better structured API (RESTful vs scraping)
- Clear rate limits and pricing
- EOD endpoint perfect for our use case
- Consistent data format

**Alternatives Considered:**
- yfinance: Free but rate-limited unpredictably, scrapes Yahoo
- Alpha Vantage: 5 calls/minute too restrictive for batch operations
- IEX Cloud: More expensive, overkill for EOD data

### Decision 2: Aggressive Caching with Immutability Assumption
**Choice:** Cache EOD data permanently (never expire historical dates)

**Rationale:**
- EOD data is immutable after market close
- Eliminates 99% of API calls for repeated views
- Only today's date needs refresh
- Stays within API rate limits
- Instant chart loads for cached tickers

**Implementation:**
```python
def is_cache_valid(date: datetime.date) -> bool:
    if date < datetime.date.today():
        return True  # Historical data never changes
    else:
        return False  # Today's data may update
```

### Decision 3: pandas-ta Over ta-lib
**Choice:** Use pandas-ta as primary indicator library

**Rationale:**
- Pure Python (no C compilation required)
- Active development and maintenance
- Integrates seamlessly with pandas DataFrames
- Covers all needed indicators except Gann HiLo
- Easier deployment (no system dependencies)

**Alternatives Considered:**
- ta-lib: Requires C compilation, installation complexity
- Custom implementations: Time-consuming, error-prone

### Decision 4: Custom Gann HiLo Implementation
**Choice:** Implement Gann HiLo Activator from scratch based on Pine Script

**Rationale:**
- Not available in pandas-ta or ta-lib
- Core component of signal strategy
- Pine Script logic is clear and translatable
- ~50 lines of code, maintainable

**Pine Script Translation:**
```python
# Pine Script logic
# HLd = close > nz(ta.sma(high, HPeriod))[1] ? 1 : (close < nz(ta.sma(low, LPeriod))[1] ? -1 : 0)
# HLv = ta.valuewhen(HLd != 0, HLd, 0)
# HiLo = HLv == -1 ? sma_high : sma_low

def calculate_gann_hilo(df, high_period=13, low_period=21):
    sma_high = df['high'].rolling(window=high_period).mean()
    sma_low = df['low'].rolling(window=low_period).mean()
    
    # Direction determination
    hld = np.where(df['close'] > sma_high.shift(1), 1, 
                   np.where(df['close'] < sma_low.shift(1), -1, 0))
    
    # Forward fill last non-zero value
    hlv = pd.Series(hld).replace(0, np.nan).fillna(method='ffill').fillna(0)
    
    # Select line based on direction
    hilo = np.where(hlv == -1, sma_high, sma_low)
    
    return pd.Series(hilo, index=df.index)
```

### Decision 5: Plotly for Charting
**Choice:** Use Plotly for interactive charts

**Rationale:**
- Native Streamlit integration (st.plotly_chart)
- Interactive out of the box (zoom, pan, hover)
- Subplots for volume chart
- Professional appearance
- Good performance with 1000+ data points

**Alternatives Considered:**
- matplotlib: Static charts, requires manual interactivity
- lightweight-charts: JavaScript library, harder Streamlit integration
- Altair: Limited financial charting capabilities

### Decision 6: Signal Calculation on Entire Dataset
**Choice:** Calculate signals across all historical data, not just recent

**Rationale:**
- Provides complete signal history for analysis
- User may want to see past signals for validation
- No significant performance impact (vectorized operations)
- Supports future backtesting features

**Trade-offs:**
- Slightly more computation (negligible with pandas)
- More data to display (handled by Plotly efficiently)

### Decision 7: Synchronous Chart Loading
**Choice:** Block UI with spinner during chart load (synchronous)

**Rationale:**
- Chart is primary user focus (they expect to wait)
- 1-3 seconds acceptable for UX
- Simplifies state management
- Avoids race conditions with multiple clicks

**Alternatives Considered:**
- Async loading: Complexity outweighs benefit for <3s operations
- Pre-loading all charts: Wastes API calls, memory

## Data Flow Architecture

```
User Action (Select Ticker + Click Load)
    ↓
Check Ticker in Database
    ↓
Fetch Price Data
    ├─→ Check Cache (price_cache table)
    │   ├─→ All dates cached? → Use cache
    │   └─→ Missing dates? → API call
    ├─→ Call FMP API
    │   ├─→ Retry on failure (3x)
    │   └─→ Return OHLCV DataFrame
    └─→ Store in price_cache
    ↓
Calculate Indicators
    ├─→ MACD (pandas-ta)
    ├─→ RSI + RSI MA (pandas-ta)
    ├─→ Supertrend (pandas-ta)
    ├─→ Ichimoku (pandas-ta)
    ├─→ Gann HiLo (custom)
    ├─→ EMAs 8/21/50 (pandas)
    └─→ Volume MA 20 (pandas)
    ↓
Generate Signals
    ├─→ Long OPEN (5 conditions AND)
    ├─→ Long CLOSE (3 conditions OR)
    ├─→ Short OPEN (6 conditions AND)
    └─→ Short CLOSE (3 conditions OR)
    ↓
Render Chart
    ├─→ Main plot: Candlesticks + Indicators + Signals
    └─→ Volume subplot: Bars + MA + Cloud
    ↓
Display to User
```

## Signal Logic Translation

### Long OPEN Signal (All conditions must be TRUE)
```python
def detect_long_open(df):
    """
    Pine Script:
    if (condition6a and condition8 and condition11 and condition2 and condition5)
        strategy.entry("Long", strategy.long)
    """
    return (
        (df['MACD_12_26_9'] > df['MACDs_12_26_9']) &      # condition6a: MACD > Signal
        (df['close'] > df['gann_hilo']) &                  # condition8: Price > Gann HiLo
        (df['RSI_14'] > df['rsi_ma']) &                    # condition11: RSI > RSI MA
        (df['close'] > df['SUPERT_10_3.0']) &              # condition2: Price > Supertrend
        (df['close'] > df['high'].shift(1))                # condition5: Close > Prev High
    )
```

### Long CLOSE Signal (Any condition triggers exit)
```python
def detect_long_close(df):
    """
    Pine Script:
    if (condition_exit6 or condition_exit5 or candleinthecloud)
        strategy.close("Long")
    """
    # Check if price is in Ichimoku cloud
    in_cloud = (
        ((df['close'] < df['ISA_9'].shift(26)) & (df['close'] > df['ISB_26'].shift(26))) |
        ((df['close'] > df['ISA_9'].shift(26)) & (df['close'] < df['ISB_26'].shift(26)))
    )
    
    return (
        (df['close'] < df['gann_hilo']) |                  # condition_exit6
        (df['MACD_12_26_9'] < df['MACDs_12_26_9']) |       # condition_exit5
        in_cloud
    )
```

### Short OPEN Signal (All conditions must be TRUE)
```python
def detect_short_open(df):
    """
    Pine Script:
    if (condition6sa and condition7s and condition8s and condition11s and condition2s and condition5s)
        strategy.entry("short", strategy.short)
    """
    return (
        (df['MACD_12_26_9'] < df['MACDs_12_26_9']) &      # condition6sa
        (df['MACD_12_26_9'] < df['MACD_12_26_9'].shift(1)) &  # condition7s
        (df['close'] < df['gann_hilo']) &                  # condition8s
        (df['RSI_14'] < df['rsi_ma']) &                    # condition11s
        (df['close'] < df['SUPERT_10_3.0']) &              # condition2s
        (df['close'] < df['low'].shift(1))                 # condition5s
    )
```

### Short CLOSE Signal (Any condition triggers exit)
```python
def detect_short_close(df):
    """
    Pine Script:
    if (condition_exit6s or condition_exit5s or candleinthecloud)
        strategy.close("short")
    """
    in_cloud = (
        ((df['close'] < df['ISA_9'].shift(26)) & (df['close'] > df['ISB_26'].shift(26))) |
        ((df['close'] > df['ISA_9'].shift(26)) & (df['close'] < df['ISB_26'].shift(26)))
    )
    
    return (
        (df['close'] > df['gann_hilo']) |                  # condition_exit6s
        (df['MACD_12_26_9'] > df['MACDs_12_26_9']) |       # condition_exit5s
        in_cloud
    )
```

## API Integration Patterns

### FMPClient Class
```python
class FMPClient:
    BASE_URL = "https://financialmodelingprep.com/stable"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        
    def fetch_historical_eod(self, symbol: str) -> pd.DataFrame:
        """
        Fetch end-of-day historical data
        
        Returns DataFrame with columns: date, open, high, low, close, volume
        """
        url = f"{self.BASE_URL}/historical-price-eod/full"
        params = {"symbol": symbol, "apikey": self.api_key}
        
        response = self._retry_request(url, params)
        data = response.json()
        
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        
        return df
        
    def _retry_request(self, url: str, params: dict, max_retries: int = 3) -> requests.Response:
        """Exponential backoff retry logic"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                wait_time = 2 ** attempt
                time.sleep(wait_time)
```

## Risks / Trade-offs

### Risk 1: API Rate Limit Exceeded
**Risk:** Users viewing many tickers in one day could exceed 250 API calls

**Mitigation:**
- Aggressive caching (90%+ hit rate expected)
- Display remaining API quota in UI (future)
- Batch operations where possible
- Consider upgrading API plan for production

### Risk 2: Signal Calculation Accuracy
**Risk:** Python implementation doesn't match Pine Script exactly

**Mitigation:**
- Unit tests with known signal outputs
- Side-by-side comparison with TradingView charts
- Document any intentional deviations
- Validate with sample tickers (AAPL, TSLA, etc.)

### Risk 3: Chart Rendering Performance
**Risk:** Charts slow with 5+ years of daily data (1800+ points)

**Mitigation:**
- Plotly handles 1000+ points efficiently (tested)
- Use Plotly's WebGL mode if needed
- Limit default date range to 2 years (future enhancement)
- Downsample for very long ranges (future)

### Risk 4: Ichimoku Cloud Displacement
**Risk:** Cloud displacement by 26 periods may cause confusion with signal dates

**Mitigation:**
- Clearly document in UI that cloud is forward-shifted
- Use shift(-26) for visual display
- Signal logic uses actual date (not shifted)

### Risk 5: Cache Staleness
**Risk:** Today's data becomes stale if market is still open

**Mitigation:**
- Always refresh today's data on each request
- Show last updated timestamp on chart
- Add manual refresh button (future)

## Testing Strategy

### Unit Tests
1. **FMP Client:**
   - Mock API responses (success, 404, 429, timeout)
   - Test retry logic with failures
   - Verify DataFrame structure

2. **Indicators:**
   - Test each indicator with known inputs/outputs
   - Verify Gann HiLo matches Pine Script
   - Test edge cases (NaN handling, first N rows)

3. **Signals:**
   - Test each signal condition independently
   - Test combined logic (AND/OR operations)
   - Verify signal DataFrame structure

### Integration Tests
1. Full pipeline: API → Cache → Indicators → Signals → Chart
2. Cache hit/miss scenarios
3. Multiple tickers sequentially
4. Error recovery (bad ticker, API failure)

### Validation Tests
1. Compare signals with TradingView Pine Script output
2. Visual inspection of charts for accuracy
3. Verify signal marker positioning on candles

## Performance Targets

| Operation | Target | Measurement |
|-----------|--------|-------------|
| API call (uncached) | <2 seconds | Network latency |
| Indicator calculation (2000 bars) | <500ms | Pandas vectorization |
| Signal generation (2000 bars) | <100ms | Boolean operations |
| Chart rendering | <1 second | Plotly rendering |
| **Total (cached)** | **<3 seconds** | End-to-end |

## Open Questions

1. **Date Range Selection**: Should we add a date range picker for charts (e.g., last 6 months, 1 year, all-time)?
   - **Recommendation**: Defer to future enhancement, default to all available data

2. **Indicator Values Table**: Should we display a table of indicator values below the chart?
   - **Recommendation**: Not in MVP, hover tooltips sufficient

3. **Export Functionality**: Should we add "Download Data" button for CSV export?
   - **Recommendation**: Nice-to-have, defer to future

4. **Historical Data Depth**: How many years of data to fetch?
   - **Recommendation**: Fetch all available (typically 5 years), FMP provides full history

5. **Signal Confidence Scoring**: Should we add signal strength/confidence metrics?
   - **Recommendation**: Out of scope, would require strategy modification
