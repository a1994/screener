# Change: Add Ticker Management Infrastructure

## Why
The stock screener needs foundational infrastructure to manage user watchlists before implementing chart analysis and signal generation. Currently, there is no system to store, retrieve, or manage stock tickers, which is required for all downstream functionality.

## What Changes
- Add SQLite database with `tickers` and `price_cache` tables for persistent storage
- Implement ticker input via comma-separated strings and CSV file upload
- Create User Dashboard tab for ticker CRUD operations (view, filter, sort, delete)
- Build base Streamlit application structure with 3-tab navigation (Chart Analysis, Alerts, Dashboard)
- Add pagination for ticker list (50 tickers per page)
- Implement ticker validation and deduplication logic
- Create modular code architecture with separation of concerns (database, components, utils)

## Impact
- **Affected specs**: ticker-management (new capability)
- **Affected code**: 
  - New: `database/` module (db_manager.py, models.py, ticker_repository.py)
  - New: `components/` module (dashboard.py, ticker_input.py)
  - New: `utils/` module (validators.py, formatters.py)
  - New: `app.py` (main Streamlit entry point)
  - New: SQLite database file
- **Breaking changes**: None (new functionality)
- **Dependencies**: Required for Chart Analysis (Proposal 2) and Alert System (Proposal 3)

## Success Criteria
- User can add 100+ tickers via CSV in <5 seconds
- Dashboard loads and filters 1000+ tickers in <1 second
- No duplicate tickers can exist (enforced by UNIQUE constraint)
- All database operations are atomic with rollback on errors
- Unit test coverage >80% for database and validation logic
