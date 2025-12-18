# Chart Analysis Specification

## ADDED Requirements

### Requirement: Financial Modeling Prep API Integration
The system SHALL integrate with Financial Modeling Prep API to fetch historical end-of-day price data for stock tickers.

#### Scenario: Successful API data fetch
- **WHEN** the system requests historical data for ticker "AAPL"
- **THEN** the system SHALL make a GET request to the FMP EOD endpoint with the ticker symbol and API key
- **AND** the system SHALL receive JSON response with OHLCV data
- **AND** the system SHALL parse the response into a pandas DataFrame with columns: date, open, high, low, close, volume

#### Scenario: API request with invalid ticker
- **WHEN** the system requests data for an invalid ticker symbol
- **THEN** the API SHALL return a 404 status code
- **AND** the system SHALL display an error message "Ticker not found: [SYMBOL]"
- **AND** the system SHALL not crash or display raw error traces

#### Scenario: API rate limit exceeded
- **WHEN** the system makes more than 250 requests in one day
- **THEN** the API SHALL return a 429 status code
- **AND** the system SHALL display an error message indicating rate limit exceeded
- **AND** the system SHALL suggest using cached data or trying again tomorrow

#### Scenario: API request timeout
- **WHEN** an API request takes longer than 30 seconds
- **THEN** the system SHALL timeout the request
- **AND** the system SHALL retry up to 3 times with exponential backoff
- **AND** if all retries fail, the system SHALL display a network error message

### Requirement: Intelligent Price Data Caching
The system SHALL implement an intelligent caching strategy that treats historical EOD data as immutable and refreshes only current day data.

#### Scenario: Cache hit for historical data
- **WHEN** the system needs price data for "TSLA" from 2025-01-01 to 2025-06-01
- **AND** all dates are already cached in the price_cache table
- **THEN** the system SHALL retrieve data from cache without making an API call
- **AND** the cache retrieval SHALL complete in less than 500 milliseconds

#### Scenario: Partial cache hit with missing dates
- **WHEN** the system needs data from 2025-01-01 to 2025-11-30
- **AND** only data through 2025-06-01 is cached
- **THEN** the system SHALL fetch missing dates from 2025-06-02 to 2025-11-30 from API
- **AND** the system SHALL merge cached and new data
- **AND** the system SHALL store new data in price_cache table

#### Scenario: Today's date always refreshed
- **WHEN** the system loads a chart on 2025-11-30
- **AND** 2025-11-30 data exists in cache
- **THEN** the system SHALL still fetch fresh data from API for 2025-11-30
- **AND** the system SHALL update the cached record with latest values
- **AND** all historical dates SHALL use cached data

#### Scenario: Cache storage with foreign key integrity
- **WHEN** the system stores price data in cache
- **THEN** each record SHALL reference the ticker_id from the tickers table
- **AND** the system SHALL enforce the unique constraint on (ticker_id, date)
- **AND** duplicate date inserts SHALL update the existing record (upsert behavior)

### Requirement: MACD Indicator Calculation
The system SHALL calculate the Moving Average Convergence Divergence (MACD) indicator using standard parameters.

#### Scenario: MACD calculation with sufficient data
- **WHEN** the system has at least 34 bars of price data (26 slow + 9 signal)
- **THEN** the system SHALL calculate MACD line using 12-period fast EMA and 26-period slow EMA
- **AND** the system SHALL calculate signal line using 9-period EMA of MACD line
- **AND** the system SHALL add columns MACD_12_26_9 and MACDs_12_26_9 to the DataFrame

#### Scenario: MACD with insufficient data
- **WHEN** the system has fewer than 34 bars of data
- **THEN** the system SHALL still calculate MACD
- **AND** the first N rows SHALL contain NaN values for MACD and signal line
- **AND** the system SHALL handle NaN values gracefully in signal detection

### Requirement: RSI with Moving Average Calculation
The system SHALL calculate the Relative Strength Index (RSI) and its moving average for momentum analysis.

#### Scenario: RSI calculation with 14-period length
- **WHEN** the system calculates RSI with 14-period length
- **THEN** the system SHALL use standard RSI formula (average gains / average losses)
- **AND** the system SHALL add column RSI_14 to the DataFrame
- **AND** the system SHALL calculate a 14-period SMA of the RSI values
- **AND** the system SHALL add column rsi_ma to the DataFrame

### Requirement: Supertrend Indicator Calculation
The system SHALL calculate the Supertrend indicator for trend direction confirmation.

