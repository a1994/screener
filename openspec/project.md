# Project Context

## Purpose
The SCREENER project is a Python-based stock screener built with Streamlit, designed to generate trading signals (Long - OPEN, Long - CLOSE, Short - OPEN, Short - CLOSE) based on a multi-indicator confirmation strategy. The core idea is to wait for multiple "green lights" (bullish signals) to align before entering long positions, and exit when any "red light" (bearish reversal) triggers. The strategy combines technical indicators including MACD, Gann HiLo, RSI, Supertrend, Ichimoku Cloud, and recent price action to identify high-probability trade entries and exits for stocks and other financial instruments.

## Tech Stack
- **Language**: Python
- **Frontend/UI**: Streamlit (for interactive web-based screener interface)
- **Data Processing**: pandas, numpy
- **Data Fetching**: yfinance (for Yahoo Finance API)
- **Technical Indicators**: ta-lib or pandas-ta (for MACD, RSI, Supertrend, Ichimoku Cloud); custom implementation for Gann HiLo if not available
- **Visualization**: matplotlib or plotly (via Streamlit for charts)
- **Database**: SQLite for caching historical data and user preferences
- **Deployment**: Docker for containerization, potentially hosted on cloud platforms like AWS or Heroku
- **Version Control**: Git with GitHub for collaboration
- **Documentation/Spec Management**: OpenSpec framework for managing project specifications and changes

## Project Conventions

### Code Style
- Follow PEP 8 for Python code (if Python is used)
- Use meaningful variable and function names
- Include docstrings for all functions and classes
- Consistent indentation and line length limits

### Architecture Patterns
- Modular design with separation of concerns (data fetching, analysis, presentation)
- Use of object-oriented programming where appropriate
- Event-driven architecture for real-time data updates (if applicable)

### Testing Strategy
- Unit tests for individual functions and modules using pytest (for Python)
- Integration tests for end-to-end workflows
- Aim for high test coverage (>80%) on critical components

### Git Workflow
- Use feature branches for new developments
- Commit messages should be descriptive and follow conventional commits (e.g., "feat: add new screening filter")
- Pull requests required for merging to main branch
- Use OpenSpec for managing change proposals and specifications

## Domain Context
- Financial markets operate 24/7 for some instruments (e.g., crypto), requiring consideration for time zones and market hours
- Data sources include free APIs (Yahoo Finance, Alpha Vantage) and paid services; handle API rate limits and data quality
- Regulatory compliance: Ensure no insider trading implications; data should be publicly available
- Risk management: Screening tools should include risk metrics like volatility, drawdown analysis

### Trading Strategy Overview
The strategy uses a multi-confirmation approach, requiring all "green lights" for entry and exiting on any "red light" to minimize false signals.

#### Long Entry (Bullish Signals)
1. **MACD Momentum**: MACD line crosses above its signal line (upward momentum shift).
2. **Price vs Gann HiLo**: Price is above the Gann HiLo line (short-term uptrend).
3. **RSI Strength**: RSI is higher than its moving average (strengthening momentum).
4. **Supertrend Direction**: Price is above the Supertrend line (confirmed uptrend).
5. **Recent Price Action**: Current close is higher than previous bar's high (immediate momentum).
- **Entry**: All 5 conditions met → Long OPEN.

#### Long Exit
- Exit if any of:
  1. MACD crosses below signal line (momentum fading).
  2. Price drops below Gann HiLo (support broken).
  3. Price enters Ichimoku cloud (uncertainty zone).
- **Exit**: Any condition met → Long CLOSE.

#### Short Entry (Bearish Signals)
1. **MACD Momentum**: MACD crosses below signal line (downward shift).
2. **Price vs Gann HiLo**: Price is below Gann HiLo (downtrend).
3. **MACD Acceleration**: MACD lower than previous bar (accelerating down).
4. **RSI Weakness**: RSI lower than its moving average (weak momentum).
5. **Supertrend Direction**: Price below Supertrend (confirmed downtrend).
6. **Recent Price Action**: Current close lower than previous bar's low (immediate down momentum).
- **Entry**: All conditions met → Short OPEN.

#### Short Exit
- Exit if any of:
  1. MACD crosses above signal line (momentum reversal).
  2. Price breaks above Gann HiLo (resistance broken).
  3. Price enters Ichimoku cloud (uncertainty).
- **Exit**: Any condition met → Short CLOSE.

This strategy emphasizes confirmation across multiple indicators to reduce noise and improve signal reliability.

## Important Constraints
- Data accuracy and timeliness: Financial data can be stale; implement caching and refresh mechanisms
- Performance: Large datasets (e.g., historical prices for thousands of stocks) require efficient algorithms
- Security: Handle user data and API keys securely; avoid storing sensitive financial information
- Scalability: Design for potential growth in data volume and user base

## External Dependencies
- Yahoo Finance API (via yfinance library) for historical stock data and real-time quotes
- Technical analysis libraries: ta-lib or pandas-ta for MACD, RSI, Supertrend, Ichimoku Cloud calculations
- Custom or third-party implementations for Gann HiLo activator (if not in standard libraries)
- Potentially Alpha Vantage or other APIs for additional data validation
