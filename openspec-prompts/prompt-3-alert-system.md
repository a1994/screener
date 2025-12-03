# OpenSpec Prompt 3: Alert System & Signal Monitoring

## Context
Building on the ticker management (Proposal 1) and signal generation (Proposal 2) infrastructure, this proposal covers the automated alert system. The system will monitor all tickers in the database, detect the most recent trading signals (Long OPEN/CLOSE, Short OPEN/CLOSE), and display them in a dedicated Alerts tab with intelligent deduplication, sorting, and refresh capabilities.

## Problem Statement
Traders need a centralized alert dashboard to:
1. Monitor the latest trading signals across all tickers in their watchlist
2. See the most recent position status for each ticker (open/close events)
3. Avoid alert clutter by showing only relevant signals (maximum 2 alerts per ticker)
4. Refresh all ticker data on demand to catch new signals
5. Navigate through alerts efficiently with pagination

The system must handle signal lifecycle management (replacing old alerts when new positions open), maintain chronological ordering, and provide a clear view of current trading opportunities.

## Requirements

### 1. Alert Data Model

#### Database Schema Extension

##### New Table: `alerts`
```sql
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker_id INTEGER NOT NULL,
    ticker_symbol TEXT NOT NULL,
    alert_type TEXT NOT NULL CHECK(alert_type IN ('Long - OPEN', 'Long - CLOSE', 'Short - OPEN', 'Short - CLOSE')),
    signal_date DATE NOT NULL,
    price REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticker_id) REFERENCES tickers(id) ON DELETE CASCADE
);

CREATE INDEX idx_alerts_ticker_id ON alerts(ticker_id);
CREATE INDEX idx_alerts_signal_date ON alerts(signal_date DESC);
CREATE INDEX idx_alerts_created_at ON alerts(created_at DESC);
```

#### Alert Record Structure
Each alert represents a single signal event:
- **ticker_id**: Foreign key to tickers table
- **ticker_symbol**: Denormalized for quick display (avoid joins)
- **alert_type**: One of 4 signal types
- **signal_date**: The date when the signal occurred (from OHLC data)
- **price**: Close price on signal date
- **created_at**: When alert was inserted into database

### 2. Alert Generation Logic

#### Trigger Points (Option C: Both scenarios)
1. **On Ticker Addition**: When new tickers are added via Dashboard (Proposal 1)
   - Immediately fetch historical data
   - Calculate signals across entire dataset
   - Store most recent signals as alerts
   
2. **On Manual Refresh**: When user clicks "Refresh All" button in Alerts tab
   - Re-fetch data for all active tickers
   - Recalculate signals
   - Update alert records

#### Signal Processing Workflow
```python
def generate_alerts_for_ticker(ticker_id: int, ticker_symbol: str) -> List[Alert]:
    """
    Generate alerts for a single ticker
    
    Steps:
    1. Fetch latest price data (with caching)
    2. Calculate all indicators
    3. Generate signal DataFrame (from Proposal 2)
    4. Extract most recent signals
    5. Apply deduplication rules
    6. Return alert records
    """
    # Fetch data (uses cache from Proposal 2)
    df = fetch_price_data(ticker_symbol)
    
    # Calculate indicators and signals
    df = calculate_all_indicators(df)
    signals = generate_signals(df)
    
    # Find most recent signals
    recent_alerts = extract_recent_signals(df, signals, ticker_id, ticker_symbol)
    
    return recent_alerts
```

#### Alert Deduplication Rules (Option A)

**Rule: Maximum 2 alerts per ticker**
- One alert for the most recent position **OPEN** event (Long OPEN or Short OPEN)
- One alert for the most recent position **CLOSE** event (Long CLOSE or Short CLOSE)

**Deduplication Logic:**

1. **Scenario 1: New position opens**
   ```
   Before:
   TICKER | ALERT TYPE   | DATE
   HOOD   | Long - OPEN  | 2025-11-20
   HOOD   | Long - CLOSE | 2025-11-21
   
   New Signal: Long - OPEN on 2025-11-25
   
   After:
   TICKER | ALERT TYPE   | DATE
   HOOD   | Long - OPEN  | 2025-11-25  ← New alert
   (Previous Long OPEN and Long CLOSE deleted)
   ```

2. **Scenario 2: Position closes**
   ```
   Before:
   TICKER | ALERT TYPE   | DATE
   HOOD   | Long - OPEN  | 2025-11-25
   
   New Signal: Long - CLOSE on 2025-11-27
   
   After:
   TICKER | ALERT TYPE   | DATE
   HOOD   | Long - OPEN  | 2025-11-25
   HOOD   | Long - CLOSE | 2025-11-27  ← New alert added
   ```

