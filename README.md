# Stock Screener - Technical Analysis Dashboard

A Streamlit-based web application for tracking and analyzing stock tickers with technical indicators, trading signals, and alerts.

## Features

### ✅ Ticker Management (Implemented)
- **Multiple input methods**: Manual entry, comma-separated input, CSV upload
- **Bulk operations**: Add, search, filter, and delete tickers in bulk
- **Pagination**: Efficient display of large ticker lists
- **Export**: Download ticker lists as CSV
- **Search & Sort**: Find tickers quickly with search and sorting options

### 🚧 Coming Soon
- **Chart Analysis**: Interactive charts with EMAs (8, 21, 50) and technical indicators
- **Trading Signals**: Long/Short OPEN/CLOSE signals based on indicator combinations
- **Alert System**: Customizable alerts for price movements and signal triggers

## Technical Indicators (Planned)

- MACD (12, 26, 9)
- RSI (14)
- Supertrend (10, 3.0)
- Ichimoku Cloud (9, 26, 52)
- Gann HiLo Activator (13, 21)
- EMAs (8, 21, 50)
- Volume MA (20)

## Installation

### Prerequisites
- Python 3.9 or higher
- pip package manager

### Setup

1. **Clone the repository** (or navigate to the project directory)

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables** (optional):
   ```bash
   export FMP_API_KEY="your_api_key_here"
   export DATABASE_PATH="path/to/database.db"
   ```

   Or create a `.env` file:
   ```
   FMP_API_KEY=your_api_key_here
   DATABASE_PATH=data/screener.db
   ```

## Usage

### Running the Application

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

### Adding Tickers

1. Navigate to the **Dashboard** tab
2. Click **"➕ Add Tickers"** to expand the input section
3. Choose your preferred input method:
   - **Manual Entry**: Add one ticker at a time
   - **Comma-Separated**: Add multiple tickers (e.g., `AAPL, MSFT, GOOGL`)
   - **CSV Upload**: Upload a CSV file with a `symbol` or `ticker` column

### Managing Tickers

- **Search**: Use the search box to filter tickers by symbol
- **Sort**: Sort by symbol, date added, or last updated
- **Delete**: Select tickers using checkboxes and click "Delete Selected"
- **Export**: Download current page or all tickers as CSV

## Project Structure

```
.
├── app.py                  # Main Streamlit application
├── config/                 # Configuration settings
│   ├── __init__.py
│   └── settings.py
├── database/              # Database layer
│   ├── __init__.py
│   ├── db_manager.py      # SQLite connection management
│   ├── models.py          # Schema documentation
│   └── ticker_repository.py  # CRUD operations
├── components/            # UI components
│   ├── __init__.py
│   ├── ticker_input.py    # Ticker input forms
│   └── dashboard.py       # Dashboard display
├── utils/                 # Utility functions
│   ├── __init__.py
│   ├── validators.py      # Input validation
│   └── formatters.py      # Display formatting
├── tests/                 # Test files
│   └── ...
├── data/                  # Database storage (auto-created)
│   └── screener.db
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Configuration

### Database
- **Location**: `data/screener.db` (configurable via `DATABASE_PATH`)
- **Type**: SQLite with WAL mode
- **Auto-initialized**: Database and tables created automatically on first run

### API Key
The application uses Financial Modeling Prep API for stock data. A default API key is included for testing, but it's recommended to get your own free API key at [financialmodelingprep.com](https://financialmodelingprep.com/developer/docs/)

### Settings
All settings can be configured in `config/settings.py`:
- Database path
- Pagination defaults
- API configuration
- Technical indicator parameters

## Development

### Adding Tests

Tests are located in the `tests/` directory. Run tests with pytest:

```bash
pytest tests/
```

### Code Structure

The project follows a modular architecture:
- **Repository Pattern**: Database operations isolated in repository classes
- **Component-based UI**: Reusable Streamlit components
- **Configuration Management**: Centralized settings
- **Utility Functions**: Shared validation and formatting logic

## Database Schema

### Tickers Table
- `id`: Primary key
- `symbol`: Ticker symbol (unique)
- `created_at`: Timestamp when added
- `last_updated`: Timestamp of last update
- `is_active`: Soft delete flag

### Price Cache Table (for future use)
- `id`: Primary key
- `ticker_id`: Foreign key to tickers
- `date`: Price date
- `open`, `high`, `low`, `close`, `volume`: OHLCV data
- `cached_at`: Cache timestamp

## Troubleshooting

### Import Errors
If you see import errors, ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Database Issues
If you encounter database errors, try deleting the database file and restarting:
```bash
rm data/screener.db
streamlit run app.py
```

### Port Already in Use
If port 8501 is busy, specify a different port:
```bash
streamlit run app.py --server.port 8502
```

## Contributing

This project follows the OpenSpec specification system. See `openspec/` directory for:
- Project specifications
- Change proposals
- Implementation tasks

## License

[Add your license here]

## Support

For issues, questions, or contributions, please [create an issue](your-repo-url/issues).

## Roadmap

- [x] Ticker management infrastructure
- [ ] Chart analysis with technical indicators
- [ ] Trading signal generation
- [ ] Alert system
- [ ] Email notifications
- [ ] Portfolio tracking
- [ ] Backtesting capabilities
