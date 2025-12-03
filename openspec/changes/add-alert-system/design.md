# Design: Alert System & Signal Monitoring

## Context
The alert system provides a centralized monitoring dashboard for trading signals across the user's entire watchlist. It must intelligently deduplicate signals to show only the most relevant position information, support bulk updates efficiently, and integrate seamlessly with both ticker management and chart analysis systems.

**Constraints:**
- Maximum 2 alerts per ticker (one open + one close)
- Alerts must stay synchronized with chart signals
- Background processing must not block UI
- Support 100+ tickers with reasonable refresh time
- Use existing signal generation logic (no duplication)

## Goals / Non-Goals

**Goals:**
- Single source of truth for latest position signals
- Efficient bulk refresh for entire watchlist
- Clear alert lifecycle with automatic cleanup
- Fast alert display with pagination
- Automatic alert generation on ticker addition

**Non-Goals:**
- Email/SMS notifications
- Custom alert rules or filters
- Alert history tracking (only current state)
- Real-time alert updates (manual refresh only)
- Multi-user alert management

## Decisions

### Decision 1: Max 2 Alerts Per Ticker (Open + Close)
**Choice:** Enforce exactly 0-2 alerts per ticker (one position open, one position close)

**Rationale:**
- Focus on current position status, not full history
- Reduces noise (no duplicate open/close signals)
- Simpler UI (consistent structure per ticker)
- Clear action items for traders

**Deduplication Rules:**
1. Find most recent OPEN signal (Long or Short, whichever is later)
2. Find most recent CLOSE signal AFTER that open
3. When new OPEN appears, delete previous OPEN+CLOSE pair

**Example Flow:**
```
Initial: []

After Long OPEN on 2025-11-20:
[{HOOD, Long-OPEN, 2025-11-20}]

After Long CLOSE on 2025-11-21:
[{HOOD, Long-OPEN, 2025-11-20}, {HOOD, Long-CLOSE, 2025-11-21}]

After NEW Long OPEN on 2025-11-25:
[{HOOD, Long-OPEN, 2025-11-25}]  ← Previous pair deleted

After Short OPEN on 2025-11-28:
[{HOOD, Short-OPEN, 2025-11-28}]  ← Replaces Long open
```

### Decision 2: Denormalized ticker_symbol in alerts Table
**Choice:** Store ticker_symbol directly in alerts table (not just ticker_id)

**Rationale:**
- Avoids JOIN on every alert query
- Primary use case is display (read-heavy)
- Ticker symbols rarely change
- Faster pagination queries

**Trade-off:** 
- 10-20 bytes extra per alert
- Update complexity if ticker renamed (rare)
- Acceptable for performance gain

### Decision 3: Background Alert Generation on Ticker Add
**Choice:** Use threading.Thread() for async alert generation when tickers added

**Rationale:**
- Ticker insertion should be fast and responsive
- Alert generation may take 1-2 seconds per ticker (API + calc)
- User doesn't need alerts immediately (can view later)
- Non-blocking UX is critical

**Implementation:**
```python
# In ticker_repository.py bulk_insert()
for ticker in tickers:
    ticker_id = insert_ticker(ticker)
    
    # Generate alerts in background
    threading.Thread(
        target=update_alerts_for_ticker,
        args=(ticker_id, ticker),
        daemon=True
    ).start()
```

**Risk:** Thread failure is silent
**Mitigation:** Log errors, user can manually refresh later

### Decision 4: Synchronous Refresh All with Progress
**Choice:** Block UI with progress bar during Refresh All (not async)

**Rationale:**
- User explicitly requested refresh (expects to wait)
- Progress feedback is valuable (50 of 100 tickers...)
- Simpler error handling (immediate feedback)
- Prevents concurrent refresh conflicts

**Performance Target:** 100 tickers in <5 minutes (with 500ms rate limiting)

### Decision 5: Reuse Signal Generation from Chart Analysis
**Choice:** Import and reuse SignalDetector from indicators module

**Rationale:**
- Single source of truth for signal logic
- No code duplication
- Guaranteed consistency between charts and alerts
- Shared caching benefits

**Architecture:**
```
alerts/generator.py
    ↓ imports
indicators/signals.py (from chart-analysis)
    ↓ uses
indicators/calculator.py (from chart-analysis)
    ↓ uses
api/cache_manager.py (from chart-analysis)
```

### Decision 6: Sort by signal_date DESC (Default)
**Choice:** Always show latest signals first by default

