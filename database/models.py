"""Data models for database tables."""

# Table schemas are defined in db_manager.py
# This file can be extended in the future for ORM models if needed

# Tickers table schema:
# - id: INTEGER PRIMARY KEY AUTOINCREMENT
# - symbol: TEXT UNIQUE NOT NULL
# - added_date: DATETIME DEFAULT CURRENT_TIMESTAMP
# - last_updated: DATETIME
# - is_active: BOOLEAN DEFAULT 1

# Price cache table schema:
# - id: INTEGER PRIMARY KEY AUTOINCREMENT
# - ticker_id: INTEGER NOT NULL
# - date: DATE NOT NULL
# - open: REAL
# - high: REAL
# - low: REAL
# - close: REAL
# - volume: INTEGER
# - cached_at: DATETIME DEFAULT CURRENT_TIMESTAMP
# - FOREIGN KEY (ticker_id) REFERENCES tickers(id) ON DELETE CASCADE
# - UNIQUE(ticker_id, date)

# Alerts table schema:
# - id: INTEGER PRIMARY KEY AUTOINCREMENT
# - ticker_id: INTEGER NOT NULL
# - ticker_symbol: TEXT NOT NULL
# - alert_type: TEXT NOT NULL CHECK(alert_type IN ('LONG_OPEN', 'LONG_CLOSE', 'SHORT_OPEN', 'SHORT_CLOSE'))
# - signal_date: DATE NOT NULL
# - price: REAL NOT NULL
# - created_at: DATETIME DEFAULT CURRENT_TIMESTAMP
# - FOREIGN KEY (ticker_id) REFERENCES tickers(id) ON DELETE CASCADE
