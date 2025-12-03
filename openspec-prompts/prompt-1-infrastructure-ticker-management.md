# OpenSpec Prompt 1: Core Infrastructure & Ticker Management

## Context
I'm building a Python-based stock screener web application using Streamlit. This is the first phase focusing on the foundational infrastructure, database design, and ticker management system. The application will eventually support multi-indicator trading signal analysis, but this proposal focuses on the core data management layer.

## Problem Statement
We need a robust system to:
1. Allow users to input stock tickers in bulk (via comma-separated strings or CSV file upload)
2. Store tickers persistently in a local SQLite database
3. Provide a user dashboard for ticker management (view, filter, sort, delete operations)
4. Establish the base Streamlit application structure with tab navigation

## Requirements

### 1. Database Schema Design
- **Technology**: SQLite (local, file-based database)
- **Primary Table**: `tickers`
  - Fields needed:
    - `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
    - `symbol` (TEXT UNIQUE NOT NULL) - Stock ticker symbol (e.g., "AAPL", "TSLA")
    - `added_date` (DATETIME DEFAULT CURRENT_TIMESTAMP) - When ticker was added
    - `last_updated` (DATETIME) - Last time data was refreshed for this ticker
    - `is_active` (BOOLEAN DEFAULT 1) - Soft delete flag
  - Indexes: Create index on `symbol` for fast lookups
  
- **Secondary Table**: `price_cache` (for future use, spec structure only)
  - Fields:
    - `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
    - `ticker_id` (INTEGER FOREIGN KEY to tickers.id)
    - `date` (DATE NOT NULL)
    - `open`, `high`, `low`, `close`, `volume` (REAL)
    - `cached_at` (DATETIME DEFAULT CURRENT_TIMESTAMP)
  - Indexes: Composite index on (`ticker_id`, `date`)

### 2. Ticker Input Methods

#### Method A: Comma-Separated String Input
- UI Component: `st.text_area()` for multi-line input
- Input format: "AAPL, TSLA, MSFT, GOOGL" (case-insensitive, whitespace-tolerant)
- Validation requirements:
  - Strip whitespace from each ticker
  - Convert to uppercase
  - Remove duplicates before insertion
  - Validate ticker format: alphanumeric, 1-5 characters typically
  - Show error for invalid formats
  - Display summary: "X tickers added, Y duplicates skipped, Z invalid"

#### Method B: CSV File Upload
- UI Component: `st.file_uploader(type=['csv'])`
- Expected CSV format:
  - Option 1: Single column with header "symbol" or "ticker"
  - Option 2: Single column without header (first column used)
- Processing requirements:
  - Parse CSV using pandas
  - Apply same validation as Method A
  - Handle encoding issues (try UTF-8, fallback to latin-1)
  - Show preview of first 10 tickers before confirmation
  - Batch insert with transaction handling

#### Shared Logic
- Create a `TickerManager` class with methods:
  - `parse_tickers(input_string: str) -> List[str]`
  - `validate_ticker(symbol: str) -> bool`
  - `bulk_insert(tickers: List[str]) -> Dict[str, Any]` (returns success/failure counts)
  - `check_duplicates(tickers: List[str]) -> Dict[str, List[str]]` (returns existing/new)

### 3. User Dashboard Tab

#### Features Required:
1. **Ticker List Display**
   - Show all active tickers in a `st.dataframe()` with columns:
     - Symbol
     - Added Date
     - Last Updated
     - Actions (delete button)
   - Display total count: "Managing X tickers"

2. **Filter/Sort Functionality**
   - Filter options:
     - Search by symbol (case-insensitive partial match)
     - Date range filter (added between X and Y)
   - Sort options:
     - By Symbol (A-Z, Z-A)
     - By Added Date (Newest first, Oldest first)
     - By Last Updated (Recently updated first)
   - Use `st.selectbox()` for sort, `st.text_input()` for search

3. **Delete Operations**
   - Individual delete: Button per row (soft delete: set `is_active = 0`)
   - Bulk delete: Multi-select with `st.multiselect()` + "Delete Selected" button
   - Confirmation dialog: Use `st.warning()` + confirm button
   - Success feedback: `st.success()` message with count