**Rationale:**
- Most recent signals are most actionable
- Users care about "what happened today/this week"
- Historical signals less relevant for trading decisions
- Consistent with alert semantics (not a log)

**Implementation:** SQL `ORDER BY signal_date DESC, created_at DESC`

### Decision 7: Pagination at 20 Alerts Per Page
**Choice:** Show 20 alerts per page (vs 50 for tickers)

**Rationale:**
- Alerts include more columns (date, type, price)
- Smaller page size improves readability
- Faster page loads
- Consistent with typical alert volumes (2 per ticker = 100 alerts for 50 tickers)

## Data Model

### Alerts Table Schema
```sql
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker_id INTEGER NOT NULL,
    ticker_symbol TEXT NOT NULL,              -- Denormalized for performance
    alert_type TEXT NOT NULL CHECK(
        alert_type IN ('Long - OPEN', 'Long - CLOSE', 'Short - OPEN', 'Short - CLOSE')
    ),
    signal_date DATE NOT NULL,                -- Date of signal occurrence
    price REAL,                               -- Close price on signal date
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticker_id) REFERENCES tickers(id) ON DELETE CASCADE
);

CREATE INDEX idx_alerts_ticker_id ON alerts(ticker_id);
CREATE INDEX idx_alerts_signal_date ON alerts(signal_date DESC);
CREATE INDEX idx_alerts_created_at ON alerts(created_at DESC);
```

**Key Points:**
- Foreign key CASCADE delete (ticker removed → alerts removed)
- CHECK constraint ensures valid alert types
- Indexes optimize pagination and filtering
- No UNIQUE constraint (replaced atomically via delete+insert)

## Alert Deduplication Algorithm

```python
def extract_recent_signals(df: pd.DataFrame, signals: pd.DataFrame, 
                          ticker_id: int, ticker_symbol: str) -> List[Dict]:
    """
    Extract max 2 alerts: most recent OPEN + its corresponding CLOSE
    
    Logic:
    1. Find most recent Long OPEN and Short OPEN
    2. Choose whichever is later (most recent position direction)
    3. Find CLOSE signal that occurred AFTER that open
    4. Return [open_alert] or [open_alert, close_alert]
    """
    alerts = []
    
    # Extract signal dates
    long_opens = df[signals['long_open']]['date']
    long_closes = df[signals['long_close']]['date']
    short_opens = df[signals['short_open']]['date']
    short_closes = df[signals['short_close']]['date']
    
    # Find most recent OPEN (Long vs Short)
    recent_long_open = long_opens.max() if not long_opens.empty else None
    recent_short_open = short_opens.max() if not short_opens.empty else None
    
    if recent_long_open is None and recent_short_open is None:
        return []  # No signals found
    
    # Determine which open is most recent
    if recent_long_open and recent_short_open:
        if recent_long_open > recent_short_open:
            recent_open_date = recent_long_open
            open_type = 'Long - OPEN'
            close_signals = long_closes
            close_type = 'Long - CLOSE'
        else:
            recent_open_date = recent_short_open
            open_type = 'Short - OPEN'
            close_signals = short_closes
            close_type = 'Short - CLOSE'
    elif recent_long_open:
        recent_open_date = recent_long_open
        open_type = 'Long - OPEN'
        close_signals = long_closes
        close_type = 'Long - CLOSE'
    else:
        recent_open_date = recent_short_open
        open_type = 'Short - OPEN'
        close_signals = short_closes
        close_type = 'Short - CLOSE'
    
    # Add OPEN alert
    open_price = df[df['date'] == recent_open_date]['close'].values[0]
    alerts.append({
        'ticker_id': ticker_id,
        'ticker_symbol': ticker_symbol,
        'alert_type': open_type,
        'signal_date': recent_open_date,
        'price': open_price
    })
    
    # Find CLOSE after OPEN
    closes_after_open = close_signals[close_signals > recent_open_date]
    if not closes_after_open.empty:
        recent_close_date = closes_after_open.max()
        close_price = df[df['date'] == recent_close_date]['close'].values[0]
        
        alerts.append({
            'ticker_id': ticker_id,
            'ticker_symbol': ticker_symbol,
            'alert_type': close_type,
            'signal_date': recent_close_date,
            'price': close_price
        })
    
    return alerts
```

## Alert Update Flow