3. **Scenario 3: Direction change (Long to Short)**
   ```
   Before:
   TICKER | ALERT TYPE   | DATE
   HOOD   | Long - OPEN  | 2025-11-25
   HOOD   | Long - CLOSE | 2025-11-27
   
   New Signal: Short - OPEN on 2025-11-28
   
   After:
   TICKER | ALERT TYPE   | DATE
   HOOD   | Short - OPEN | 2025-11-28  ← New alert, previous deleted
   ```

**Implementation:**
```python
def extract_recent_signals(df: pd.DataFrame, signals: pd.DataFrame, 
                          ticker_id: int, ticker_symbol: str) -> List[Dict]:
    """
    Extract most recent open and close signals
    
    Logic:
    1. Find most recent Long OPEN or Short OPEN (whichever is later)
    2. Find most recent Long CLOSE or Short CLOSE AFTER the open
    3. Return maximum 2 alerts
    """
    alerts = []
    
    # Get all signal dates
    long_opens = df[signals['long_open']].copy()
    long_closes = df[signals['long_close']].copy()
    short_opens = df[signals['short_open']].copy()
    short_closes = df[signals['short_close']].copy()
    
    # Find most recent OPEN (Long or Short)
    most_recent_long_open = long_opens['date'].max() if not long_opens.empty else None
    most_recent_short_open = short_opens['date'].max() if not short_opens.empty else None
    
    recent_open = None
    open_type = None
    
    if most_recent_long_open and most_recent_short_open:
        if most_recent_long_open > most_recent_short_open:
            recent_open = most_recent_long_open
            open_type = 'Long - OPEN'
        else:
            recent_open = most_recent_short_open
            open_type = 'Short - OPEN'
    elif most_recent_long_open:
        recent_open = most_recent_long_open
        open_type = 'Long - OPEN'
    elif most_recent_short_open:
        recent_open = most_recent_short_open
        open_type = 'Short - OPEN'
    
    # Add open alert
    if recent_open:
        open_price = df[df['date'] == recent_open]['close'].values[0]
        alerts.append({
            'ticker_id': ticker_id,
            'ticker_symbol': ticker_symbol,
            'alert_type': open_type,
            'signal_date': recent_open,
            'price': open_price
        })
        
        # Find corresponding close after open date
        if open_type == 'Long - OPEN':
            closes_after_open = long_closes[long_closes['date'] > recent_open]
        else:  # Short - OPEN
            closes_after_open = short_closes[short_closes['date'] > recent_open]
        
        if not closes_after_open.empty:
            most_recent_close = closes_after_open['date'].max()
            close_type = 'Long - CLOSE' if open_type == 'Long - OPEN' else 'Short - CLOSE'
            close_price = df[df['date'] == most_recent_close]['close'].values[0]
            
            alerts.append({
                'ticker_id': ticker_id,
                'ticker_symbol': ticker_symbol,
                'alert_type': close_type,
                'signal_date': most_recent_close,
                'price': close_price
            })
    
    return alerts
```

#### Alert Storage
```python
def update_alerts_for_ticker(ticker_id: int, ticker_symbol: str):
    """
    Update alerts for a ticker (replace old with new)
    
    Steps:
    1. Generate new alerts
    2. Delete all existing alerts for this ticker
    3. Insert new alerts
    4. Use transaction for atomicity
    """
    new_alerts = generate_alerts_for_ticker(ticker_id, ticker_symbol)
    
    with get_db_connection() as conn:
        # Delete old alerts
        conn.execute("DELETE FROM alerts WHERE ticker_id = ?", (ticker_id,))
        
        # Insert new alerts
        for alert in new_alerts:
            conn.execute("""
                INSERT INTO alerts (ticker_id, ticker_symbol, alert_type, signal_date, price)
                VALUES (?, ?, ?, ?, ?)
            """, (alert['ticker_id'], alert['ticker_symbol'], alert['alert_type'], 
                  alert['signal_date'], alert['price']))
        
        conn.commit()
```

### 3. Alerts Tab UI

#### Layout & Components
```python
with tab2:  # Alerts Tab
    st.title("🔔 Trading Alerts")
    
    # Header controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.subheader(f"Total Alerts: {get_total_alert_count()}")
    
    with col2:
        sort_order = st.selectbox(
            "Sort by",
            options=["Latest First", "Oldest First"],
            index=0
        )
    
    with col3:
        if st.button("🔄 Refresh All", type="primary"):
            refresh_all_alerts()
    
    # Alerts table
    display_alerts_table(sort_order)
```