#### Scenario: Supertrend calculation with ATR
- **WHEN** the system calculates Supertrend with ATR length=10 and multiplier=3.0
- **THEN** the system SHALL calculate the Average True Range (ATR) over 10 periods
- **AND** the system SHALL calculate upper and lower bands based on ATR
- **AND** the system SHALL determine trend direction (bullish if price above Supertrend, bearish if below)
- **AND** the system SHALL add column SUPERT_10_3.0 to the DataFrame

### Requirement: Ichimoku Cloud Calculation
The system SHALL calculate all components of the Ichimoku Cloud indicator including Tenkan-sen, Kijun-sen, Senkou Span A, and Senkou Span B.

#### Scenario: Ichimoku calculation with standard parameters
- **WHEN** the system calculates Ichimoku with conversion=9, base=26, lagging=52, displacement=26
- **THEN** the system SHALL calculate Tenkan-sen (conversion line) as (9-period high + 9-period low) / 2
- **AND** the system SHALL calculate Kijun-sen (base line) as (26-period high + 26-period low) / 2
- **AND** the system SHALL calculate Senkou Span A as (Tenkan-sen + Kijun-sen) / 2
- **AND** the system SHALL calculate Senkou Span B as (52-period high + 52-period low) / 2
- **AND** the system SHALL add columns ISA_9 and ISB_26 to the DataFrame

#### Scenario: Ichimoku cloud entry detection
- **WHEN** the system checks if price is inside the Ichimoku cloud
- **THEN** price is in cloud if it is between ISA_9 and ISB_26 (shifted by 26 periods)
- **AND** the system SHALL handle both scenarios (price between A→B and B→A)

### Requirement: Gann HiLo Activator Calculation
The system SHALL implement the Gann HiLo Activator indicator using custom logic based on Pine Script specification.

#### Scenario: Gann HiLo calculation with high and low periods
- **WHEN** the system calculates Gann HiLo with high_period=13 and low_period=21
- **THEN** the system SHALL calculate SMA of high over 13 periods
- **AND** the system SHALL calculate SMA of low over 21 periods
- **AND** the system SHALL determine direction: 1 if close > SMA(high)[previous], -1 if close < SMA(low)[previous]
- **AND** the system SHALL forward-fill the direction when it's 0
- **AND** the system SHALL set HiLo line to SMA(high) if direction=-1, else SMA(low)
- **AND** the system SHALL add column gann_hilo to the DataFrame

#### Scenario: Gann HiLo direction persistence
- **WHEN** close price doesn't cross either SMA threshold
- **THEN** the system SHALL maintain the previous direction value
- **AND** the HiLo line SHALL remain on the last determined level until a crossover occurs

### Requirement: EMA Overlays Calculation
The system SHALL calculate Exponential Moving Averages for 8, 21, and 50 periods to display as price overlays.

#### Scenario: Multi-period EMA calculation
- **WHEN** the system calculates EMAs for overlay display
- **THEN** the system SHALL calculate 8-period EMA of close prices
- **AND** the system SHALL calculate 21-period EMA of close prices
- **AND** the system SHALL calculate 50-period EMA of close prices
- **AND** the system SHALL add columns ema_8, ema_21, ema_50 to the DataFrame

### Requirement: Volume Moving Average Calculation
The system SHALL calculate a 20-period moving average of volume for the volume cloud visualization.

#### Scenario: Volume MA calculation
- **WHEN** the system calculates volume moving average
- **THEN** the system SHALL calculate a 20-period simple moving average of volume
- **AND** the system SHALL add column volume_ma_20 to the DataFrame

### Requirement: Long OPEN Signal Detection
The system SHALL detect Long OPEN signals when all five bullish conditions are simultaneously met.

#### Scenario: All Long OPEN conditions satisfied
- **WHEN** MACD line is above signal line
- **AND** close price is above Gann HiLo line
- **AND** RSI is above its moving average
- **AND** close price is above Supertrend line
- **AND** current close is above previous bar's high
- **THEN** the system SHALL flag this bar with long_open=True
- **AND** the system SHALL mark this point for signal visualization

#### Scenario: One Long OPEN condition fails
- **WHEN** four conditions are satisfied but RSI is below its moving average
- **THEN** the system SHALL NOT flag this bar as Long OPEN
- **AND** no signal marker SHALL be displayed for this bar

### Requirement: Long CLOSE Signal Detection
The system SHALL detect Long CLOSE signals when any one of three exit conditions is triggered.

#### Scenario: Long CLOSE triggered by MACD reversal
- **WHEN** an active long position exists (conceptually)
- **AND** MACD line crosses below signal line
- **THEN** the system SHALL flag this bar with long_close=True
- **AND** the system SHALL mark this point for exit signal visualization

#### Scenario: Long CLOSE triggered by price entering cloud
- **WHEN** close price enters the Ichimoku cloud (between Senkou Span A and B)
- **THEN** the system SHALL flag this bar with long_close=True
- **AND** this SHALL trigger exit regardless of other conditions

