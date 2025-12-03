# Implementation Tasks

## 1. API Integration & Data Fetching
- [x] 1.1 Create `api/__init__.py` module
- [x] 1.2 Implement `api/fmp_client.py` with Financial Modeling Prep API integration
- [x] 1.3 Add API request retry logic with exponential backoff (3 attempts)
- [x] 1.4 Implement timeout handling (30 seconds)
- [x] 1.5 Add API rate limiting tracker
- [x] 1.6 Create error handling for invalid tickers and network failures

## 2. Caching Infrastructure
- [x] 2.1 Implement `api/cache_manager.py` for price data caching
- [x] 2.2 Add cache validation logic (historical dates vs today)
- [x] 2.3 Implement cache read from price_cache table
- [x] 2.4 Implement cache write with upsert logic
- [x] 2.5 Add cache expiry rules (never expire historical, refresh today)
- [x] 2.6 Create batch cache operations for performance

## 3. Technical Indicator Calculations
- [x] 3.1 Create `indicators/__init__.py` module
- [x] 3.2 Implement `indicators/calculator.py` main calculator class
- [x] 3.3 Add MACD calculation using pandas-ta (fast=12, slow=26, signal=9)
- [x] 3.4 Add RSI calculation with moving average (length=14)
- [x] 3.5 Add Supertrend calculation (ATR length=10, multiplier=3.0)
- [x] 3.6 Add Ichimoku Cloud calculation (conversion=9, base=26, lagging=52, displacement=26)
- [x] 3.7 Implement custom Gann HiLo Activator in `indicators/gann_hilo.py`
- [x] 3.8 Add EMA calculations (8, 21, 50 periods)
- [x] 3.9 Add Volume MA calculation (20-period)
- [x] 3.10 Create unified calculate_all_indicators() method

## 4. Trading Signal Generation
- [x] 4.1 Create `indicators/signals.py` module
- [x] 4.2 Implement Long OPEN signal detection (5 conditions)
- [x] 4.3 Implement Long CLOSE signal detection (3 exit conditions)
- [x] 4.4 Implement Short OPEN signal detection (6 conditions)
- [x] 4.5 Implement Short CLOSE signal detection (3 exit conditions)
- [x] 4.6 Add Ichimoku cloud entry detection logic
- [x] 4.7 Create signal DataFrame structure
- [x] 4.8 Verify signal logic matches Pine Script exactly

## 5. Chart Rendering with Plotly
- [x] 5.1 Create `charts/__init__.py` module
- [x] 5.2 Implement `charts/plotly_renderer.py` main renderer class
- [x] 5.3 Add candlestick chart generation (OHLC data)
- [x] 5.4 Add EMA overlay plots (8, 21, 50 with distinct colors)
- [x] 5.5 Add Gann HiLo line overlay (blue dashed line)
- [x] 5.6 Add Supertrend line overlay (purple, color-coded by direction)
- [x] 5.7 Add Ichimoku Cloud fill between Senkou Span A and B
- [x] 5.8 Add signal markers (triangles: green/red/orange/cyan)
- [x] 5.9 Create volume subplot with colored bars
- [x] 5.10 Add volume MA line and cloud fill
- [x] 5.11 Configure chart layout (2 subplots, 70/30 height ratio)
- [x] 5.12 Add hover tooltips for all elements
- [x] 5.13 Enable interactive features (zoom, pan, crosshair)

## 6. Chart Analysis Tab UI
- [x] 6.1 Create `components/chart_analysis.py` module
- [x] 6.2 Implement ticker dropdown populated from database
- [x] 6.3 Add "Load Chart" button with loading spinner
- [x] 6.4 Integrate API data fetching on button click
- [x] 6.5 Display chart using st.plotly_chart()
- [x] 6.6 Add signal summary metrics (counts of each signal type)
- [x] 6.7 Add error handling for missing data or API failures
- [x] 6.8 Show empty state when no tickers available

## 7. Data Processing Pipeline
- [x] 7.1 Create `charts/formatters.py` for data formatting
- [x] 7.2 Implement pandas DataFrame to Plotly format conversion
- [x] 7.3 Add date formatting for x-axis
- [x] 7.4 Add price formatting for y-axis
- [x] 7.5 Implement signal marker positioning logic (above/below candles)

## 8. Integration with Ticker Management
- [x] 8.1 Extend `database/ticker_repository.py` with get_active_tickers() for dropdown
- [x] 8.2 Add price_cache query methods (get_cached_data, is_cache_valid)
- [x] 8.3 Update ticker last_updated timestamp after data fetch
- [x] 8.4 Link ticker_id to price_cache foreign key

## 9. Configuration & Settings
- [x] 9.1 Add API key configuration in `config/settings.py`
- [x] 9.2 Add indicator parameters as configurable constants
- [x] 9.3 Add chart styling configuration (colors, line widths)
- [x] 9.4 Add cache TTL settings

## 10. Error Handling & Validation
- [x] 10.1 Handle API rate limit exceeded (429 status)
- [x] 10.2 Handle invalid ticker symbols (404 status)
- [x] 10.3 Handle network timeouts gracefully
- [x] 10.4 Validate indicator calculation outputs (no NaN in critical fields)
- [x] 10.5 Add logging for API calls and errors

## 11. Testing
- [x] 11.1 Create `tests/test_fmp_client.py` with mock API responses
- [x] 11.2 Create `tests/test_indicators.py` for indicator calculations
- [x] 11.3 Create `tests/test_signals.py` for signal detection logic
- [x] 11.4 Create `tests/test_gann_hilo.py` for custom Gann HiLo implementation
- [x] 11.5 Verify signal logic against known Pine Script outputs
- [x] 11.6 Test cache hit/miss scenarios
- [x] 11.7 Test chart rendering with sample data
- [x] 11.8 Test error scenarios (API failures, malformed data)
- [x] 11.9 Achieve >80% test coverage on indicator and signal modules

## 12. Performance Optimization
- [x] 12.1 Benchmark indicator calculation time for 2000+ data points
- [x] 12.2 Optimize pandas operations (vectorization, avoid loops)
- [x] 12.3 Implement batch indicator calculation
- [x] 12.4 Add progress tracking for long-running calculations
- [x] 12.5 Profile chart rendering performance

## 13. Documentation
- [x] 13.1 Document API integration patterns
- [x] 13.2 Document indicator formulas and parameters
- [x] 13.3 Document signal logic with examples
- [x] 13.4 Add docstrings to all functions and classes
- [x] 13.5 Create usage guide for Chart Analysis tab

## 14. Integration & Deployment
- [x] 14.1 Integrate Chart Analysis tab into main app.py
- [x] 14.2 Test full workflow: select ticker → load data → calculate → render chart
- [x] 14.3 Test with multiple tickers (AAPL, TSLA, MSFT, etc.)
- [x] 14.4 Verify cache persistence across app restarts
- [x] 14.5 Test signal accuracy with historical data
- [x] 14.6 Perform end-to-end user acceptance testing
