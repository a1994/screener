"""Ticker input component for the stock screener."""

import streamlit as st
import pandas as pd
from typing import List, Tuple, Optional
from io import StringIO

from database import TickerRepository, get_db_connection
from utils import parse_tickers, validate_ticker, normalize_ticker, check_duplicates
from config import MAX_BULK_INSERT_SIZE


def render_ticker_input(repo: TickerRepository) -> None:
    """
    Render ticker input UI with multiple input methods.
    
    Args:
        repo: TickerRepository instance for database operations
    """
    st.subheader("Add Tickers")
    
    # Create tabs for different input methods
    tab1, tab2, tab3 = st.tabs(["Manual Entry", "Comma-Separated", "CSV Upload"])
    
    with tab1:
        _render_manual_entry(repo)
    
    with tab2:
        _render_comma_separated(repo)
    
    with tab3:
        _render_csv_upload(repo)


def _render_manual_entry(repo: TickerRepository) -> None:
    """
    Render manual single ticker entry.
    
    Args:
        repo: TickerRepository instance
    """
    with st.form("manual_ticker_form"):
        ticker_input = st.text_input(
            "Ticker Symbol",
            placeholder="Enter ticker symbol (e.g., AAPL)",
            help="Enter a single ticker symbol (1-5 characters, alphanumeric or dots)"
        )
        
        submitted = st.form_submit_button("Add Ticker")
        
        if submitted and ticker_input:
            ticker = normalize_ticker(ticker_input)
            is_valid, error_msg = validate_ticker(ticker)
            
            if not is_valid:
                st.error(f"Invalid ticker: {error_msg}")
                return
            
            # Check if ticker already exists
            existing = repo.get_by_symbol(ticker)
            if existing:
                st.warning(f"Ticker {ticker} already exists in the database")
                return
            
            # Add ticker
            try:
                ticker_id = repo.add_ticker(ticker)
                if ticker_id:
                    st.success(f"✅ Added ticker: {ticker}")
                    # Trigger refresh of ticker dropdowns in other tabs
                    st.session_state.ticker_list_updated = True
                else:
                    st.error(f"Failed to add ticker: {ticker}")
            except Exception as e:
                st.error(f"Error adding ticker: {str(e)}")


def _render_comma_separated(repo: TickerRepository) -> None:
    """
    Render comma-separated bulk ticker entry.
    
    Args:
        repo: TickerRepository instance
    """
    with st.form("bulk_ticker_form"):
        ticker_input = st.text_area(
            "Ticker Symbols (comma-separated)",
            placeholder="Enter ticker symbols separated by commas (e.g., AAPL, MSFT, GOOGL)",
            help="Enter multiple ticker symbols separated by commas",
            height=100
        )
        
        submitted = st.form_submit_button("Add Tickers")
        
        if submitted and ticker_input:
            # Parse tickers
            tickers = parse_tickers(ticker_input)
            
            if not tickers:
                st.warning("No valid tickers found in input")
                return
            
            if len(tickers) > MAX_BULK_INSERT_SIZE:
                st.error(f"Too many tickers. Maximum allowed: {MAX_BULK_INSERT_SIZE}")
                return
            
            # Validate all tickers
            invalid_tickers = []
            valid_tickers = []
            
            for ticker in tickers:
                is_valid, error_msg = validate_ticker(ticker)
                if is_valid:
                    valid_tickers.append(ticker)
                else:
                    invalid_tickers.append((ticker, error_msg))
            
            if invalid_tickers:
                st.warning(f"Found {len(invalid_tickers)} invalid ticker(s):")
                for ticker, error_msg in invalid_tickers[:5]:  # Show first 5
                    st.text(f"  • {ticker}: {error_msg}")
                if len(invalid_tickers) > 5:
                    st.text(f"  ... and {len(invalid_tickers) - 5} more")
            
            if not valid_tickers:
                st.error("No valid tickers to add")
                return
            
            # Check for duplicates
            existing_symbols = [t['symbol'] for t in repo.get_all()[0]]
            new_tickers, existing_tickers = check_duplicates(valid_tickers, existing_symbols)
            
            if existing_tickers:
                st.info(f"Skipping {len(existing_tickers)} ticker(s) already in database: {', '.join(existing_tickers[:5])}")
            
            if not new_tickers:
                st.warning("All tickers already exist in database")
                return
            
            # Bulk add
            try:
                result = repo.bulk_add(new_tickers)
                
                if result['added'] > 0:
                    st.success(f"✅ Added {result['added']} ticker(s)")
                    # Trigger refresh of ticker dropdowns in other tabs
                    st.session_state.ticker_list_updated = True
                
                if result['failed'] > 0:
                    st.warning(f"Failed to add {result['failed']} ticker(s)")
                    if result['errors']:
                        with st.expander("View errors"):
                            for error in result['errors'][:10]:  # Show first 10
                                st.text(f"  • {error}")
                
            except Exception as e:
                st.error(f"Error adding tickers: {str(e)}")


