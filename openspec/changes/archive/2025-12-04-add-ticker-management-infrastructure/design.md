# Design: Ticker Management Infrastructure

## Context
This is the foundational layer for the stock screener application. The system must reliably store and manage user watchlists (stock tickers) while providing a responsive UI for bulk operations. The design must support future features including chart analysis, signal generation, and alert management without requiring schema changes.

**Constraints:**
- Local SQLite database (no server infrastructure)
- Streamlit framework (single-page app with session state)
- Must handle 1000+ tickers efficiently
- No user authentication in initial phase (single-user system)

## Goals / Non-Goals

**Goals:**
- Persistent storage of ticker symbols with metadata
- Efficient bulk ticker input (100+ tickers at once)
- Fast retrieval and filtering of ticker lists
- Data integrity (no duplicates, referential integrity)
- Modular architecture for easy extension

**Non-Goals:**
- Real-time ticker validation against market data
- User authentication/multi-user support
- Ticker categorization (sectors, industries)
- Ticker metadata enrichment (company names, market cap)
- Automatic ticker discovery/suggestions

## Decisions

### Decision 1: SQLite for Data Persistence
**Choice:** Use SQLite with local file-based storage

**Rationale:**
- Zero configuration (no server setup required)
- Built into Python standard library
- ACID compliance for data integrity
- Sufficient performance for <10,000 tickers
- Easy backup (single file copy)

**Alternatives Considered:**
- PostgreSQL: Overkill for single-user application, requires server setup
- JSON files: No ACID guarantees, poor query performance, no referential integrity
- CSV files: No concurrent access control, no indexing

### Decision 2: Separate price_cache Table (Future-Proofing)
**Choice:** Create `price_cache` table in initial schema even though it won't be used until Proposal 2

**Rationale:**
- Avoids migration complexity later
- Establishes foreign key relationship from the start
- Documents intended data flow
- No performance penalty (empty table)

**Alternatives Considered:**
- Add in Proposal 2: Requires migration script, potential data backup issues
- Embed in single table: Violates normalization, poor query performance

### Decision 3: Soft Delete for Tickers
**Choice:** Use `is_active` boolean flag instead of hard deletes

**Rationale:**
- Preserves historical data for price_cache foreign keys
- Allows "undo" functionality in future
- Maintains referential integrity with related records
- Simplifies cascade logic

**Alternatives Considered:**
- Hard delete with CASCADE: Loses historical price data
- Move to deleted_tickers table: Adds complexity, requires trigger logic

### Decision 4: Denormalized ticker_symbol in alerts (Proposal 3)
**Choice:** Store ticker symbol directly in alerts table (not just ticker_id)

**Rationale:**
- Avoids JOIN on every alert query
- Faster alert display (main use case)
- Ticker symbols rarely change
- Simplifies alert queries

**Trade-offs:**
- 10-20 bytes extra per alert
- Update complexity if ticker symbol changes (rare edge case)

### Decision 5: Streamlit Session State for UI State
**Choice:** Use `st.session_state` for pagination, filters, selected items

**Rationale:**
- Native Streamlit feature
- Persists across reruns within session
- Avoids database round-trips for UI state

**Alternatives Considered:**
- Store in database: Too many writes, performance overhead
- URL query parameters: Poor UX for complex state, limited size

### Decision 6: Synchronous Ticker Input
**Choice:** Block UI during ticker insertion (show progress bar)

**Rationale:**
- Simplifies error handling (immediate feedback)
- Insertion is fast (<5 seconds for 100 tickers)
- Prevents race conditions with concurrent operations

**Alternatives Considered:**
- Async with background tasks: Overkill for small operation, complex error handling
- Batch queue: Adds complexity, user must wait anyway

### Decision 7: Modular Code Architecture
**Choice:** Separate concerns into distinct modules:
- `database/` - Data layer
- `components/` - UI layer
- `utils/` - Business logic
- `config/` - Configuration

**Rationale:**
- Testability (isolate database logic)
- Reusability (components used across tabs)
- Maintainability (clear boundaries)
- Follows Streamlit best practices

## Data Model

### Tickers Table
```sql
CREATE TABLE tickers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT UNIQUE NOT NULL,           -- Ticker symbol (e.g., "AAPL")
    added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_updated DATETIME,                  -- Last data refresh time
    is_active BOOLEAN DEFAULT 1            -- Soft delete flag
);

CREATE INDEX idx_tickers_symbol ON tickers(symbol);
CREATE INDEX idx_tickers_is_active ON tickers(is_active);
```

**Key Points:**
- `symbol` has UNIQUE constraint (prevents duplicates)
- `is_active` defaults to 1 (active)
- Indexes on frequently filtered columns

### Price Cache Table (for Proposal 2)
```sql
CREATE TABLE price_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker_id INTEGER NOT NULL,
    date DATE NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    cached_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticker_id) REFERENCES tickers(id) ON DELETE CASCADE,
    UNIQUE(ticker_id, date)                -- One record per ticker per day
);

CREATE INDEX idx_price_cache_ticker_date ON price_cache(ticker_id, date);
```