### Scenario: Ticker Added (Background)
```
User adds AAPL in Dashboard
    ↓
ticker_repository.bulk_insert()
    ↓
Thread.start(generate_alerts_for_ticker, args=(ticker_id, "AAPL"))
    ↓ (background thread)
Fetch price data → Calculate indicators → Generate signals
    ↓
extract_recent_signals() → returns [Long-OPEN on 2025-11-15]
    ↓
DELETE FROM alerts WHERE ticker_id = ?
INSERT INTO alerts (...) VALUES (...)
    ↓
Done (user sees in Alerts tab when they navigate there)
```

### Scenario: Refresh All (Foreground)
```
User clicks "Refresh All" button
    ↓
Display progress bar (0%)
    ↓
FOR EACH ticker in database:
    ↓
    Update status: "Refreshing AAPL (1 of 50)..."
    ↓
    Fetch data (with cache) → Calculate → Generate signals
    ↓
    Extract recent alerts
    ↓
    DELETE + INSERT atomically
    ↓
    Update progress: 2% complete
    ↓
    Sleep 500ms (rate limiting)
    ↓
NEXT ticker
    ↓
Hide progress bar
Display summary: "✅ 48 succeeded, ❌ 2 failed"
```

## Performance Optimization

### Database Query Optimization
```sql
-- Paginated alerts with sorting (optimized with indexes)
SELECT ticker_symbol, alert_type, signal_date, price
FROM alerts
ORDER BY signal_date DESC, created_at DESC
LIMIT 20 OFFSET ?;

-- Total count (separate query, cached in session state)
SELECT COUNT(*) FROM alerts;
```

### Batch Processing
- Process tickers in batches of 10 (future optimization)
- Reuse API client session
- Bulk delete + insert in single transaction

### Caching Leverage
- 90%+ cache hit rate from chart-analysis module
- Only today's data refreshed from API
- Historical signals recalculated from cache (fast)

## Risks / Trade-offs

### Risk 1: Background Thread Failures Silent
**Risk:** Alert generation thread crashes, user doesn't know

**Mitigation:**
- Log all exceptions with traceback
- Add "last alert update" timestamp per ticker (future)
- Manual Refresh All always available

### Risk 2: Race Condition During Refresh All
**Risk:** User adds ticker while Refresh All is running

**Mitigation:**
- Disable "Add Ticker" during Refresh All (future)
- Or: Queue new tickers for next refresh
- Or: Accept that new ticker won't have alerts until next refresh

**Decision:** Accept limitation for MVP (simple implementation)

### Risk 3: Stale Alerts After Signal Logic Change
**Risk:** If signal logic updated in chart-analysis, alerts are stale

**Mitigation:**
- Run Refresh All after signal logic changes
- Document in release notes
- Consider alert version tracking (future)

### Risk 4: Deduplication Edge Cases
**Risk:** Multiple signals on same day, unclear which to keep

**Mitigation:**
- Use first occurrence (earliest time) if multiple on same date
- Document behavior in design doc
- Test with synthetic data

## Testing Strategy

### Unit Tests
1. **Alert Deduplication:**
   - Test: Long OPEN → Long CLOSE → new Long OPEN (deletes old pair)
   - Test: Long OPEN/CLOSE → Short OPEN (deletes Long pair)
   - Test: Only Long OPEN (no close yet)
   - Test: No signals at all

2. **Alert Repository:**
   - Test pagination calculations
   - Test sorting ASC/DESC
   - Test foreign key cascade delete
   - Test concurrent updates (threading)

### Integration Tests
1. End-to-end: Add ticker → wait → check alerts appear
2. Refresh All: 10 tickers → verify all updated
3. Ticker delete: verify alerts cascade deleted
4. Cache integration: verify no duplicate API calls

### Performance Tests
- 100 tickers Refresh All: <5 minutes
- 1000 alerts display: <1 second
- 10,000 alerts pagination: <1 second per page

## Open Questions

1. **Alert Age Limit**: Should alerts older than 90 days be auto-deleted?
   - **Recommendation:** No auto-delete for MVP, user can refresh to update

2. **Alert Notifications**: Should we add browser notifications when new alerts appear?
   - **Recommendation:** Defer to future enhancement

3. **Alert Filters**: Should we add filters (Long only, Short only, Open only, Close only)?
   - **Recommendation:** Nice-to-have, add after MVP if requested

4. **Alert History**: Should we track historical alerts in separate table?
   - **Recommendation:** Out of scope, current state only

5. **Refresh All Scheduling**: Should we add automatic nightly refresh?
   - **Recommendation:** Manual only for MVP, consider scheduled jobs later
