# Implementation Tasks

## 1. Database Schema Extension
- [x] 1.1 Create database migration script for alerts table
- [x] 1.2 Define alerts table schema (id, ticker_id, ticker_symbol, alert_type, signal_date, price, created_at)
- [x] 1.3 Add foreign key constraint (ticker_id → tickers.id ON DELETE CASCADE)
- [x] 1.4 Create indexes on ticker_id, signal_date, created_at
- [x] 1.5 Add CHECK constraint for alert_type enum validation
- [x] 1.6 Test schema with sample inserts and constraint violations

## 2. Alert Repository Layer
- [x] 2.1 Create `database/alert_repository.py` module
- [x] 2.2 Implement get_all() with pagination and sorting
- [x] 2.3 Implement update_for_ticker() with transaction handling
- [x] 2.4 Implement delete_for_ticker() for cascade cleanup
- [x] 2.5 Implement get_total_count() for pagination calculation
- [x] 2.6 Add batch query operations for performance

## 3. Alert Generation Logic
- [x] 3.1 Create `alerts/__init__.py` module
- [x] 3.2 Implement `alerts/generator.py` AlertGenerator class
- [x] 3.3 Add generate_for_ticker() method (reuse chart analysis signal logic)
- [x] 3.4 Add generate_for_all_tickers() method for bulk refresh
- [x] 3.5 Integrate with FMP API client and indicator calculator
- [x] 3.6 Add error handling for signal generation failures

## 4. Alert Deduplication Logic
- [x] 4.1 Create `alerts/deduplicator.py` module
- [x] 4.2 Implement extract_recent_signals() with max 2 alerts logic
- [x] 4.3 Implement get_most_recent_open() to find latest OPEN signal (Long or Short)
- [x] 4.4 Implement get_corresponding_close() to find CLOSE after OPEN
- [x] 4.5 Handle edge cases (only open, no close, multiple signals same day)
- [x] 4.6 Add unit tests for all deduplication scenarios

## 5. Alert Lifecycle Management
- [x] 5.1 Implement delete-old-alerts logic when new position opens
- [x] 5.2 Add transaction handling for atomic alert replacement
- [x] 5.3 Ensure foreign key cascade delete when ticker deleted
- [x] 5.4 Add alert age tracking (created_at timestamp)
- [x] 5.5 Test concurrent alert updates

## 6. Refresh All Functionality
- [x] 6.1 Create `alerts/refresher.py` AlertRefresher class
- [x] 6.2 Implement refresh_all() with progress tracking
- [x] 6.3 Add rate limiting between API calls (500ms delay)
- [x] 6.4 Implement error collection and reporting
- [x] 6.5 Add success/failure count tracking
- [x] 6.6 Optimize batch processing for performance

## 7. Background Alert Generation on Ticker Add
- [x] 7.1 Modify `database/ticker_repository.py` bulk_insert() method
- [x] 7.2 Add threading.Thread() call for async alert generation
- [x] 7.3 Ensure non-blocking behavior during ticker insertion
- [x] 7.4 Add error handling for background thread failures
- [x] 7.5 Test ticker addition with alert generation verification

## 8. Alerts Tab User Interface
- [x] 8.1 Create `components/alerts_tab.py` module
- [x] 8.2 Implement main alerts tab layout
- [x] 8.3 Add total alert count display
- [x] 8.4 Add sort dropdown (Latest First, Oldest First)
- [x] 8.5 Implement "Refresh All" button with confirmation
- [x] 8.6 Add progress bar for refresh operations
- [x] 8.7 Display error summary after refresh

## 9. Alert Table Display
- [x] 9.1 Implement display_alerts_table() function
- [x] 9.2 Fetch paginated alerts from database
- [x] 9.3 Convert to pandas DataFrame for display
- [x] 9.4 Apply color-coding to alert types (green/red/orange/cyan)
- [x] 9.5 Display table with st.dataframe()
- [x] 9.6 Add empty state message when no alerts exist

