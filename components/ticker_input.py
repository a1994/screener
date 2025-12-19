"""Ticker input component for the stock screener."""

import streamlit as st
import pandas as pd
from typing import List, Tuple, Optional
from io import StringIO

from database import TickerRepository, ThemeRepository, get_db_connection
from utils import parse_tickers, validate_ticker, normalize_ticker, check_duplicates
from utils.mobile_responsive import mobile_friendly_columns, mobile_friendly_form
from config import MAX_BULK_INSERT_SIZE


def render_ticker_input(repo: TickerRepository, user_id: int = 1) -> None:
    """
    Render ticker input UI with multiple input methods and theme selection.
    
    Args:
        repo: TickerRepository instance for database operations
        user_id: User ID for whom to add tickers
    """
    st.subheader("Add Tickers")
    
    # Initialize theme repository
    theme_repo = ThemeRepository()
    
    # Theme selection (required for all input methods)
    selected_theme_id = _render_theme_selector(theme_repo, user_id)
    
    if selected_theme_id is None:
        st.warning("⚠️ Please select or create a theme before adding tickers in Theme Management section below.")
        return
    
    # Create tabs for different input methods
    tab1, tab2, tab3 = st.tabs(["Manual Entry", "Comma-Separated", "CSV Upload"])
    
    with tab1:
        _render_manual_entry(repo, theme_repo, user_id, selected_theme_id)
    
    with tab2:
        _render_comma_separated(repo, theme_repo, user_id, selected_theme_id)
    
    with tab3:
        _render_csv_upload(repo, theme_repo, user_id, selected_theme_id)


