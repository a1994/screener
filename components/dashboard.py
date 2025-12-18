"""Dashboard component for displaying and managing tickers."""

import streamlit as st
import pandas as pd
from typing import List, Dict, Any

from database import TickerRepository
from utils import format_datetime, format_count
from config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


def render_dashboard(repo: TickerRepository, user_id: int = 1) -> None:
    """
    Render ticker management dashboard with table, pagination, and filters for a specific user.
    
    Args:
        repo: TickerRepository instance for database operations
        user_id: User ID to filter tickers by
    """
    st.subheader("Ticker Management Dashboard")
    
    # Initialize session state for pagination and filters
    if 'page' not in st.session_state:
        st.session_state.page = 1
    if 'page_size' not in st.session_state:
        st.session_state.page_size = DEFAULT_PAGE_SIZE
    if 'sort_by' not in st.session_state:
        st.session_state.sort_by = 'symbol'
    if 'sort_dir' not in st.session_state:
        st.session_state.sort_dir = 'ASC'
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ''
    
    # Filters row
    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
    
    with col1:
        search_query = st.text_input(
            "Search tickers",
            value=st.session_state.search_query,
            placeholder="Search by symbol...",
            key="search_input"
        )
        if search_query != st.session_state.search_query:
            st.session_state.search_query = search_query
            st.session_state.page = 1  # Reset to first page on search
    
    with col2:
        sort_options = {
            'Symbol (A-Z)': ('symbol', 'ASC'),
            'Symbol (Z-A)': ('symbol', 'DESC'),
            'Added (Newest)': ('created_at', 'DESC'),
            'Added (Oldest)': ('created_at', 'ASC'),
            'Updated (Newest)': ('last_updated', 'DESC'),
            'Updated (Oldest)': ('last_updated', 'ASC'),
        }
        
        # Find current selection
        current_sort = f"{st.session_state.sort_by} ({st.session_state.sort_dir})"
        current_label = None
        for label, (col, dir) in sort_options.items():
            if col == st.session_state.sort_by and dir == st.session_state.sort_dir:
                current_label = label
                break
        
        sort_selection = st.selectbox(
            "Sort by",
            options=list(sort_options.keys()),
            index=list(sort_options.keys()).index(current_label) if current_label else 0,
            key="sort_select"
        )
        
        st.session_state.sort_by, st.session_state.sort_dir = sort_options[sort_selection]
    
    with col3:
        page_size = st.selectbox(
            "Per page",
            options=[25, 50, 100, 200],
            index=[25, 50, 100, 200].index(st.session_state.page_size) if st.session_state.page_size in [25, 50, 100, 200] else 1,
            key="page_size_select"
        )
        if page_size != st.session_state.page_size:
            st.session_state.page_size = page_size
            st.session_state.page = 1  # Reset to first page
    
    with col4:
        if st.button("🔄 Refresh", key="refresh_btn"):
            st.rerun()
    
    # Fetch data
    try:
        tickers, total_count = repo.get_all(
            page=st.session_state.page,
            page_size=st.session_state.page_size,
            sort_by=st.session_state.sort_by,
            sort_dir=st.session_state.sort_dir,
            search_query=st.session_state.search_query if st.session_state.search_query else None,
            user_id=user_id
        )
        
        # Display count
        if st.session_state.search_query:
            st.write(f"Found {format_count(total_count)} ticker(s) matching '{st.session_state.search_query}'")
        else:
            st.write(f"Total tickers: {format_count(total_count)}")
        
        if not tickers:
            st.info("No tickers found. Add some tickers to get started!")
            return
        
        # Convert to DataFrame for display
        df = pd.DataFrame(tickers)
        
        # Format dates
        if 'created_at' in df.columns:
            df['created_at'] = df['created_at'].apply(lambda x: format_datetime(x, 'N/A'))
        if 'last_updated' in df.columns:
            df['last_updated'] = df['last_updated'].apply(lambda x: format_datetime(x, 'N/A'))
        
        # Add selection column
        df.insert(0, 'Select', False)
        
        # Display table with checkboxes
        st.write("### Ticker List")
        
        # Use data editor for selection
        edited_df = st.data_editor(
            df,
            hide_index=True,
            width='stretch',
            disabled=['id', 'symbol', 'created_at', 'last_updated', 'is_active'],
            key=f"ticker_table_{st.session_state.page}"
        )
        
        # Pagination controls
        total_pages = (total_count + st.session_state.page_size - 1) // st.session_state.page_size
        
        if total_pages > 1:
            col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
            
            with col1:
                if st.button("⏮️ First", disabled=st.session_state.page == 1):
                    st.session_state.page = 1
                    st.rerun()
            
            with col2:
                if st.button("◀️ Prev", disabled=st.session_state.page == 1):
                    st.session_state.page -= 1
                    st.rerun()
            
            with col3:
                st.write(f"Page {st.session_state.page} of {total_pages}")
            
            with col4:
                if st.button("Next ▶️", disabled=st.session_state.page >= total_pages):
                    st.session_state.page += 1
                    st.rerun()
            
            with col5:
                if st.button("Last ⏭️", disabled=st.session_state.page >= total_pages):
                    st.session_state.page = total_pages
                    st.rerun()
        
        # Bulk actions
        selected_tickers = edited_df[edited_df['Select']]['id'].tolist()
        
        if selected_tickers:
            st.write(f"**{len(selected_tickers)} ticker(s) selected**")
            
            col1, col2 = st.columns([1, 5])
            
            with col1:
                if st.button("🗑️ Delete Selected", type="primary"):
                    try:
                        deleted_count = repo.bulk_delete(selected_tickers)
                        if deleted_count > 0:
                            st.success(f"✅ Deleted {deleted_count} ticker(s)")
                            st.rerun()
                        else:
                            st.error("Failed to delete tickers")
                    except Exception as e:
                        st.error(f"Error deleting tickers: {str(e)}")
        
        # Export functionality
        st.write("### Export")
        
        col1, col2 = st.columns([1, 5])
        
        with col1:
            # Create CSV export
            export_symbols = [t['symbol'] for t in tickers]
            csv_data = pd.DataFrame({'symbol': export_symbols})
            
            st.download_button(
                label="📥 Export Current Page",
                data=csv_data.to_csv(index=False),
                file_name="tickers_export.csv",
                mime="text/csv",
                help="Export tickers on current page to CSV"
            )
        
        with col2:
            if st.button("📥 Export All Tickers"):
                try:
                    all_tickers = repo.get_active_tickers()
                    if all_tickers:
                        csv_data = pd.DataFrame({'symbol': all_tickers})
                        st.download_button(
                            label="Download All Tickers CSV",
                            data=csv_data.to_csv(index=False),
                            file_name="all_tickers_export.csv",
                            mime="text/csv",
                        )
                    else:
                        st.info("No tickers to export")
                except Exception as e:
                    st.error(f"Error exporting tickers: {str(e)}")
    
    except Exception as e:
        st.error(f"Error loading tickers: {str(e)}")


def render_ticker_stats(repo: TickerRepository, user_id: int = 1) -> None:
    """
    Render ticker statistics in sidebar or separate section for a specific user.
    
    Args:
        repo: TickerRepository instance
        user_id: User ID to filter tickers by
    """
    try:
        tickers, total_count = repo.get_all(page=1, page_size=1, user_id=user_id)
        
        st.metric("Total Active Tickers", format_count(total_count))
        
    except Exception as e:
        st.error(f"Error loading stats: {str(e)}")
