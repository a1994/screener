# Change: Add Chart Analysis & Trading Signal Visualization

## Why
Users need to visually analyze stock price movements and identify trading opportunities based on technical indicators. The system must fetch historical price data, calculate multi-indicator signals (MACD, RSI, Gann HiLo, Supertrend, Ichimoku Cloud), and display them on interactive charts to support informed trading decisions.

## What Changes
- Integrate Financial Modeling Prep API for historical EOD price data retrieval
- Implement intelligent caching strategy for API responses (EOD data immutable)
- Calculate technical indicators: MACD, RSI, Supertrend, Ichimoku Cloud, Gann HiLo Activator
- Add EMA overlays (8, 21, 50 periods) and Volume MA cloud (20-period)
- Implement trading signal logic (Long OPEN/CLOSE, Short OPEN/CLOSE) based on Pine Script strategy
- Create interactive Plotly candlestick charts with indicator overlays and signal markers
- Build Chart Analysis tab with ticker dropdown and chart rendering
- Calculate signals across entire historical dataset for comprehensive analysis

## Impact
- **Affected specs**: chart-analysis (new capability)
- **Affected code**:
  - New: `api/` module (fmp_client.py, cache_manager.py)
  - New: `indicators/` module (calculator.py, gann_hilo.py, signals.py)
  - New: `charts/` module (plotly_renderer.py, formatters.py)
  - Modified: `components/chart_analysis.py` (new Chart Analysis tab)
  - Modified: `database/ticker_repository.py` (extend for price cache queries)
  - Modified: `app.py` (integrate Chart Analysis tab)
- **Breaking changes**: None (new functionality)
- **Dependencies**: 
  - **Requires**: Proposal 1 (ticker-management-infrastructure) - needs ticker database
  - **Required by**: Proposal 3 (alert-system) - signals used for alert generation
- **External APIs**: Financial Modeling Prep (250 requests/day free tier)

## Success Criteria
- Chart loads with all indicators in <3 seconds for cached data
- Signal calculations match Pine Script logic with 100% accuracy
- All 4 signal types (Long OPEN/CLOSE, Short OPEN/CLOSE) correctly identified
- Cache hit rate >90% for repeated ticker views
- Charts are interactive with zoom, pan, and hover tooltips
- Volume cloud is visually distinct
- Signal markers clearly visible on candles