def _render_csv_upload(repo: TickerRepository) -> None:
    """
    Render CSV file upload for bulk ticker entry.
    
    Args:
        repo: TickerRepository instance
    """
    st.write("Upload a CSV file with ticker symbols. The file should have a column named 'symbol' or 'ticker'.")
    
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=['csv'],
        help="Upload a CSV file with a 'symbol' or 'ticker' column"
    )
    
    if uploaded_file is not None:
        try:
            # Read CSV
            df = pd.read_csv(uploaded_file)
            
            # Find ticker column
            ticker_col = None
            for col in ['symbol', 'ticker', 'Symbol', 'Ticker', 'SYMBOL', 'TICKER']:
                if col in df.columns:
                    ticker_col = col
                    break
            
            if ticker_col is None:
                st.error("CSV file must contain a 'symbol' or 'ticker' column")
                return
            
            # Extract and normalize tickers
            tickers = df[ticker_col].dropna().astype(str).tolist()
            tickers = [normalize_ticker(t) for t in tickers]
            tickers = list(dict.fromkeys(tickers))  # Remove duplicates
            
            if not tickers:
                st.warning("No valid tickers found in CSV file")
                return
            
            if len(tickers) > MAX_BULK_INSERT_SIZE:
                st.error(f"Too many tickers in CSV. Maximum allowed: {MAX_BULK_INSERT_SIZE}")
                return
            
            st.write(f"Found {len(tickers)} unique ticker(s) in CSV file")
            
            # Preview
            with st.expander("Preview tickers"):
                st.write(tickers[:20])
                if len(tickers) > 20:
                    st.text(f"... and {len(tickers) - 20} more")
            
            if st.button("Add Tickers from CSV"):
                # Validate all tickers
                invalid_tickers = []
                valid_tickers = []
                
                for ticker in tickers:
                    is_valid, error_msg = validate_ticker(ticker)
                    if is_valid:
                        valid_tickers.append(ticker)
                    else:
                        invalid_tickers.append((ticker, error_msg))
                
                if invalid_tickers:
                    st.warning(f"Found {len(invalid_tickers)} invalid ticker(s):")
                    with st.expander("View invalid tickers"):
                        for ticker, error_msg in invalid_tickers[:20]:
                            st.text(f"  • {ticker}: {error_msg}")
                
                if not valid_tickers:
                    st.error("No valid tickers to add")
                    return
                
                # Check for duplicates
                existing_symbols = [t['symbol'] for t in repo.get_all()[0]]
                new_tickers, existing_tickers = check_duplicates(valid_tickers, existing_symbols)
                
                if existing_tickers:
                    st.info(f"Skipping {len(existing_tickers)} ticker(s) already in database")
                
                if not new_tickers:
                    st.warning("All tickers already exist in database")
                    return
                
                # Bulk add
                try:
                    result = repo.bulk_add(new_tickers)
                    
                    if result['added'] > 0:
                        st.success(f"✅ Added {result['added']} ticker(s)")
                        # Trigger refresh of ticker dropdowns in other tabs
                        st.session_state.ticker_list_updated = True
                    
                    if result['failed'] > 0:
                        st.warning(f"Failed to add {result['failed']} ticker(s)")
                        if result['errors']:
                            with st.expander("View errors"):
                                for error in result['errors'][:20]:
                                    st.text(f"  • {error}")
                    
                except Exception as e:
                    st.error(f"Error adding tickers: {str(e)}")
        
        except Exception as e:
            st.error(f"Error reading CSV file: {str(e)}")