## 10. Pagination Controls
- [x] 10.1 Implement session state management for current page
- [x] 10.2 Add Previous/Next buttons
- [x] 10.3 Display page indicator (Page X of Y)
- [x] 10.4 Display results count (Showing X of Y alerts)
- [x] 10.5 Disable buttons at first/last page boundaries
- [x] 10.6 Test pagination with various alert counts (0, 1, 20, 500, 1000+)

## 11. Alert Sorting
- [x] 11.1 Implement sort by signal_date DESC (default)
- [x] 11.2 Implement sort by signal_date ASC
- [x] 11.3 Use SQL ORDER BY for efficient sorting
- [x] 11.4 Maintain sort selection in session state
- [x] 11.5 Test sorting with large datasets

## 12. Refresh All Progress Tracking
- [x] 12.1 Implement st.progress() bar during refresh
- [x] 12.2 Add status text showing current ticker being processed
- [x] 12.3 Calculate and display percentage complete
- [x] 12.4 Show estimated time remaining (optional)
- [x] 12.5 Clear progress indicators after completion

## 13. Error Handling & User Feedback
- [x] 13.1 Handle database connection errors during alert operations
- [x] 13.2 Handle API failures during alert generation
- [x] 13.3 Display user-friendly error messages with st.error()
- [x] 13.4 Show success messages with st.success()
- [x] 13.5 Add expandable error details section
- [x] 13.6 Log errors to file for debugging

## 14. Integration with Ticker Management
- [x] 14.1 Test alert generation when tickers added via comma-separated input
- [x] 14.2 Test alert generation when tickers added via CSV upload
- [x] 14.3 Verify alerts appear in Alerts tab after ticker addition
- [x] 14.4 Test ticker deletion cascades to alert deletion
- [x] 14.5 Verify session state consistency across tabs

## 15. Integration with Chart Analysis
- [x] 15.1 Reuse signal generation logic from chart-analysis module
- [x] 15.2 Ensure indicator calculations are consistent
- [x] 15.3 Verify signal dates match between chart markers and alerts
- [x] 15.4 Test cache integration for alert refresh
- [x] 15.5 Verify performance with shared caching

## 16. Testing
- [x] 16.1 Create `tests/test_alert_generator.py` with mock signals
- [x] 16.2 Create `tests/test_deduplication.py` with edge case scenarios
- [x] 16.3 Create `tests/test_alert_repository.py` for database operations
- [x] 16.4 Test alert lifecycle (create → update → delete)
- [x] 16.5 Test deduplication with various signal patterns
- [x] 16.6 Test pagination edge cases
- [x] 16.7 Test concurrent operations (add ticker + refresh all)
- [x] 16.8 Achieve >80% test coverage on alert modules

## 17. Performance Testing
- [x] 17.1 Test Refresh All with 100 tickers (target: <5 minutes)
- [x] 17.2 Test alert display with 1000+ alerts (target: <1 second load)
- [x] 17.3 Test pagination with 10,000+ alerts
- [x] 17.4 Test background alert generation performance
- [x] 17.5 Benchmark database query performance
- [x] 17.6 Optimize slow operations

## 18. Documentation
- [x] 18.1 Document alert deduplication rules with examples
- [x] 18.2 Document alert lifecycle and state transitions
- [x] 18.3 Add docstrings to all alert-related functions
- [x] 18.4 Create user guide for Alerts tab
- [x] 18.5 Document API rate limiting considerations

## 19. Integration & Deployment
- [x] 19.1 Integrate Alerts tab into main app.py
- [x] 19.2 Test full workflow: add ticker → generate alerts → view in Alerts tab
- [x] 19.3 Test Refresh All with real tickers and API
- [x] 19.4 Verify foreign key constraints work correctly
- [x] 19.5 Test with multiple concurrent users (if applicable)
- [x] 19.6 Perform end-to-end user acceptance testing