#### Refresh All Functionality
```python
def refresh_all_alerts():
    """
    Refresh alerts for all active tickers
    
    Steps:
    1. Get all active tickers from database
    2. Show progress bar
    3. Update alerts for each ticker (with rate limiting)
    4. Display summary
    """
    tickers = get_all_active_tickers()
    total_tickers = len(tickers)
    
    if total_tickers == 0:
        st.warning("No tickers to refresh")
        return
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    success_count = 0
    error_count = 0
    errors = []
    
    for idx, (ticker_id, ticker_symbol) in enumerate(tickers):
        try:
            status_text.text(f"Refreshing {ticker_symbol} ({idx + 1}/{total_tickers})...")
            
            # Update alerts (includes API call with caching)
            update_alerts_for_ticker(ticker_id, ticker_symbol)
            success_count += 1
            
            # Rate limiting (avoid API throttling)
            time.sleep(0.5)  # 500ms between requests
            
        except Exception as e:
            error_count += 1
            errors.append(f"{ticker_symbol}: {str(e)}")
            
        progress_bar.progress((idx + 1) / total_tickers)
    
    progress_bar.empty()
    status_text.empty()
    
    # Display summary
    if success_count > 0:
        st.success(f"✅ Refreshed {success_count} tickers successfully")
    
    if error_count > 0:
        st.error(f"❌ Failed to refresh {error_count} tickers")
        with st.expander("View Errors"):
            for error in errors:
                st.text(error)
```

#### Alerts Table Display
```python
def display_alerts_table(sort_order: str):
    """
    Display paginated alerts table
    
    Features:
    - Sorted by date (latest first by default)
    - Paginated (20 alerts per page)
    - Color-coded alert types
    - Clickable ticker symbols (link to Chart Analysis tab)
    """
    # Get current page from session state
    if 'alert_page' not in st.session_state:
        st.session_state.alert_page = 1
    
    page_size = 20
    offset = (st.session_state.alert_page - 1) * page_size
    
    # Fetch alerts
    sort_direction = "DESC" if sort_order == "Latest First" else "ASC"
    alerts, total_count = get_paginated_alerts(page_size, offset, sort_direction)
    
    if not alerts:
        st.info("No alerts found. Add tickers and click 'Refresh All' to generate alerts.")
        return
    
    # Convert to DataFrame for display
    df = pd.DataFrame(alerts, columns=['Ticker', 'Alert Type', 'Date', 'Price'])
    
    # Apply styling
    def style_alert_type(val):
        if 'OPEN' in val:
            color = 'green' if 'Long' in val else 'orange'
        else:
            color = 'red' if 'Long' in val else 'cyan'
        return f'background-color: {color}; color: white; font-weight: bold'
    
    styled_df = df.style.applymap(style_alert_type, subset=['Alert Type'])
    
    # Display table
    st.dataframe(styled_df, use_container_width=True, height=600)
    
    # Pagination controls
    total_pages = (total_count + page_size - 1) // page_size
    
    col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
    
    with col1:
        if st.session_state.alert_page > 1:
            if st.button("← Previous"):
                st.session_state.alert_page -= 1
                st.rerun()
    
    with col2:
        st.write(f"Page {st.session_state.alert_page} of {total_pages}")
    
    with col3:
        st.write(f"Showing {len(alerts)} of {total_count} alerts")
    
    with col4:
        if st.session_state.alert_page < total_pages:
            if st.button("Next →"):
                st.session_state.alert_page += 1
                st.rerun()
```

#### Database Query for Paginated Alerts
```python
def get_paginated_alerts(page_size: int, offset: int, 
                        sort_direction: str = "DESC") -> Tuple[List, int]:
    """
    Fetch paginated alerts with sorting
    
    Returns:
        - List of alert tuples (ticker_symbol, alert_type, signal_date, price)
        - Total count of alerts
    """
    with get_db_connection() as conn:
        # Get total count
        total_count = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
        
        # Get paginated results
        query = f"""
            SELECT ticker_symbol, alert_type, signal_date, price
            FROM alerts
            ORDER BY signal_date {sort_direction}, created_at {sort_direction}
            LIMIT ? OFFSET ?
        """
        
        alerts = conn.execute(query, (page_size, offset)).fetchall()
        
        return alerts, total_count
```

### 4. Alert Generation on Ticker Addition