**Key Points:**
- Foreign key ensures referential integrity
- Composite UNIQUE constraint prevents duplicate dates
- CASCADE delete removes cache when ticker deleted

## API Contracts

### TickerRepository Interface
```python
class TickerRepository:
    def add_ticker(self, symbol: str) -> int:
        """Insert single ticker, return ticker_id"""
        
    def bulk_add(self, symbols: List[str]) -> Dict[str, List[str]]:
        """
        Insert multiple tickers
        Returns: {'success': [...], 'duplicates': [...], 'errors': [...]}
        """
        
    def get_all(self, page: int, page_size: int, 
                sort_by: str, sort_dir: str) -> Tuple[List[Dict], int]:
        """Get paginated tickers with sorting, return (rows, total_count)"""
        
    def search(self, query: str, page: int, page_size: int) -> Tuple[List[Dict], int]:
        """Search tickers by symbol (case-insensitive)"""
        
    def delete(self, ticker_id: int) -> bool:
        """Soft delete ticker (set is_active=0)"""
        
    def bulk_delete(self, ticker_ids: List[int]) -> int:
        """Soft delete multiple tickers, return count deleted"""
```

### Ticker Validation Rules
```python
def validate_ticker(symbol: str) -> Tuple[bool, Optional[str]]:
    """
    Validate ticker format
    
    Rules:
    - 1-5 characters (most tickers)
    - Alphanumeric only (allow dots for international tickers)
    - Not empty after strip
    
    Returns: (is_valid, error_message)
    """
```

## Component Hierarchy

```
app.py (Streamlit entry)
├── Tab 1: Chart Analysis (placeholder)
├── Tab 2: Alerts (placeholder)
└── Tab 3: Dashboard
    ├── components/ticker_input.py
    │   ├── Text area input form
    │   └── CSV upload form
    └── components/dashboard.py
        ├── Filter controls (search, date range)
        ├── Sort controls
        ├── Ticker table (st.dataframe)
        ├── Pagination controls
        └── Delete controls (individual + bulk)
```

## Risks / Trade-offs

### Risk 1: SQLite Concurrency Limitations
**Risk:** SQLite locks database during writes, potential conflicts with concurrent operations

**Mitigation:**
- Use `with` context managers for automatic connection closing
- Keep transactions short
- Set `timeout` parameter on connections (30 seconds)
- Not a concern for single-user application

### Risk 2: CSV Encoding Issues
**Risk:** User uploads CSV with non-UTF-8 encoding causing parse errors

**Mitigation:**
- Try UTF-8 first, fallback to latin-1
- Show clear error message with encoding hint
- Provide example CSV format in UI

### Risk 3: Database File Corruption
**Risk:** Application crash during write could corrupt SQLite file

**Mitigation:**
- Enable SQLite WAL (Write-Ahead Logging) mode for better crash recovery
- Document backup procedure (copy .db file)
- Consider periodic automatic backups in future

### Risk 4: Performance with Large Datasets
**Risk:** Pagination queries slow with 10,000+ tickers

**Mitigation:**
- Indexes on filter/sort columns
- Use `LIMIT`/`OFFSET` efficiently
- Benchmark with 10,000 records during testing
- Consider full-text search index if needed

## Migration Plan

### Initial Setup (New Installation)
1. Run `app.py` - database auto-initializes on first launch
2. Schema created via `db_manager.init_db()`
3. No data migration needed (greenfield)

### Future Schema Changes (Proposals 2 & 3)
- Proposal 2: No schema changes (price_cache already exists)
- Proposal 3: Add `alerts` table (migration script required)

## Testing Strategy

### Unit Tests
- **Database layer:** Mock sqlite3 connections
  - Test CRUD operations
  - Test constraint violations (duplicate symbols)
  - Test transaction rollback on errors
  
- **Validation:** Pure functions, easy to test
  - Valid tickers: "AAPL", "TSLA", "BRK.B"
  - Invalid tickers: "", "TOOLONG", "123@!"
  
- **CSV parsing:** Test with sample files
  - Valid CSV with header
  - Valid CSV without header
  - Malformed CSV (extra columns, missing data)

### Integration Tests
- End-to-end workflow: Input → Store → Display → Delete
- Pagination: Navigate through multiple pages
- Concurrent operations: Add while displaying (via threading)

### Performance Tests
- Bulk insert 1000 tickers: <5 seconds
- Filter 5000 tickers by symbol: <500ms
- Paginate 10,000 tickers: <1 second per page load

## Open Questions

1. **Ticker Symbol Standards**: Should we validate against known ticker formats (e.g., US only vs international)?
   - **Recommendation**: Be permissive initially, validate against API in Proposal 2

2. **Maximum Ticker Limit**: Should we cap the number of tickers per user?
   - **Recommendation**: No hard limit initially, monitor performance

3. **Export Functionality**: Should dashboard support exporting ticker list to CSV?
   - **Recommendation**: Defer to future enhancement (not in MVP)

4. **Ticker Metadata**: Should we store company names, sectors from API?
   - **Recommendation**: Defer to Proposal 2 when API integration is added

5. **Undo Delete**: Should we add "restore deleted tickers" feature?
   - **Recommendation**: Implement soft delete now, UI for restore in future if needed