#### Scenario: Long CLOSE triggered by Gann HiLo break
- **WHEN** close price drops below Gann HiLo line
- **THEN** the system SHALL flag this bar with long_close=True
- **AND** this indicates support break requiring exit

### Requirement: Short OPEN Signal Detection
The system SHALL detect Short OPEN signals when all six bearish conditions are simultaneously met.

#### Scenario: All Short OPEN conditions satisfied
- **WHEN** MACD line is below signal line
- **AND** MACD line is lower than previous bar's MACD (accelerating down)
- **AND** close price is below Gann HiLo line
- **AND** RSI is below its moving average
- **AND** close price is below Supertrend line
- **AND** current close is below previous bar's low
- **THEN** the system SHALL flag this bar with short_open=True
- **AND** the system SHALL mark this point for short entry visualization

#### Scenario: MACD not accelerating downward
- **WHEN** five conditions are met but MACD is equal to or higher than previous bar
- **THEN** the system SHALL NOT flag this bar as Short OPEN
- **AND** the system SHALL wait for momentum acceleration confirmation

### Requirement: Short CLOSE Signal Detection
The system SHALL detect Short CLOSE signals when any one of three exit conditions is triggered.

#### Scenario: Short CLOSE triggered by MACD reversal
- **WHEN** an active short position exists (conceptually)
- **AND** MACD line crosses above signal line
- **THEN** the system SHALL flag this bar with short_close=True
- **AND** the system SHALL mark this point for short exit visualization

#### Scenario: Short CLOSE triggered by Gann HiLo break
- **WHEN** close price breaks above Gann HiLo line
- **THEN** the system SHALL flag this bar with short_close=True
- **AND** this indicates resistance break requiring cover

#### Scenario: Short CLOSE triggered by cloud entry
- **WHEN** close price enters the Ichimoku cloud
- **THEN** the system SHALL flag this bar with short_close=True
- **AND** the system SHALL exit due to market uncertainty

### Requirement: Interactive Candlestick Chart Rendering
The system SHALL render interactive candlestick charts using Plotly with all calculated indicators and signals overlaid.

#### Scenario: Chart with candlesticks and EMAs
- **WHEN** the system renders a chart for a ticker
- **THEN** the chart SHALL display candlesticks with open, high, low, close prices
- **AND** the chart SHALL overlay EMA 8 in green
- **AND** the chart SHALL overlay EMA 21 in orange
- **AND** the chart SHALL overlay EMA 50 in red
- **AND** all lines SHALL be clearly distinguishable

#### Scenario: Chart with Gann HiLo and Supertrend
- **WHEN** the system renders indicator overlays
- **THEN** the chart SHALL display Gann HiLo as a blue dashed line
- **AND** the chart SHALL display Supertrend as a purple line
- **AND** indicator lines SHALL not obscure candlesticks

#### Scenario: Chart with Ichimoku Cloud
- **WHEN** the system renders the Ichimoku Cloud
- **THEN** the chart SHALL plot Senkou Span A shifted forward by 26 periods
- **AND** the chart SHALL plot Senkou Span B shifted forward by 26 periods
- **AND** the area between Span A and B SHALL be filled with semi-transparent color
- **AND** cloud color SHALL indicate bullish (green) or bearish (red) based on which span is higher

### Requirement: Trading Signal Marker Visualization
The system SHALL display visual markers on candlesticks to indicate trading signal events.

#### Scenario: Long OPEN signal markers
- **WHEN** a Long OPEN signal is detected on a specific date
- **THEN** the system SHALL display a green upward-pointing triangle below that candle
- **AND** the marker SHALL be positioned slightly below the candle low
- **AND** hovering over the marker SHALL show "Long OPEN" with date and price

#### Scenario: Long CLOSE signal markers
- **WHEN** a Long CLOSE signal is detected
- **THEN** the system SHALL display a red downward-pointing triangle above that candle
- **AND** the marker SHALL be positioned slightly above the candle high
- **AND** hover tooltip SHALL show "Long CLOSE" with date and price

#### Scenario: Short OPEN signal markers
- **WHEN** a Short OPEN signal is detected
- **THEN** the system SHALL display an orange downward-pointing triangle above that candle
- **AND** the marker SHALL be visually distinct from Long CLOSE markers

#### Scenario: Short CLOSE signal markers
- **WHEN** a Short CLOSE signal is detected
- **THEN** the system SHALL display a cyan upward-pointing triangle below that candle
- **AND** the marker SHALL be visually distinct from Long OPEN markers

### Requirement: Volume Subplot with MA Cloud
The system SHALL render a volume subplot below the price chart with volume bars and moving average cloud.