#### Integration with Ticker Management (Proposal 1)

Modify the `bulk_insert()` method in `TickerRepository`:
```python
def bulk_insert(self, tickers: List[str]) -> Dict[str, Any]:
    """
    Insert tickers and generate initial alerts
    
    Modified to trigger alert generation after successful insert
    """
    results = {
        'success': [],
        'duplicates': [],
        'errors': []
    }
    
    with get_db_connection() as conn:
        for ticker in tickers:
            try:
                # Insert ticker
                cursor = conn.execute(
                    "INSERT INTO tickers (symbol) VALUES (?)",
                    (ticker,)
                )
                ticker_id = cursor.lastrowid
                results['success'].append(ticker)
                
                # Generate alerts asynchronously (non-blocking)
                threading.Thread(
                    target=update_alerts_for_ticker,
                    args=(ticker_id, ticker)
                ).start()
                
            except sqlite3.IntegrityError:
                results['duplicates'].append(ticker)
            except Exception as e:
                results['errors'].append((ticker, str(e)))
        
        conn.commit()
    
    return results
```

**Note**: Alert generation runs in background thread to avoid blocking UI during bulk ticker addition.

### 5. Alert Filtering & Search (Future Enhancement)

Placeholder for future features:
- Filter by alert type (Long only, Short only, Open only, Close only)
- Search by ticker symbol
- Date range filter
- Export alerts to CSV

UI elements:
```python
# In Alerts Tab (above table)
with st.expander("🔍 Filters (Coming Soon)"):
    col1, col2 = st.columns(2)
    with col1:
        st.multiselect("Alert Types", 
                      options=['Long - OPEN', 'Long - CLOSE', 'Short - OPEN', 'Short - CLOSE'],
                      disabled=True)
    with col2:
        st.text_input("Search Ticker", disabled=True)
```

### 6. Code Organization

#### New/Modified Modules
```
screener/
├── database/
│   ├── alert_repository.py (NEW - Alert CRUD operations)
│   └── ticker_repository.py (MODIFIED - Add alert generation trigger)
├── alerts/
│   ├── __init__.py (NEW)
│   ├── generator.py (NEW - Alert generation logic)
│   ├── deduplicator.py (NEW - Alert deduplication rules)
│   └── refresher.py (NEW - Bulk refresh logic)
├── components/
│   ├── alerts_tab.py (NEW - Alerts Tab UI)
│   └── ...
└── tests/
    ├── test_alert_generation.py (NEW)
    └── test_deduplication.py (NEW)
```

#### Key Classes

##### AlertGenerator (alerts/generator.py)
```python
class AlertGenerator:
    def __init__(self, fmp_client: FMPClient, indicator_calculator: IndicatorCalculator):
        self.fmp_client = fmp_client
        self.indicator_calculator = indicator_calculator
        
    def generate_for_ticker(self, ticker_id: int, ticker_symbol: str) -> List[Alert]:
        """Generate alerts for single ticker"""
        
    def generate_for_all_tickers(self) -> Dict[str, Any]:
        """Generate alerts for all active tickers (Refresh All)"""
```

##### AlertDeduplicator (alerts/deduplicator.py)
```python
class AlertDeduplicator:
    @staticmethod
    def extract_recent_signals(df: pd.DataFrame, signals: pd.DataFrame, 
                               ticker_id: int, ticker_symbol: str) -> List[Dict]:
        """Apply deduplication rules and extract max 2 alerts"""
        
    @staticmethod
    def get_most_recent_open(long_opens: pd.DataFrame, 
                            short_opens: pd.DataFrame) -> Tuple[Optional[date], Optional[str]]:
        """Determine most recent open signal"""
```

##### AlertRepository (database/alert_repository.py)
```python
class AlertRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        
    def get_all(self, page_size: int, offset: int, 
               sort_direction: str) -> Tuple[List, int]:
        """Fetch paginated alerts"""
        
    def update_for_ticker(self, ticker_id: int, alerts: List[Dict]):
        """Replace alerts for a ticker"""
        
    def delete_for_ticker(self, ticker_id: int):
        """Delete all alerts for a ticker (when ticker is deleted)"""
        
    def get_total_count(self) -> int:
        """Get total alert count"""
```

##### AlertRefresher (alerts/refresher.py)
```python
class AlertRefresher:
    def __init__(self, alert_generator: AlertGenerator, alert_repository: AlertRepository):
        self.alert_generator = alert_generator
        self.alert_repository = alert_repository
        
    def refresh_all(self, progress_callback: Callable = None) -> Dict[str, Any]:
        """
        Refresh alerts for all tickers
        
        Args:
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with success/error counts and details
        """
```