4. **Pagination**
   - Show 50 tickers per page by default
   - Navigation: "Previous" / "Next" buttons
   - Page indicator: "Page X of Y"
   - Use `st.session_state` to track current page

### 4. Streamlit Application Structure

#### Tab Layout
```python
tab1, tab2, tab3 = st.tabs(["Chart Analysis", "Alerts", "Dashboard"])

with tab1:
    # Chart Analysis (placeholder for Proposal 2)
    st.info("Chart analysis will be implemented in Phase 2")
    
with tab2:
    # Alerts (placeholder for Proposal 3)
    st.info("Alert system will be implemented in Phase 3")
    
with tab3:
    # User Dashboard (implement in this phase)
    render_dashboard()
```

#### Session State Management
- Initialize in main():
  - `st.session_state.db_connection`
  - `st.session_state.current_page`
  - `st.session_state.filter_settings`
  - `st.session_state.selected_tickers` (for bulk operations)

#### Error Handling
- Database connection errors: Show user-friendly message, log to file
- File upload errors: Validate file size (<5MB), format, encoding
- Network errors (future-proof): Graceful degradation

### 5. Code Organization

#### Directory Structure
```
screener/
├── app.py (main Streamlit entry point)
├── database/
│   ├── __init__.py
│   ├── db_manager.py (connection, migrations)
│   ├── models.py (table schemas)
│   └── ticker_repository.py (CRUD operations)
├── components/
│   ├── __init__.py
│   ├── dashboard.py (dashboard UI logic)
│   └── ticker_input.py (input forms)
├── utils/
│   ├── __init__.py
│   ├── validators.py (ticker validation)
│   └── formatters.py (display formatting)
├── config/
│   ├── __init__.py
│   └── settings.py (app configuration)
└── tests/
    ├── test_ticker_manager.py
    └── test_validators.py
```

#### Key Classes/Modules
1. `DatabaseManager` (database/db_manager.py)
   - Methods: `get_connection()`, `init_db()`, `migrate()`
   
2. `TickerRepository` (database/ticker_repository.py)
   - Methods: `add_ticker()`, `bulk_add()`, `get_all()`, `delete()`, `search()`, `filter_by_date()`
   
3. `DashboardComponent` (components/dashboard.py)
   - Methods: `render()`, `render_ticker_table()`, `render_filters()`, `handle_delete()`

## Technical Constraints
- Python 3.9+
- Streamlit 1.30+
- SQLite 3.x (included with Python)
- Follow PEP 8 style guidelines
- All database operations must use parameterized queries (SQL injection prevention)
- Use context managers for database connections
- Implement proper logging (Python `logging` module)

## Success Criteria
1. User can add 100+ tickers via CSV upload in <5 seconds
2. Database operations are atomic (rollback on errors)
3. Dashboard loads and filters 1000+ tickers in <1 second
4. No duplicate tickers can exist in database (enforced by UNIQUE constraint)
5. All ticker validation is consistent across input methods
6. Unit test coverage >80% for database and validation logic

## Non-Goals (Out of Scope for This Proposal)
- API integration for price data (covered in Proposal 2)
- Trading signal calculation (covered in Proposal 2)
- Alert generation system (covered in Proposal 3)
- User authentication/multi-user support
- Real-time data streaming

## Open Questions
1. Should we add a "ticker metadata" table for storing company name, sector, exchange? (Can be added later)
2. Do we need export functionality (export ticker list to CSV)? 
3. Should deleted tickers be permanently removed or soft-deleted? (Assuming soft-delete for now)
4. Maximum number of tickers to support? (Targeting 5,000 for this phase)

## Reference Materials
- PEP 8 Style Guide: https://peps.python.org/pep-0008/
- Streamlit Documentation: https://docs.streamlit.io/
- SQLite Best Practices: https://www.sqlite.org/lang.html

---

**Next Steps After Approval:**
This proposal will generate:
- Detailed technical specification
- Database migration scripts
- Implementation tasks with effort estimates
- Test plan with test cases
