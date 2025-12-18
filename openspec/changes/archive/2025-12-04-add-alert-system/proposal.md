# Change: Add Alert System & Signal Monitoring

## Why
Traders need a centralized dashboard to monitor the latest trading signals across all tickers without manually loading each chart. The system must automatically detect signal events, maintain only relevant alerts per ticker, and provide bulk refresh capabilities for portfolio-wide signal monitoring.

## What Changes
- Add alerts table to database with foreign key to tickers table
- Implement alert generation logic that extracts most recent signals from historical data
- Create intelligent deduplication (max 2 alerts per ticker: one open + one close)
- Build Alerts tab UI with paginated, sortable alert table
- Add "Refresh All" functionality to batch-update alerts for all tickers
- Integrate alert generation with ticker addition workflow (background processing)
- Implement alert lifecycle management (auto-delete old alerts when new positions open)
- Add date-based sorting with latest alerts shown first

## Impact
- **Affected specs**: alert-system (new capability)
- **Affected code**:
  - New: `database/alert_repository.py` (alert CRUD operations)
  - New: `alerts/` module (generator.py, deduplicator.py, refresher.py)
  - New: `components/alerts_tab.py` (Alerts tab UI)
  - Modified: `database/ticker_repository.py` (trigger alert generation on insert)
  - Modified: `app.py` (integrate Alerts tab)
  - Modified: Database schema (add alerts table)
- **Breaking changes**: None (new functionality)
- **Dependencies**:
  - **Requires**: Proposal 1 (ticker-management) - needs ticker database
  - **Requires**: Proposal 2 (chart-analysis-signals) - needs signal generation logic
- **Performance impact**: Background alert generation uses threading to avoid UI blocking

## Success Criteria
- Maximum 2 alerts per ticker enforced at all times
- Alerts sorted chronologically (latest first) by default
- Refresh All successfully updates >95% of tickers (excluding API failures)
- Pagination works correctly for 1000+ alerts
- Alert generation on ticker addition completes in background without UI freeze
- Duplicate alerts never appear (verified by constraint tests)
- Alert display loads in <1 second for 1000+ alerts
