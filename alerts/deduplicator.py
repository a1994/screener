"""
Alert deduplication logic.
Enforces max 2 alerts per ticker rule: most recent OPEN + corresponding CLOSE.
"""

from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd


class AlertDeduplicator:
    """
    Deduplicates alerts to enforce max 2 alerts per ticker rule.
    Keeps most recent OPEN signal + corresponding CLOSE signal after that OPEN.
    """
    
    @staticmethod
    def deduplicate(signals_df: pd.DataFrame) -> List[Dict]:
        """
        Deduplicate signals to max 2 alerts per ticker.
        
        Strategy:
        1. Find most recent OPEN signal (LONG_OPEN or SHORT_OPEN, whichever is later)
        2. Find most recent CLOSE signal AFTER that OPEN
        3. Return up to 2 alerts: [OPEN, CLOSE] or just [OPEN] if no close yet
        
        Args:
            signals_df: DataFrame with 'signal' and 'date' columns
                       signal values: 'LONG_OPEN', 'LONG_CLOSE', 'SHORT_OPEN', 'SHORT_CLOSE'
                       
        Returns:
            List of alert dictionaries with keys: alert_type, signal_date, price
        """
        if signals_df is None or signals_df.empty:
            return []
        
        # Filter to only rows with signals
        signal_rows = signals_df[signals_df['signal'].notna()].copy()
        
        if signal_rows.empty:
            return []
        
        # Ensure date column is datetime
        if not pd.api.types.is_datetime64_any_dtype(signal_rows['date']):
            signal_rows['date'] = pd.to_datetime(signal_rows['date'])
        
        # Sort by date descending (most recent first)
        signal_rows = signal_rows.sort_values('date', ascending=False)
        
        alerts = []
        
        # Find most recent OPEN signal
        open_signals = signal_rows[
            signal_rows['signal'].isin(['LONG OPEN', 'SHORT OPEN'])
        ]
        
        if open_signals.empty:
            # No OPEN signals, check for orphaned CLOSE signals
            close_signals = signal_rows[
                signal_rows['signal'].isin(['LONG CLOSE', 'SHORT CLOSE'])
            ]
            
            if not close_signals.empty:
                # Return most recent CLOSE only (convert space to underscore)
                most_recent_close = close_signals.iloc[0]
                alerts.append({
                    'alert_type': most_recent_close['signal'].replace(' ', '_'),
                    'signal_date': most_recent_close['date'].strftime('%Y-%m-%d'),
                    'price': float(most_recent_close['close'])
                })
            
            return alerts
        
        # Get most recent OPEN
        most_recent_open = open_signals.iloc[0]
        open_date = most_recent_open['date']
        open_type = most_recent_open['signal']  # LONG_OPEN or SHORT_OPEN
        
        # Add OPEN alert (convert space to underscore for database)
        alert_type = open_type.replace(' ', '_')
        alerts.append({
            'alert_type': alert_type,
            'signal_date': open_date.strftime('%Y-%m-%d'),
            'price': float(most_recent_open['close'])
        })
        
        # Find corresponding CLOSE signal AFTER the OPEN
        # If OPEN is LONG OPEN, look for LONG CLOSE
        # If OPEN is SHORT OPEN, look for SHORT CLOSE
        close_type_signal = 'LONG CLOSE' if open_type == 'LONG OPEN' else 'SHORT CLOSE'
        close_type_db = close_type_signal.replace(' ', '_')
        
        close_signals = signal_rows[
            (signal_rows['signal'] == close_type_signal) &
            (signal_rows['date'] > open_date)
        ]
        
        if not close_signals.empty:
            # Get most recent CLOSE after the OPEN
            most_recent_close = close_signals.iloc[0]
            alerts.append({
                'alert_type': close_type_db,
                'signal_date': most_recent_close['date'].strftime('%Y-%m-%d'),
                'price': float(most_recent_close['close'])
            })
        
        # Sort alerts by date descending (latest first) before returning
        alerts.sort(key=lambda x: x['signal_date'], reverse=True)
        
        return alerts
    
    @staticmethod
    def validate_alerts(alerts: List[Dict]) -> bool:
        """
        Validate that alerts meet the max 2 alerts rule.
        
        Args:
            alerts: List of alert dictionaries
            
        Returns:
            True if valid, False otherwise
        """
        if len(alerts) > 2:
            return False
        
        if len(alerts) == 2:
            # Should have one OPEN and one CLOSE
            types = [alert['alert_type'] for alert in alerts]
            
            has_open = any(t in ['LONG_OPEN', 'SHORT_OPEN'] for t in types)
            has_close = any(t in ['LONG_CLOSE', 'SHORT_CLOSE'] for t in types)
            
            if not (has_open and has_close):
                return False
            
            # CLOSE date should be after or equal to OPEN date
            open_alert = next((a for a in alerts if a['alert_type'] in ['LONG_OPEN', 'SHORT_OPEN']), None)
            close_alert = next((a for a in alerts if a['alert_type'] in ['LONG_CLOSE', 'SHORT_CLOSE']), None)
            
            if open_alert and close_alert:
                open_date = datetime.strptime(open_alert['signal_date'], '%Y-%m-%d')
                close_date = datetime.strptime(close_alert['signal_date'], '%Y-%m-%d')
                
                if close_date < open_date:
                    return False
        
        return True
    
    @staticmethod
    def get_alert_summary(alerts: List[Dict]) -> str:
        """
        Get human-readable summary of alerts.
        
        Args:
            alerts: List of alert dictionaries
            
        Returns:
            Summary string
        """
        if not alerts:
            return "No alerts"
        
        if len(alerts) == 1:
            alert = alerts[0]
            return f"{alert['alert_type']} on {alert['signal_date']}"
        
        if len(alerts) == 2:
            # Assuming sorted by date descending
            first = alerts[0]
            second = alerts[1]
            return f"{first['alert_type']} on {first['signal_date']}, {second['alert_type']} on {second['signal_date']}"
        
        return f"{len(alerts)} alerts"
