"""Dashboard component for displaying and managing tickers."""

import streamlit as st
import pandas as pd
from typing import List, Dict, Any

from database import TickerRepository, ThemeRepository
from utils import format_datetime, format_count
from utils.mobile_responsive import mobile_friendly_columns, mobile_metric_card, mobile_data_table
from config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from components import render_ticker_input


def render_dashboard(repo: TickerRepository, user_id: int = 1) -> None:
    """
    Render ticker management dashboard with table, pagination, and filters for a specific user.
    
    Args:
        repo: TickerRepository instance for database operations
        user_id: User ID to filter tickers by
    """
    st.subheader("Ticker Management Dashboard")
    
    # Add ticker section (collapsible)
    with st.expander("➕ Add Tickers", expanded=False):
        render_ticker_input(repo, user_id=user_id)
    
    st.markdown("---")
    
    # Initialize theme repository
    theme_repo = ThemeRepository()
    
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
    if 'selected_theme_filter' not in st.session_state:
        st.session_state.selected_theme_filter = None
    
    # Filters row - mobile responsive
    col1, col2, col3, col4, col5 = mobile_friendly_columns(5)
    
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
        # Theme filter
        user_themes = theme_repo.get_user_themes(user_id)
        theme_options = {"All Themes": None}
        theme_options.update({theme['name']: theme['id'] for theme in user_themes})
        
        # Find current selection
        current_theme_label = "All Themes"
        for label, theme_id in theme_options.items():
            if theme_id == st.session_state.selected_theme_filter:
                current_theme_label = label
                break
        
        theme_selection = st.selectbox(
            "Filter by Theme",
            options=list(theme_options.keys()),
            index=list(theme_options.keys()).index(current_theme_label),
            key="theme_filter_select"
        )
        
        new_theme_filter = theme_options[theme_selection]
        if new_theme_filter != st.session_state.selected_theme_filter:
            st.session_state.selected_theme_filter = new_theme_filter
            st.session_state.page = 1  # Reset to first page on filter change
    
    with col3:
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
    
    with col4:
        page_size = st.selectbox(
            "Per page",
            options=[25, 50, 100, 200],
            index=[25, 50, 100, 200].index(st.session_state.page_size) if st.session_state.page_size in [25, 50, 100, 200] else 1,
            key="page_size_select"
        )
        if page_size != st.session_state.page_size:
            st.session_state.page_size = page_size
            st.session_state.page = 1  # Reset to first page
    
    with col5:
        if st.button("🔄 Refresh", key="refresh_btn"):
            st.rerun()
    
    # Theme Management Section
    st.write("### Theme Management")
    
    # Add new theme section
    with st.expander("➕ Create New Theme", expanded=False):
        col1, col2 = st.columns([3, 2])
        
        with col1:
            new_theme_name = st.text_input(
                "Theme Name",
                placeholder="Enter theme name...",
                key="new_theme_name_input"
            )
            new_theme_description = st.text_input(
                "Description (Optional)",
                placeholder="Enter theme description...",
                key="new_theme_desc_input"
            )
        
        with col2:
            st.write("")  # Spacer
            if st.button("✅ Create Theme", type="primary", key="dashboard_create_theme_btn"):
                if new_theme_name and new_theme_name.strip():
                    theme_id = theme_repo.create_theme(
                        user_id, 
                        new_theme_name.strip(), 
                        new_theme_description.strip() if new_theme_description else None
                    )
                    if theme_id:
                        st.success(f"✅ Created theme '{new_theme_name}'")
                        st.rerun()
                    else:
                        st.error("❌ Failed to create theme (name may already exist)")
                else:
                    st.error("❌ Please enter a theme name")
    
    # Manage existing themes section
    if user_themes:
        col1, col2, col3 = st.columns([3, 2, 3])
        
        with col1:
            # Theme selection for management
            theme_to_manage = st.selectbox(
                "Select theme to delete",
                options=[{"name": "Select a theme...", "id": None}] + user_themes,
                format_func=lambda x: x["name"],
                key="theme_management_select"
            )
            

        
        with col2:
            if theme_to_manage and theme_to_manage["id"]:
                # Add button to filter ticker list by this theme
                if st.button("🔍 Show Tickers in Theme", key="filter_by_theme_btn", help="Filter ticker list to show only tickers in this theme"):
                    st.session_state.selected_theme_filter = theme_to_manage["id"]
                    st.session_state.page = 1
                    st.rerun()
                
                # Get theme statistics
                theme_tickers = theme_repo.get_tickers_by_theme(theme_to_manage["id"], user_id)
                ticker_count = len(theme_tickers)
                
                # Allow deletion regardless of orphaned tickers
                if st.button(f"🗑️ Delete Theme", 
                           type="secondary", 
                           key="delete_theme_btn"):
                    # First remove all ticker-theme relationships (makes tickers orphaned if needed)
                    for ticker in theme_tickers:
                        theme_repo.remove_ticker_from_theme(ticker['id'], theme_to_manage["id"])
                    
                    # Then delete the theme
                    if theme_repo.delete_theme(theme_to_manage["id"], user_id):
                        if ticker_count > 0:
                            st.success(f"✅ Deleted theme '{theme_to_manage['name']}' - {ticker_count} ticker(s) are now orphaned")
                        else:
                            st.success(f"✅ Deleted theme '{theme_to_manage['name']}'")
                        # Reset theme filter if we deleted the currently filtered theme
                        if st.session_state.selected_theme_filter == theme_to_manage["id"]:
                            st.session_state.selected_theme_filter = None
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to delete theme '{theme_to_manage['name']}'")
        
        with col3:
            if theme_to_manage and theme_to_manage["id"]:
                st.info(f"💡 Theme has {ticker_count} ticker(s). Will be orphaned if deleted.")
    else:
        st.info("💡 No themes created yet. Create your first theme above to organize your tickers!")
        
        st.divider()
    
    # Fetch data based on theme filter
    try:
        if st.session_state.selected_theme_filter == "ORPHANED":
            # Get orphaned tickers
            all_orphaned_tickers = theme_repo.get_orphaned_tickers(
                user_id, 
                search_query=st.session_state.search_query if st.session_state.search_query else None,
                sort_by=st.session_state.sort_by,
                sort_dir=st.session_state.sort_dir
            )
            
            # Apply pagination
            total_count = len(all_orphaned_tickers)
            start_idx = (st.session_state.page - 1) * st.session_state.page_size
            end_idx = start_idx + st.session_state.page_size
            tickers = all_orphaned_tickers[start_idx:end_idx]
        elif st.session_state.selected_theme_filter:
            # Get tickers for specific theme
            all_theme_tickers = theme_repo.get_tickers_by_theme(st.session_state.selected_theme_filter, user_id)
            
            # Apply search filter if provided
            if st.session_state.search_query:
                search_lower = st.session_state.search_query.lower()
                all_theme_tickers = [t for t in all_theme_tickers if search_lower in t['symbol'].lower()]
            
            # Apply sorting
            reverse = st.session_state.sort_dir == 'DESC'
            if st.session_state.sort_by == 'symbol':
                all_theme_tickers.sort(key=lambda x: x['symbol'], reverse=reverse)
            elif st.session_state.sort_by == 'created_at':
                all_theme_tickers.sort(key=lambda x: x.get('created_at', ''), reverse=reverse)
            elif st.session_state.sort_by == 'last_updated':
                all_theme_tickers.sort(key=lambda x: x.get('last_updated', ''), reverse=reverse)
            
            # Apply pagination
            total_count = len(all_theme_tickers)
            start_idx = (st.session_state.page - 1) * st.session_state.page_size
            end_idx = start_idx + st.session_state.page_size
            tickers = all_theme_tickers[start_idx:end_idx]
        else:
            # Get all tickers (existing logic)
            tickers, total_count = repo.get_all(
                page=st.session_state.page,
                page_size=st.session_state.page_size,
                sort_by=st.session_state.sort_by,
                sort_dir=st.session_state.sort_dir,
                search_query=st.session_state.search_query if st.session_state.search_query else None,
                user_id=user_id
            )
        
        # Display count with context
        context_info = []
        if st.session_state.selected_theme_filter == "ORPHANED":
            context_info.append("🔺 Orphaned Tickers")
        elif st.session_state.selected_theme_filter:
            # Get theme name
            user_themes = theme_repo.get_user_themes(user_id)
            theme_name = next((t['name'] for t in user_themes if t['id'] == st.session_state.selected_theme_filter), 'Unknown')
            context_info.append(f"Theme: {theme_name}")
        
        if st.session_state.search_query:
            context_info.append(f"Search: '{st.session_state.search_query}'")
        
        if context_info:
            st.write(f"Found {format_count(total_count)} ticker(s) ({', '.join(context_info)})")
        else:
            st.write(f"Total tickers: {format_count(total_count)}")
        
        # Show warning for orphaned tickers
        if st.session_state.selected_theme_filter == "ORPHANED" and total_count > 0:
            st.warning(f"⚠️ Found {total_count} orphaned ticker(s) with no theme assignments. Consider assigning them to themes or deleting them permanently.")
        
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
        
        # Reorder columns to show themes after symbol
        if 'themes' in df.columns:
            cols = list(df.columns)
            cols.remove('themes')
            if 'symbol' in cols:
                symbol_idx = cols.index('symbol')
                cols.insert(symbol_idx + 1, 'themes')
                df = df[cols]
        
        # Add selection column
        df.insert(0, 'Select', False)
        
        # Display clean ticker table
        st.markdown("## Ticker List")
        
        # Custom CSS for clean table design
        st.markdown("""
        <style>
        .ticker-table {
            width: 100%;
            max-width: 100%;
            margin-top: 1rem;
        }
        .ticker-row {
            display: grid;
            grid-template-columns: minmax(60px, 0.8fr) minmax(60px, 0.8fr) minmax(80px, 1fr) minmax(150px, 2fr) minmax(120px, 1.5fr) minmax(120px, 1.5fr);
            gap: 1rem;
            padding: 0.75rem 1rem;
            border-bottom: 1px solid #333;
            background: transparent;
            color: white;
            align-items: center;
            width: 100%;
        }
        .ticker-header {
            display: grid;
            grid-template-columns: minmax(60px, 0.8fr) minmax(60px, 0.8fr) minmax(80px, 1fr) minmax(150px, 2fr) minmax(120px, 1.5fr) minmax(120px, 1.5fr);
            gap: 1rem;
            padding: 1rem;
            font-weight: bold;
            color: white;
            background: transparent;
            border-bottom: 2px solid #666;
            width: 100%;
        }
        .select-cell {
            text-align: center;
        }
        .id-cell {
            font-family: monospace;
            color: #9ca3af;
            text-align: center;
        }
        .symbol-cell {
            color: white;
            font-weight: 600;
            font-family: monospace;
        }
        .date-cell {
            font-size: 0.9rem;
            color: #d1d5db;
            font-family: monospace;
        }
        .checkbox-style {
            transform: scale(1.2);
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Table container
        st.markdown('<div class="ticker-table">', unsafe_allow_html=True)
        
        # Header row
        st.markdown("""
        <div class="ticker-header">
            <div>Select</div>
            <div>id</div>
            <div>symbol</div>
            <div>themes</div>
            <div>added_date</div>
            <div>last_updated</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Data rows with selection checkboxes  
        selected_tickers = []
        for idx, row in df.iterrows():
            # Use 6 columns to match the header: Select, ID, Symbol, Themes, Added Date, Last Updated
            col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 2, 1.5, 1.5])
            
            with col1:
                is_selected = st.checkbox(
                    "", 
                    key=f"select_{row['id']}",
                    label_visibility="collapsed"
                )
                if is_selected:
                    selected_tickers.append(row['id'])
            
            with col2:
                st.markdown(f'<div class="id-cell">{row["id"]}</div>', unsafe_allow_html=True)
            
            with col3:
                st.markdown(f'<div class="symbol-cell">{row["symbol"]}</div>', unsafe_allow_html=True)
            
            with col4:
                # Get themes for this ticker
                try:
                    ticker_themes = theme_repo.get_themes_for_ticker(row['id'], user_id)
                    if ticker_themes and isinstance(ticker_themes, list):
                        themes_text = ', '.join([t['name'] for t in ticker_themes if isinstance(t, dict) and 'name' in t])
                        if themes_text:
                            st.markdown(f'<div class="date-cell">{themes_text}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown('<div class="date-cell" style="color: #ffa500;">🔺 ORPHANED</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="date-cell" style="color: #ffa500;">🔺 ORPHANED</div>', unsafe_allow_html=True)
                except Exception as e:
                    # Show error in themes column for debugging
                    st.markdown(f'<div class="date-cell" style="color: red;">Error: {str(e)}</div>', unsafe_allow_html=True)
            
            with col5:
                added_date = row.get('created_at', 'N/A')
                if added_date != 'N/A' and len(str(added_date)) > 10:
                    added_date = str(added_date)[:10]  # Show just date part
                st.markdown(f'<div class="date-cell">{added_date}</div>', unsafe_allow_html=True)
            
            with col6:
                last_updated = row.get('last_updated', 'N/A')
                if last_updated != 'N/A' and len(str(last_updated)) > 10:
                    last_updated = str(last_updated)[:10]  # Show just date part
                st.markdown(f'<div class="date-cell">{last_updated}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Pagination controls
        total_pages = (total_count + st.session_state.page_size - 1) // st.session_state.page_size
        
        if total_pages > 1:
            col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
            
            with col1:
                if st.button("⏮️ First", disabled=st.session_state.page == 1, key="dashboard_first_btn"):
                    st.session_state.page = 1
                    st.rerun()

            with col2:
                if st.button("◀️ Prev", disabled=st.session_state.page == 1, key="dashboard_prev_btn"):
                    st.session_state.page -= 1
                    st.rerun()

            with col3:
                st.write(f"Page {st.session_state.page} of {total_pages}")
            
            with col4:
                if st.button("Next ▶️", disabled=st.session_state.page >= total_pages, key="dashboard_next_btn"):
                    st.session_state.page += 1
                    st.rerun()

            with col5:
                if st.button("Last ⏭️", disabled=st.session_state.page >= total_pages, key="dashboard_last_btn"):
                    st.session_state.page = total_pages
                    st.rerun()
        
        # Bulk actions for selected tickers
        if selected_tickers:
            st.markdown("---")  # Add separator line
            st.markdown(f"### Actions for Selected Tickers ({len(selected_tickers)} selected)")
            
            # Theme-aware delete button text and info
            if st.session_state.selected_theme_filter == "ORPHANED":
                button_text = "🗑️ Delete Permanently"
                info_text = "💡 Will delete orphaned tickers permanently (recommended cleanup)."
                info_type = "info"
            elif st.session_state.selected_theme_filter:
                theme_name = next((t['name'] for t in user_themes if t['id'] == st.session_state.selected_theme_filter), 'Unknown')
                button_text = f"🗑️ Remove from '{theme_name}'"
                info_text = f"💡 Will only remove from theme '{theme_name}'. Tickers in other themes will remain."
                info_type = "info"
            else:
                button_text = "🗑️ Delete Selected"
                info_text = "⚠️ Will delete tickers permanently from all themes."
                info_type = "warning"
            
            # Display info message
            if info_type == "info":
                st.info(info_text)
            else:
                st.warning(info_text)
            
            # Display the action button prominently
            if st.button(button_text, type="primary", key="dashboard_delete_btn", use_container_width=True):
                    try:
                        if st.session_state.selected_theme_filter == "ORPHANED":
                            # Delete orphaned tickers permanently (recommended)
                            deleted_count = repo.bulk_delete(selected_tickers)
                            if deleted_count > 0:
                                st.success(f"✅ Permanently deleted {deleted_count} orphaned ticker(s)")
                                st.rerun()
                            else:
                                st.error("Failed to delete orphaned tickers")
                        elif st.session_state.selected_theme_filter:
                            # Remove from theme only
                            theme_id = st.session_state.selected_theme_filter
                            if theme_id:
                                removed_count = 0
                                for ticker_id in selected_tickers:
                                    if theme_repo.remove_ticker_from_theme(theme_id, ticker_id):
                                        removed_count += 1
                                
                                if removed_count > 0:
                                    theme_name = next((t['name'] for t in user_themes if t['id'] == st.session_state.selected_theme_filter), 'Unknown')
                                    st.success(f"✅ Removed {removed_count} ticker(s) from theme '{theme_name}'")
                                    st.rerun()
                                else:
                                    st.error("Failed to remove tickers from theme")
                        else:
                            # Delete tickers entirely (original behavior)
                            deleted_count = repo.bulk_delete(selected_tickers)
                            if deleted_count > 0:
                                st.success(f"✅ Deleted {deleted_count} ticker(s)")
                                st.rerun()
                            else:
                                st.error("Failed to delete tickers")
                    except Exception as e:
                        st.error(f"Error during operation: {str(e)}")
        
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
                help="Export tickers on current page to CSV",
                key="dashboard_export_page_btn"
            )
        
        with col2:
            if st.button("📥 Export All Tickers", key="dashboard_export_btn"):
                try:
                    all_tickers = repo.get_active_tickers()
                    if all_tickers:
                        csv_data = pd.DataFrame({'symbol': all_tickers})
                        st.download_button(
                            label="Download All Tickers CSV",
                            data=csv_data.to_csv(index=False),
                            file_name="all_tickers_export.csv",
                            mime="text/csv",
                            key="dashboard_export_all_btn"
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