def _render_theme_selector(theme_repo: ThemeRepository, user_id: int) -> Optional[int]:
    """
    Render theme selector with create new option.
    
    Args:
        theme_repo: ThemeRepository instance
        user_id: User ID
        
    Returns:
        Selected theme ID or None if no theme selected
    """
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Get user themes
        user_themes = theme_repo.get_user_themes(user_id)
        
        # Create options for dropdown
        theme_options = {"None": None}  # Default empty option
        theme_options.update({theme['name']: theme['id'] for theme in user_themes})
        theme_options["➕ Create New Theme"] = "CREATE_NEW"
        
        selected_option = st.selectbox(
            "Select Theme *",
            options=list(theme_options.keys()),
            index=0,
            help="Select an existing theme or create a new one. Required to add tickers.",
            key="theme_selector"
        )
        
        selected_theme_id = theme_options[selected_option]
    
    with col2:
        if selected_theme_id == "CREATE_NEW":
            if st.button("Create", key="ticker_input_create_theme_btn"):
                st.session_state.show_create_theme = True
    
    # Handle new theme creation
    if selected_theme_id == "CREATE_NEW" and st.session_state.get('show_create_theme', False):
        with st.expander("Create New Theme", expanded=True):
            with st.form("create_theme_form"):
                new_theme_name = st.text_input(
                    "Theme Name *",
                    placeholder="e.g., Tech Stocks, Blue Chip, Growth Stocks"
                )
                new_theme_description = st.text_area(
                    "Description (optional)",
                    placeholder="Brief description of this theme",
                    height=60
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    create_submitted = st.form_submit_button("✅ Create Theme", key="theme_create_submit")
                with col2:
                    create_cancelled = st.form_submit_button("❌ Cancel", key="theme_create_cancel")
                
                if create_submitted and new_theme_name.strip():
                    theme_id = theme_repo.create_theme(
                        user_id=user_id,
                        name=new_theme_name.strip(),
                        description=new_theme_description.strip() if new_theme_description.strip() else None
                    )
                    
                    if theme_id:
                        st.success(f"✅ Created theme: {new_theme_name}")
                        st.session_state.show_create_theme = False
                        st.session_state.selected_theme_id = theme_id
                        st.rerun()
                    else:
                        st.error("❌ Theme name already exists or creation failed")
                
                if create_cancelled:
                    st.session_state.show_create_theme = False
                    st.rerun()
        
        return None  # No theme selected while creating
    
    # Return the selected theme ID from session state if available, otherwise from dropdown
    if 'selected_theme_id' in st.session_state:
        return st.session_state.selected_theme_id
    
    return selected_theme_id if selected_theme_id != "CREATE_NEW" else None


def _render_manual_entry(repo: TickerRepository, theme_repo: ThemeRepository, user_id: int, theme_id: int) -> None:
    """
    Render manual single ticker entry with theme.
    
    Args:
        repo: TickerRepository instance
        theme_repo: ThemeRepository instance
        user_id: User ID for whom to add ticker
        theme_id: Theme ID to add ticker to
    """
    with st.form("manual_ticker_form"):
        ticker_input = st.text_input(
            "Ticker Symbol",
            placeholder="Enter ticker symbol (e.g., AAPL)",
            help="Enter a single ticker symbol (1-5 characters, alphanumeric or dots)"
        )
        
        submitted = st.form_submit_button("Add Ticker", key="manual_ticker_submit")
        
        if submitted and ticker_input:
            ticker = normalize_ticker(ticker_input)
            is_valid, error_msg = validate_ticker(ticker)
            
            if not is_valid:
                st.error(f"Invalid ticker: {error_msg}")
                return
            
            # Check if ticker already exists for this user
            existing = repo.get_by_symbol(ticker, user_id)
            ticker_id = None
            
            if existing:
                # Ticker exists, check if it's already in this theme
                ticker_id = existing['id']
                if theme_repo.is_ticker_in_theme(ticker_id, theme_id):
                    st.warning(f"Ticker {ticker} is already in this theme")
                    return
                else:
                    # Ticker exists but not in this theme, add it to theme
                    # Debug info
                    user_themes = theme_repo.get_user_themes(user_id)
                    theme_name = next((t['name'] for t in user_themes if t['id'] == theme_id), f'Theme {theme_id}')
                    
                    if theme_repo.add_ticker_to_theme(ticker_id, theme_id):
                        st.success(f"✅ Added existing ticker {ticker} to theme '{theme_name}'")
                        # Clear session state for theme selection
                        if 'selected_theme_id' in st.session_state:
                            del st.session_state.selected_theme_id
                        st.rerun()
                    else:
                        st.error(f"Failed to add ticker {ticker} (ID: {ticker_id}) to theme '{theme_name}' (ID: {theme_id})")
                        # Additional debug info
                        st.error("Please try refreshing the page or selecting the theme again.")
                    return
            
            # Ticker doesn't exist, create it and add to theme
            try:
                ticker_id = repo.add_ticker(ticker, user_id)
                if ticker_id:
                    # Add ticker to theme
                    # Debug info
                    user_themes = theme_repo.get_user_themes(user_id)
                    theme_name = next((t['name'] for t in user_themes if t['id'] == theme_id), f'Theme {theme_id}')
                    
                    if theme_repo.add_ticker_to_theme(ticker_id, theme_id):
                        st.success(f"✅ Added new ticker: {ticker} to theme '{theme_name}'")
                        # Clear session state for theme selection
                        if 'selected_theme_id' in st.session_state:
                            del st.session_state.selected_theme_id
                        # Trigger page rerun to refresh ticker dropdowns across all tabs
                        st.rerun()
                    else:
                        st.error(f"Failed to add ticker {ticker} (ID: {ticker_id}) to theme '{theme_name}' (ID: {theme_id})")
                        st.error("Please try refreshing the page or selecting the theme again.")
                else:
                    st.error(f"Failed to add ticker: {ticker}")
            except Exception as e:
                st.error(f"Error adding ticker: {str(e)}")


def _render_comma_separated(repo: TickerRepository, theme_repo: ThemeRepository, user_id: int, theme_id: int) -> None:
    """
    Render comma-separated bulk ticker entry with theme.
    
    Args:
        repo: TickerRepository instance
        theme_repo: ThemeRepository instance
        user_id: User ID for whom to add tickers
        theme_id: Theme ID to add tickers to
    """
    with st.form("bulk_ticker_form"):
        ticker_input = st.text_area(
            "Ticker Symbols (comma-separated)",
            placeholder="Enter ticker symbols separated by commas (e.g., AAPL, MSFT, GOOGL)",
            help="Enter multiple ticker symbols separated by commas",
            height=100
        )
        
        submitted = st.form_submit_button("Add Tickers", key="bulk_ticker_submit")
        
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
            
            # Check for duplicates for this user
            existing_symbols = [t['symbol'] for t in repo.get_all(user_id)[0]]
            new_tickers, existing_tickers = check_duplicates(valid_tickers, existing_symbols)
            
            if existing_tickers:
                st.info(f"Skipping {len(existing_tickers)} ticker(s) already in database: {', '.join(existing_tickers[:5])}")
            
            if not new_tickers:
                st.warning("All tickers already exist in database")
                return
            
            # Bulk add for this user
            try:
                result = repo.bulk_add(new_tickers, user_id)
                
                if result['added'] > 0:
                    # Add successfully added tickers to theme
                    added_to_theme = _add_tickers_to_theme(repo, theme_repo, new_tickers, user_id, theme_id)
                    st.success(f"✅ Added {result['added']} ticker(s) to theme ({added_to_theme} linked to theme)")
                
                if result['failed'] > 0:
                    st.warning(f"Failed to add {result['failed']} ticker(s)")
                    if result['errors']:
                        with st.expander("View errors"):
                            for error in result['errors'][:10]:  # Show first 10
                                st.text(f"  • {error}")
                
                # Clear session state for theme selection and trigger page rerun
                if result['added'] > 0:
                    if 'selected_theme_id' in st.session_state:
                        del st.session_state.selected_theme_id
                    st.rerun()
                
            except Exception as e:
                st.error(f"Error adding tickers: {str(e)}")


def _add_tickers_to_theme(repo: TickerRepository, theme_repo: ThemeRepository, ticker_symbols: List[str], user_id: int, theme_id: int) -> int:
    """
    Helper function to add multiple tickers to a theme.
    
    Args:
        repo: TickerRepository instance
        theme_repo: ThemeRepository instance
        ticker_symbols: List of ticker symbols to add to theme
        user_id: User ID
        theme_id: Theme ID
        
    Returns:
        Number of tickers successfully added to theme
    """
    added_to_theme = 0
    
    for symbol in ticker_symbols:
        # Get ticker by symbol (normalize first to match what bulk_add creates)
        normalized_symbol = normalize_ticker(symbol)
        ticker = repo.get_by_symbol(normalized_symbol, user_id)
        if ticker:
            # Check if ticker is already in this theme
            if not theme_repo.is_ticker_in_theme(ticker['id'], theme_id):
                if theme_repo.add_ticker_to_theme(ticker['id'], theme_id):
                    added_to_theme += 1
    
    return added_to_theme


def _render_csv_upload(repo: TickerRepository, theme_repo: ThemeRepository, user_id: int, theme_id: int) -> None:
    """
    Render CSV file upload for bulk ticker entry with theme.
    
    Args:
        repo: TickerRepository instance
        theme_repo: ThemeRepository instance
        user_id: User ID for whom to add tickers
        theme_id: Theme ID to add tickers to
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
            
            if st.button("Add Tickers from CSV", key="ticker_csv_add_btn"):
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
                
                # Check for duplicates for this user
                existing_symbols = [t['symbol'] for t in repo.get_all(user_id)[0]]
                new_tickers, existing_tickers = check_duplicates(valid_tickers, existing_symbols)
                
                if existing_tickers:
                    st.info(f"Skipping {len(existing_tickers)} ticker(s) already in database")
                
                if not new_tickers:
                    st.warning("All tickers already exist in database")
                    return
                
                # Bulk add for this user
                try:
                    result = repo.bulk_add(new_tickers, user_id)
                    
                    if result['added'] > 0:
                        # Add successfully added tickers to theme
                        added_to_theme = _add_tickers_to_theme(repo, theme_repo, new_tickers, user_id, theme_id)
                        st.success(f"✅ Added {result['added']} ticker(s) from CSV to theme ({added_to_theme} linked to theme)")
                    
                    if result['failed'] > 0:
                        st.warning(f"Failed to add {result['failed']} ticker(s)")
                        if result['errors']:
                            with st.expander("View errors"):
                                for error in result['errors'][:10]:
                                    st.text(f"  • {error}")
                    
                    # Clear session state for theme selection and trigger page rerun
                    if result['added'] > 0:
                        if 'selected_theme_id' in st.session_state:
                            del st.session_state.selected_theme_id
                        st.rerun()
                    
                except Exception as e:
                    st.error(f"Error adding tickers: {str(e)}")
        
        except Exception as e:
            st.error(f"Error reading CSV file: {str(e)}")