### 7. Performance Considerations

#### Rate Limiting for API Calls
- Financial Modeling Prep API: 250 requests/day (free tier)
- Implement exponential backoff on errors
- Add configurable delay between requests (default: 500ms)
- Show remaining API quota in UI

#### Optimization Strategies
1. **Caching**: Leverage Proposal 2's caching (EOD data doesn't change)
2. **Batch Processing**: Group ticker refreshes in batches of 10
3. **Async Processing**: Use threading for background alert generation
4. **Incremental Updates**: Only recalculate signals for new data

#### Database Indexing
- Index on `signal_date DESC` for fast sorting
- Index on `ticker_id` for deduplication queries
- Composite index on `(ticker_id, signal_date)` for updates

### 8. Error Handling & Edge Cases

#### Edge Cases
1. **No signals found for ticker**: Don't create alert record, log warning
2. **API rate limit exceeded**: Queue remaining tickers, notify user
3. **Invalid price data**: Skip ticker, log error, continue with others
4. **Ticker deleted during refresh**: Handle gracefully (foreign key cascade)
5. **Multiple open signals on same day**: Use first occurrence

#### Error Recovery
- Failed refreshes don't affect existing alerts
- Transaction rollback on database errors
- Detailed error logging for debugging
- User-friendly error messages in UI

### 9. Testing Strategy

#### Unit Tests
1. Test deduplication logic with various signal patterns
2. Test alert generation with mock price data
3. Test pagination calculations
4. Test sorting in both directions

#### Integration Tests
1. Test full refresh cycle (API → calculation → storage → display)
2. Test alert lifecycle (create → update → delete)
3. Test concurrent ticker additions with alert generation
4. Test cache integration with alert refresh

#### Test Scenarios
```python
# Example test cases
def test_deduplication_long_to_short_transition():
    """Verify old long alerts deleted when short signal appears"""
    
def test_refresh_all_with_partial_failures():
    """Ensure successful refreshes saved when some fail"""
    
def test_pagination_boundary_conditions():
    """Test pagination with 0 alerts, 1 alert, exact page size, etc."""
    
def test_alert_generation_on_ticker_add():
    """Verify alerts created automatically when ticker added"""
```

## Technical Constraints
- SQLite transactions must be atomic (all-or-nothing alert updates)
- Refresh All should complete within 5 minutes for 100 tickers
- Pagination should handle 10,000+ alerts without performance issues
- Alert table should maintain referential integrity (cascade deletes)
- Background alert generation should not block main UI thread

## Success Criteria
1. Maximum 2 alerts per ticker enforced at all times
2. Alerts sorted chronologically (latest first) by default
3. Refresh All successfully updates >95% of tickers (excluding API failures)
4. Pagination works correctly for any number of alerts
5. Alert generation on ticker addition completes in background without UI freeze
6. Duplicate alerts never appear in database (verified by constraint tests)
7. Alert display loads in <1 second for 1000+ alerts

## Non-Goals (Out of Scope)
- Email/SMS notifications for new alerts
- Custom alert rules (e.g., "alert only on Long OPEN")
- Alert history tracking (only current alerts stored)
- Multi-user alert management
- Alert priority levels
- Alert acknowledgment/dismissal

## Dependencies on Other Proposals
- **Depends on Proposal 1**: Ticker database, ticker addition flow
- **Depends on Proposal 2**: Price data fetching, indicator calculation, signal generation

## Reference Materials
- SQLite Foreign Keys: https://www.sqlite.org/foreignkeys.html
- SQLite Transactions: https://www.sqlite.org/lang_transaction.html
- Streamlit Progress Bar: https://docs.streamlit.io/library/api-reference/status/st.progress
- Threading in Python: https://docs.python.org/3/library/threading.html

## Open Questions
1. Should we add alert notifications (browser notifications when new alert appears)?
2. Do we need an "alert history" table to track past alerts?
3. Should "Refresh All" be manual only, or add automatic scheduled refresh (e.g., nightly)?
4. Maximum age for alerts? (e.g., delete alerts older than 90 days automatically)
5. Should we display alert count per ticker in Dashboard tab?

---

**Next Steps After Approval:**
- Detailed technical specification
- Database migration script for `alerts` table
- Alert deduplication rule test cases
- API rate limiting configuration
- Implementation task breakdown
- Integration points with Proposals 1 & 2 finalization
