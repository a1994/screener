# Quick Start Guide - Stock Screener

## Installation

1. **Navigate to project directory**:
   ```bash
   cd "/Users/ruchidabeer/Documents/Aniruddha/TRADING & INVESTING/PROJECTS/SCREENER"
   ```

2. **Install dependencies** (already done):
   ```bash
   .venv/bin/pip install -r requirements.txt
   ```

3. **Run tests** (all 49 passing ✅):
   ```bash
   .venv/bin/python -m pytest tests/ -v
   ```

4. **Start the application**:
   ```bash
   .venv/bin/streamlit run app.py
   ```

## Features Implemented

### ✅ Ticker Management (Proposal 1 - COMPLETE)

#### Adding Tickers
1. Go to **Dashboard** tab
2. Expand **"➕ Add Tickers"** section
3. Choose method:
   - **Manual Entry**: Single ticker input
   - **Comma-Separated**: Multiple tickers (e.g., AAPL, MSFT, GOOGL)
   - **CSV Upload**: Upload CSV with 'symbol' or 'ticker' column

#### Managing Tickers
- **Search**: Filter by ticker symbol
- **Sort**: By symbol or date (added/updated)
- **Pagination**: 25, 50, 100, or 200 items per page
- **Delete**: Select tickers and bulk delete
- **Export**: Download as CSV (current page or all)

## Project Structure

```
SCREENER/
├── app.py                    # Main Streamlit application
├── config/                   # Configuration settings
│   ├── settings.py          # Database, API, app settings
├── database/                 # Database layer
│   ├── db_manager.py        # Connection management
│   ├── models.py            # Schema documentation
│   └── ticker_repository.py # CRUD operations
├── components/               # UI components
│   ├── ticker_input.py      # Ticker input forms
│   └── dashboard.py         # Dashboard display
├── utils/                    # Utility functions
│   ├── validators.py        # Input validation
│   └── formatters.py        # Display formatting
├── tests/                    # Test suite (49 tests)
│   ├── test_database.py
│   ├── test_validators.py
│   └── test_formatters.py
├── data/                     # Database storage (auto-created)
│   └── screener.db          # SQLite database
├── requirements.txt          # Python dependencies
└── README.md                # Full documentation
```

## Testing

Run all tests:
```bash
.venv/bin/python -m pytest tests/ -v
```

Run specific test file:
```bash
.venv/bin/python -m pytest tests/test_database.py -v
```

Run with coverage:
```bash
.venv/bin/python -m pytest tests/ --cov=. --cov-report=html
```

## Database

- **Type**: SQLite 3.x with WAL mode
- **Location**: `data/screener.db`
- **Auto-initialized**: Created on first run
- **Tables**: 
  - `tickers`: Ticker symbols and metadata
  - `price_cache`: Historical price data (for future use)

### Reset Database

```bash
rm data/screener.db
.venv/bin/streamlit run app.py
```

## API Configuration

Default API key is included for testing. To use your own:

1. Get free API key from [financialmodelingprep.com](https://financialmodelingprep.com/developer/docs/)

2. Set environment variable:
   ```bash
   export FMP_API_KEY="your_key_here"
   ```

3. Or update `config/settings.py`

## Common Issues

### Port Already in Use
```bash
.venv/bin/streamlit run app.py --server.port 8502
```

### Import Errors
```bash
.venv/bin/pip install -r requirements.txt
```

### Database Locked
- Close other connections to the database
- SQLite WAL mode helps with concurrency

## Next Features (Coming Soon)

### 🚧 Chart Analysis (Proposal 2)
- Interactive price charts with EMAs
- Technical indicators (MACD, RSI, Supertrend, etc.)
- Trading signals (Long/Short OPEN/CLOSE)
- Volume analysis

### 🚧 Alert System (Proposal 3)
- Configurable price alerts
- Signal-based alerts
- Alert history
- Notification system

## Development

### Adding a New Feature

1. Create OpenSpec proposal in `openspec/changes/`
2. Implement following proposal structure
3. Write tests first (TDD)
4. Update documentation

### Code Style

- Use type hints
- Write docstrings for public functions
- Follow PEP 8
- Run linter before committing

## Support

For issues or questions:
1. Check README.md
2. Review test files for usage examples
3. Check OpenSpec documentation in `openspec/`

## Success Metrics

✅ **49/49 tests passing**  
✅ **All modules fully functional**  
✅ **No known bugs**  
✅ **Documentation complete**  
✅ **Ready for Proposal 2 & 3 implementation**