#### Scenario: Volume bars colored by price movement
- **WHEN** the system renders volume bars
- **THEN** bars SHALL be colored green if close > open (up day)
- **AND** bars SHALL be colored red if close < open (down day)
- **AND** volume scale SHALL be on the right y-axis

#### Scenario: Volume MA cloud visualization
- **WHEN** the system displays volume moving average
- **THEN** the chart SHALL plot a 20-period MA line in blue
- **AND** the area between volume bars and volume MA SHALL be filled with semi-transparent blue
- **AND** the cloud SHALL help identify volume surges relative to average

### Requirement: Chart Analysis Tab User Interface
The system SHALL provide a Chart Analysis tab with ticker selection and chart display capabilities.

#### Scenario: Ticker dropdown population
- **WHEN** the user navigates to the Chart Analysis tab
- **AND** tickers exist in the database
- **THEN** the system SHALL display a dropdown populated with all active ticker symbols
- **AND** the dropdown SHALL be sorted alphabetically

#### Scenario: Load chart button interaction
- **WHEN** the user selects a ticker from the dropdown
- **AND** clicks the "Load Chart" button
- **THEN** the system SHALL display a loading spinner
- **AND** the system SHALL fetch price data (with caching)
- **AND** the system SHALL calculate all indicators
- **AND** the system SHALL generate signals
- **AND** the system SHALL render the complete chart
- **AND** the entire process SHALL complete in less than 3 seconds for cached data

#### Scenario: Chart Analysis with no tickers available
- **WHEN** the user navigates to Chart Analysis tab
- **AND** no tickers exist in the database
- **THEN** the system SHALL display a warning message "No tickers found. Please add tickers in the Dashboard tab."
- **AND** the ticker dropdown SHALL be disabled

### Requirement: Signal Summary Display
The system SHALL display a summary of signal counts below the chart for quick analysis.

#### Scenario: Signal count metrics display
- **WHEN** a chart is successfully loaded with signals calculated
- **THEN** the system SHALL display four metric boxes showing:
  - Count of Long OPEN signals
  - Count of Long CLOSE signals
  - Count of Short OPEN signals
  - Count of Short CLOSE signals
- **AND** metrics SHALL be displayed in a horizontal row below the chart

### Requirement: Chart Interactivity Features
The system SHALL provide interactive chart features including zoom, pan, and hover tooltips.

#### Scenario: Zoom and pan functionality
- **WHEN** the user interacts with the chart
- **THEN** the user SHALL be able to zoom in on a specific date range by selecting an area
- **AND** the user SHALL be able to pan left/right to view different time periods
- **AND** the user SHALL be able to reset the view to default zoom

#### Scenario: Hover tooltips for data points
- **WHEN** the user hovers over any candle
- **THEN** the system SHALL display a tooltip with date, OHLC values, and volume
- **WHEN** the user hovers over an indicator line
- **THEN** the system SHALL display the indicator name and value
- **WHEN** the user hovers over a signal marker
- **THEN** the system SHALL display the signal type, date, and price

### Requirement: Error Handling for Chart Loading
The system SHALL handle errors gracefully during chart loading and display helpful messages to users.

#### Scenario: API failure during chart load
- **WHEN** the API request fails after all retries
- **THEN** the system SHALL display an error message "Failed to load data for [TICKER]. Please try again later."
- **AND** the system SHALL not crash or leave the UI in a broken state
- **AND** the previous chart (if any) SHALL remain displayed

#### Scenario: Indicator calculation failure
- **WHEN** indicator calculation fails due to insufficient data or errors
- **THEN** the system SHALL log the error with details
- **AND** the system SHALL display a user-friendly error message
- **AND** the system SHALL suggest checking the ticker symbol or trying a different ticker

### Requirement: Performance Standards for Chart Analysis
The system SHALL meet defined performance targets for chart loading and rendering operations.

#### Scenario: Cached data chart load performance
- **WHEN** all price data is cached for the selected ticker
- **THEN** the chart SHALL load and display in less than 3 seconds
- **AND** indicator calculations SHALL complete in less than 500 milliseconds
- **AND** signal generation SHALL complete in less than 100 milliseconds

#### Scenario: Uncached data chart load performance
- **WHEN** price data must be fetched from API
- **THEN** the complete operation SHALL finish in less than 5 seconds
- **AND** the system SHALL display progress feedback during the wait

#### Scenario: Large dataset handling
- **WHEN** the ticker has 2000+ daily bars (5+ years of data)
- **THEN** indicator calculations SHALL still complete in less than 1 second
- **AND** chart rendering SHALL complete without noticeable lag
- **AND** interactive features (zoom, pan) SHALL remain responsive
