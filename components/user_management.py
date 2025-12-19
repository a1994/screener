"""User management UI component for user selection and creation."""

import streamlit as st
import logging
from typing import Optional

from database.user_repository import UserRepository

logger = logging.getLogger(__name__)


def render_user_selector() -> int:
    """
    Render user selector in the top-right area of the app.
    Handles user creation and selection.
    
    Returns:
        Selected user ID
    """
    try:
        user_repo = UserRepository()
        
        # Initialize session state for current user
        if 'current_user_id' not in st.session_state:
            # Ensure default user exists and set as current
            default_user_id = user_repo.ensure_default_user()
            st.session_state.current_user_id = default_user_id
    except Exception as e:
        st.error(f"Failed to initialize user system: {str(e)}")
        # Return default user ID if database not ready
        if 'current_user_id' not in st.session_state:
            st.session_state.current_user_id = 1
        return st.session_state.current_user_id
    
    # Get all users for dropdown
    try:
        users = user_repo.get_all_users()
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return st.session_state.current_user_id
    
    if not users:
        st.error("No users found! Please restart the application.")
        return 1
    
    # Use container with proper width management
    with st.container():
        # User management area with fixed positioning
        st.markdown("""
        <div style="
            position: relative; 
            width: 100%; 
            display: flex; 
            justify-content: flex-end; 
            align-items: center; 
            gap: 15px; 
            padding: 10px 20px 10px 0;
            margin-bottom: 20px;
        ">
        </div>
        """, unsafe_allow_html=True)
        
        # Create two columns with better spacing
        col1, col2 = st.columns([7, 3])
        
        with col1:
            # User dropdown aligned to the right
            user_options = {user['id']: user['display_name'] for user in users}
            current_user = st.selectbox(
                "👤 User:",
                options=list(user_options.keys()),
                format_func=lambda x: user_options[x],
                index=list(user_options.keys()).index(st.session_state.current_user_id) if st.session_state.current_user_id in user_options else 0,
                key="user_selector",
                help="Select active user - only their tickers will be shown"
            )
            
            # Update session state when user changes
            if current_user != st.session_state.current_user_id:
                st.session_state.current_user_id = current_user
                st.rerun()  # Refresh the app with new user context
        
        with col2:
            st.write("")  # Add spacing
            # Create user button with compact styling
            if st.button("+ Add User", 
                        help="Create a new user account", 
                        key="user_add_btn"):
                st.session_state.show_add_user_form = True
                st.rerun()
    
    # Show add user form if triggered
    if st.session_state.get('show_add_user_form', False):
        _render_add_user_form(user_repo)
    
    return st.session_state.current_user_id


def _render_add_user_form(user_repo: UserRepository):
    """
    Render the add user form in a modal-like container.
    
    Args:
        user_repo: UserRepository instance
    """
    with st.container():
        st.markdown("---")
        st.subheader("➕ Add New User")
        
        with st.form("add_user_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                display_name = st.text_input(
                    "Display Name *",
                    placeholder="e.g., John Smith",
                    help="Human-readable name shown in the interface"
                )
            
            with col2:
                username = st.text_input(
                    "Username *",
                    placeholder="e.g., john.smith",
                    help="Unique identifier (lowercase, no spaces)"
                )
            
            # Form buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                submitted = st.form_submit_button("✅ Create User", type="primary", key="user_create_submit")
            
            with col2:
                cancelled = st.form_submit_button("❌ Cancel", key="user_create_cancel")
            
            # Handle form submission
            if submitted:
                if not display_name.strip():
                    st.error("Display name is required")
                elif not username.strip():
                    st.error("Username is required")
                else:
                    # Clean username (lowercase, no spaces)
                    clean_username = username.strip().lower().replace(' ', '.')
                    
                    # Attempt to create user
                    user_id = user_repo.add_user(clean_username, display_name.strip())
                    
                    if user_id:
                        st.success(f"✅ User '{display_name}' created successfully!")
                        st.session_state.current_user_id = user_id
                        st.session_state.show_add_user_form = False
                        st.rerun()
                    else:
                        st.error(f"❌ Username '{clean_username}' already exists. Please choose a different username.")
            
            if cancelled:
                st.session_state.show_add_user_form = False
                st.rerun()


def get_current_user() -> Optional[dict]:
    """
    Get the current user information from session state.
    
    Returns:
        Current user dictionary or None
    """
    if 'current_user_id' not in st.session_state:
        return None
    
    try:
        user_repo = UserRepository()
        return user_repo.get_user_by_id(st.session_state.current_user_id)
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        return None


def get_current_user_id() -> int:
    """
    Get the current user ID from session state.
    
    Returns:
        Current user ID (defaults to 1 if not set)
    """
    return st.session_state.get('current_user_id', 1)


def render_user_info_sidebar():
    """
    Render user information and stats in the sidebar.
    """
    current_user = get_current_user()
    
    if not current_user:
        return
    
    try:
        user_repo = UserRepository()
        stats = user_repo.get_user_stats(current_user['id'])
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return
    
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 👤 Current User")
        st.markdown(f"**{current_user['display_name']}**")
        st.markdown(f"Username: `{current_user['username']}`")
        
        # User statistics
        st.markdown("### 📊 Your Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Tickers", stats['ticker_count'])
        with col2:
            st.metric("Alerts", stats['alert_count'])
        
        # Show creation date
        created_date = current_user['created_at'][:10]  # YYYY-MM-DD
        st.caption(f"Member since: {created_date}")


def initialize_user_system():
    """
    Initialize the user system on app startup.
    Ensures default user exists and database is properly set up.
    """
    try:
        user_repo = UserRepository()
        user_repo.ensure_default_user()
        logger.info("User system initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize user system: {e}")
        # Don't show error in streamlit during initialization
        raise e


# User system will be initialized when first accessed