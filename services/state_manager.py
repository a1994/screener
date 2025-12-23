"""Service for exporting and importing application state."""

import csv
import io
import logging
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import pandas as pd
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

from database import (
    TickerRepository,
    ThemeRepository,
    UserRepository,
)

logger = logging.getLogger(__name__)

# Load environment variables from .env file (for local development)
load_dotenv()

# External database connection details for storing exports
# Try to get from Streamlit secrets first (for cloud), then from env vars, then use default
def get_external_db_url():
    """Get external database URL from various sources."""
    try:
        # Try Streamlit secrets first (for Streamlit Cloud)
        import streamlit as st
        if hasattr(st, 'secrets') and 'EXTERNAL_DATABASE_URL' in st.secrets:
            return st.secrets['EXTERNAL_DATABASE_URL']
    except Exception:
        pass
    
    # Fall back to environment variable (for local .env)
    db_url = os.getenv('EXTERNAL_DATABASE_URL')
    if db_url:
        return db_url
    
    # Fallback to hardcoded (shouldn't be used in production)
    return "postgresql://neondb_owner:npg_6mgtZhckefV2@ep-restless-sound-adaky0fn-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

EXTERNAL_DB_URL = get_external_db_url()


class StateManager:
    """Manages export and import of application state."""

    def __init__(self):
        """Initialize repositories."""
        self.ticker_repo = TickerRepository()
        self.theme_repo = ThemeRepository()
        self.user_repo = UserRepository()
        
    def _init_export_table(self):
        """Initialize the export history table in external database if it doesn't exist."""
        try:
            conn = psycopg2.connect(EXTERNAL_DB_URL)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS export_history (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(255) NOT NULL,
                    filename VARCHAR(255) NOT NULL,
                    csv_content TEXT NOT NULL,
                    record_count INTEGER,
                    export_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    import_date TIMESTAMP
                )
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info("Export history table initialized")
        except Exception as e:
            logger.warning(f"Could not initialize export table: {e}")
    
    def _save_export_to_db(self, username: str, filename: str, csv_content: str, record_count: int):
        """Save export metadata and content to external database."""
        try:
            self._init_export_table()
            conn = psycopg2.connect(EXTERNAL_DB_URL)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO export_history (username, filename, csv_content, record_count, export_date)
                VALUES (%s, %s, %s, %s, %s)
            """, (username, filename, csv_content, record_count, datetime.now()))
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(f"Exported state saved to database: {filename}")
        except Exception as e:
            logger.error(f"Failed to save export to database: {e}")
            # Don't raise - export to CSV still succeeded even if DB save fails

    def export_state(self, user_id: int) -> Tuple[bytes, str]:
        """
        Export all user data to CSV format.
        Includes: username, tickers, themes, and theme-ticker associations.

        Args:
            user_id: User ID to export

        Returns:
            Tuple of (CSV bytes, filename)
        """
        try:
            # Get user info
            user = self.user_repo.get_user_by_id(user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")

            username = user["username"]

            # Get all tickers for user
            tickers = self.ticker_repo.get_active_tickers(user_id=user_id)
            if not tickers:
                tickers = []

            # Get all themes for user
            themes = self.theme_repo.get_user_themes(user_id=user_id)
            if not themes:
                themes = []

            # Create CSV in memory
            output = io.StringIO()
            writer = csv.writer(output)

            # Write header
            writer.writerow(
                [
                    "export_type",
                    "username",
                    "ticker_symbol",
                    "theme_name",
                    "theme_description",
                    "export_date",
                ]
            )

            # Write user info (single row with username)
            export_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow(
                ["USER", username, "", "", "", export_date]
            )

            # Write themes
            for theme in themes:
                writer.writerow(
                    [
                        "THEME",
                        username,
                        "",
                        theme["name"],
                        theme.get("description", ""),
                        export_date,
                    ]
                )

            # Write tickers with their theme assignments
            for ticker_symbol in tickers:
                ticker = self.ticker_repo.get_by_symbol(ticker_symbol, user_id=user_id)
                if ticker:
                    # Get themes for this ticker
                    ticker_themes = self.theme_repo.get_themes_for_ticker(
                        ticker["id"], user_id=user_id
                    )
                    if ticker_themes:
                        for theme in ticker_themes:
                            writer.writerow(
                                [
                                    "TICKER_THEME",
                                    username,
                                    ticker_symbol,
                                    theme["name"],
                                    "",
                                    export_date,
                                ]
                            )
                    else:
                        # Ticker with no theme
                        writer.writerow(
                            ["TICKER", username, ticker_symbol, "", "", export_date]
                        )

            # Convert to bytes
            csv_bytes = output.getvalue().encode("utf-8")
            csv_string = output.getvalue()
            filename = f"{username}_state_{export_date.replace(':', '-').replace(' ', '_')}.csv"

            # Save to external database
            record_count = len(tickers) + len(themes)
            self._save_export_to_db(username, filename, csv_string, record_count)

            logger.info(
                f"Exported state for user {username}: {len(tickers)} tickers, {len(themes)} themes"
            )
            return csv_bytes, filename

        except Exception as e:
            logger.error(f"Error exporting state for user {user_id}: {e}")
            raise

    def import_state(self, csv_content: str, user_id: int) -> Dict[str, int]:
        """
        Import state from CSV file.
        Skips duplicates, creates themes if they don't exist.

        Args:
            csv_content: CSV file content as string
            user_id: User ID to import for

        Returns:
            Dictionary with counts: {'tickers_added': X, 'themes_created': X, 'skipped': X}
        """
        try:
            # Parse CSV
            reader = csv.DictReader(io.StringIO(csv_content))
            rows = list(reader)

            if not rows:
                raise ValueError("CSV file is empty")

            # Get user info
            user = self.user_repo.get_user_by_id(user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")

            username = user["username"]

            stats = {
                "tickers_added": 0,
                "themes_created": 0,
                "skipped": 0,
                "errors": [],
            }

            # Track created themes
            created_themes = {}

            # Process rows
            for row in rows:
                try:
                    export_type = row.get("export_type", "").strip().upper()
                    ticker_symbol = row.get("ticker_symbol", "").strip().upper()
                    theme_name = row.get("theme_name", "").strip()
                    theme_desc = row.get("theme_description", "").strip()

                    # Skip header row
                    if export_type == "EXPORT_TYPE":
                        continue

                    # Skip USER rows (username info)
                    if export_type == "USER":
                        continue

                    # Handle THEME rows - create themes
                    if export_type == "THEME" and theme_name:
                        # Check if theme already exists
                        existing_theme = self.theme_repo.get_theme_by_name(user_id, theme_name)

                        if not existing_theme:
                            # Create new theme
                            theme_id = self.theme_repo.create_theme(
                                user_id=user_id,
                                name=theme_name,
                                description=theme_desc,
                            )
                            if theme_id:
                                created_themes[theme_name] = True
                                stats["themes_created"] += 1
                                logger.info(f"Created theme: {theme_name}")
                        else:
                            stats["skipped"] += 1

                    # Handle TICKER rows - add tickers
                    elif export_type == "TICKER" and ticker_symbol:
                        result = self.ticker_repo.add_ticker(ticker_symbol, user_id)
                        if result:
                            stats["tickers_added"] += 1
                            logger.info(f"Added ticker: {ticker_symbol}")
                        else:
                            stats["skipped"] += 1

                    # Handle TICKER_THEME rows - associate ticker with theme
                    elif (
                        export_type == "TICKER_THEME"
                        and ticker_symbol
                        and theme_name
                    ):
                        # Get or create ticker
                        result = self.ticker_repo.add_ticker(ticker_symbol, user_id)
                        if result:
                            stats["tickers_added"] += 1
                        else:
                            # Ticker already exists
                            ticker = self.ticker_repo.get_by_symbol(
                                ticker_symbol, user_id
                            )
                            result = ticker["id"] if ticker else None

                        # Get or create theme
                        if theme_name:
                            existing_theme = self.theme_repo.get_theme_by_name(user_id, theme_name)
                            theme_id = None
                            if existing_theme:
                                theme_id = existing_theme["id"]

                            if not theme_id:
                                # Create theme if not exists
                                theme_id = self.theme_repo.create_theme(
                                    user_id=user_id,
                                    name=theme_name,
                                    description=theme_desc,
                                )
                                if theme_id:
                                    stats["themes_created"] += 1

                            # Associate ticker with theme if both exist
                            if result and theme_id:
                                try:
                                    self.theme_repo.add_ticker_to_theme(
                                        ticker_id=result, theme_id=theme_id
                                    )
                                    logger.info(
                                        f"Associated {ticker_symbol} with theme {theme_name}"
                                    )
                                except Exception as e:
                                    # Might already be associated
                                    logger.debug(
                                        f"Could not associate {ticker_symbol} with {theme_name}: {e}"
                                    )

                except Exception as row_error:
                    error_msg = f"Error processing row {row}: {row_error}"
                    logger.warning(error_msg)
                    stats["errors"].append(error_msg)

            logger.info(f"Import completed: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error importing state for user {user_id}: {e}")
            raise

    def get_user_exports(self, username: str) -> List[Dict]:
        """
        Get all saved exports for a user from the external database.

        Args:
            username: Username to fetch exports for

        Returns:
            List of export records with id, filename, export_date, record_count
        """
        try:
            self._init_export_table()
            conn = psycopg2.connect(EXTERNAL_DB_URL)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, filename, export_date, record_count
                FROM export_history
                WHERE username = %s
                ORDER BY export_date DESC
            """, (username,))
            
            exports = []
            for row in cursor.fetchall():
                exports.append({
                    "id": row[0],
                    "filename": row[1],
                    "export_date": row[2],
                    "record_count": row[3]
                })
            
            cursor.close()
            conn.close()
            
            logger.info(f"Retrieved {len(exports)} exports for user {username}")
            return exports
        except Exception as e:
            logger.error(f"Error fetching exports for user {username}: {e}")
            return []

    def get_export_csv(self, export_id: int) -> Optional[bytes]:
        """
        Get the CSV content of a specific export.

        Args:
            export_id: Export ID to fetch

        Returns:
            CSV content as bytes, or None if not found
        """
        try:
            self._init_export_table()
            conn = psycopg2.connect(EXTERNAL_DB_URL)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT csv_content, filename
                FROM export_history
                WHERE id = %s
            """, (export_id,))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result:
                csv_content = result[0]
                return csv_content.encode('utf-8')
            
            return None
        except Exception as e:
            logger.error(f"Error fetching export {export_id}: {e}")
            return None
