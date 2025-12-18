# alert-system Specification

## Purpose
TBD - created by archiving change add-alert-system. Update Purpose after archive.
## Requirements
### Requirement: Alerts Database Schema
The system SHALL provide a database table for storing trading signal alerts with foreign key relationships to tickers.

#### Scenario: Alerts table creation with constraints
- **WHEN** the database is initialized with the alert system
- **THEN** the system SHALL create an alerts table with columns: id, ticker_id, ticker_symbol, alert_type, signal_date, price, created_at
- **AND** the ticker_id column SHALL have a foreign key constraint to tickers.id with CASCADE delete
- **AND** the alert_type column SHALL have a CHECK constraint allowing only: 'Long - OPEN', 'Long - CLOSE', 'Short - OPEN', 'Short - CLOSE'
- **AND** indexes SHALL be created on ticker_id, signal_date DESC, and created_at DESC

#### Scenario: Alert cascade delete on ticker removal
- **WHEN** a ticker is deleted from the tickers table
- **THEN** all associated alerts SHALL be automatically deleted via CASCADE
- **AND** no orphaned alert records SHALL remain in the database

### Requirement: Alert Generation from Trading Signals
The system SHALL generate alerts by analyzing historical price data and extracting the most recent trading signals for each ticker.

#### Scenario: Generate alerts for ticker with Long position
- **WHEN** the system generates alerts for ticker "AAPL"
- **AND** the most recent signal is Long OPEN on 2025-11-20
- **AND** a Long CLOSE exists on 2025-11-21
- **THEN** the system SHALL create 2 alert records: one for Long OPEN, one for Long CLOSE
- **AND** both alerts SHALL reference the same ticker_id
- **AND** alert_type SHALL be 'Long - OPEN' and 'Long - CLOSE' respectively

#### Scenario: Generate alerts for ticker with only OPEN signal
- **WHEN** the system generates alerts for a ticker
- **AND** the most recent signal is Short OPEN on 2025-11-25
- **AND** no subsequent Short CLOSE signal exists
- **THEN** the system SHALL create 1 alert record for Short OPEN only
- **AND** no CLOSE alert SHALL be created

#### Scenario: No signals found for ticker
- **WHEN** the system analyzes a ticker's historical data
- **AND** no Long OPEN, Long CLOSE, Short OPEN, or Short CLOSE signals are detected
- **THEN** the system SHALL not create any alert records for that ticker
- **AND** the system SHALL log this condition for debugging

### Requirement: Alert Deduplication - Maximum 2 Alerts Per Ticker
The system SHALL enforce a maximum of 2 alerts per ticker: one position OPEN and one position CLOSE from the same signal cycle.

#### Scenario: Replace old alerts when new position opens
- **WHEN** ticker "HOOD" has existing alerts: Long OPEN (2025-11-20) and Long CLOSE (2025-11-21)
- **AND** a new Long OPEN signal occurs on 2025-11-25
- **THEN** the system SHALL delete both previous alert records
- **AND** the system SHALL create a new alert record for Long OPEN on 2025-11-25
- **AND** exactly 1 alert SHALL exist for "HOOD" after this operation

#### Scenario: Add close alert to existing open
- **WHEN** ticker "TSLA" has 1 alert: Short OPEN (2025-11-22)
- **AND** a Short CLOSE signal occurs on 2025-11-24
- **THEN** the system SHALL create a new alert record for Short CLOSE on 2025-11-24
- **AND** exactly 2 alerts SHALL exist for "TSLA": Short OPEN and Short CLOSE

#### Scenario: Direction change from Long to Short
- **WHEN** ticker "MSFT" has alerts: Long OPEN (2025-11-10) and Long CLOSE (2025-11-12)
- **AND** a new Short OPEN signal occurs on 2025-11-15
- **THEN** the system SHALL delete both Long alerts
- **AND** the system SHALL create a new alert for Short OPEN on 2025-11-15
- **AND** the alert direction SHALL reflect the most recent signal type

### Requirement: Most Recent Signal Selection
The system SHALL select alerts based on the most recent position direction, choosing between Long and Short based on which OPEN signal occurred latest.

#### Scenario: Long OPEN more recent than Short OPEN
- **WHEN** a ticker has Long OPEN on 2025-11-20 and Short OPEN on 2025-11-15
- **THEN** the system SHALL select Long OPEN as the most recent position
- **AND** the system SHALL search for Long CLOSE signals after 2025-11-20
- **AND** Short signals SHALL be ignored for alert generation

#### Scenario: Short OPEN more recent than Long OPEN
- **WHEN** a ticker has Long OPEN on 2025-11-10 and Short OPEN on 2025-11-18
- **THEN** the system SHALL select Short OPEN as the most recent position
- **AND** the system SHALL search for Short CLOSE signals after 2025-11-18
- **AND** Long signals SHALL be ignored for alert generation

### Requirement: Alert Generation on Ticker Addition
The system SHALL automatically trigger alert generation when new tickers are added to the database.

#### Scenario: Background alert generation after CSV upload
- **WHEN** a user uploads a CSV file with 50 ticker symbols
- **AND** all tickers are successfully inserted into the database
- **THEN** the system SHALL initiate background alert generation for each ticker
- **AND** alert generation SHALL not block the UI
- **AND** users SHALL be able to continue using other tabs during generation

#### Scenario: Alert generation uses threading for non-blocking behavior
- **WHEN** alert generation is triggered for a newly added ticker
- **THEN** the system SHALL spawn a background thread using threading.Thread()
- **AND** the thread SHALL run with daemon=True to prevent hanging on app exit
- **AND** any exceptions in the thread SHALL be logged without crashing the main app

### Requirement: Refresh All Alerts Functionality
The system SHALL provide a "Refresh All" button that updates alerts for all active tickers in the database.

#### Scenario: Refresh All with progress tracking
- **WHEN** a user clicks the "Refresh All" button in the Alerts tab
- **AND** the database contains 50 active tickers
- **THEN** the system SHALL display a progress bar starting at 0%
- **AND** the system SHALL iterate through each ticker sequentially
- **AND** for each ticker, the system SHALL update the status text showing "Refreshing [SYMBOL] (X of Y)..."
- **AND** the progress bar SHALL update incrementally with each completed ticker
- **AND** the progress bar SHALL reach 100% when all tickers are processed

#### Scenario: Refresh All with API rate limiting
- **WHEN** the system refreshes alerts for multiple tickers
- **THEN** the system SHALL wait 500 milliseconds between each ticker refresh
- **AND** this delay SHALL prevent API rate limit violations
- **AND** the total refresh time for 100 tickers SHALL not exceed 5 minutes

#### Scenario: Refresh All error handling
- **WHEN** the system encounters an error while refreshing a specific ticker
- **THEN** the system SHALL log the error with ticker symbol and details
- **AND** the system SHALL continue processing remaining tickers
- **AND** after completion, the system SHALL display a summary showing success count and error count
- **AND** users SHALL be able to expand an error details section to view which tickers failed

### Requirement: Alert Display with Pagination
The system SHALL display alerts in a paginated table with 20 alerts per page, sorted by date.

#### Scenario: Display alerts in tabular format
- **WHEN** a user navigates to the Alerts tab
- **AND** alerts exist in the database
- **THEN** the system SHALL display a table with columns: Ticker, Alert Type, Date, Price
- **AND** the system SHALL show a maximum of 20 alerts per page
- **AND** the system SHALL display the total alert count at the top

#### Scenario: No alerts available
- **WHEN** a user navigates to the Alerts tab
- **AND** no alerts exist in the database
- **THEN** the system SHALL display an info message "No alerts found. Add tickers and click 'Refresh All' to generate alerts."
- **AND** the system SHALL not display an empty table

#### Scenario: Alert table color coding
- **WHEN** the system displays the alert table
- **THEN** Long OPEN alerts SHALL have a green background
- **AND** Long CLOSE alerts SHALL have a red background
- **AND** Short OPEN alerts SHALL have an orange background
- **AND** Short CLOSE alerts SHALL have a cyan background
- **AND** text SHALL be white and bold for contrast

### Requirement: Alert Sorting by Date
The system SHALL support sorting alerts by signal date in both ascending and descending order.

#### Scenario: Default sorting - latest first
- **WHEN** the Alerts tab loads for the first time
- **THEN** alerts SHALL be sorted by signal_date in descending order (latest first)
- **AND** the most recent alert SHALL appear at the top of the first page

#### Scenario: User selects oldest first sorting
- **WHEN** a user selects "Oldest First" from the sort dropdown
- **THEN** the system SHALL re-query alerts sorted by signal_date ascending
- **AND** the oldest alert SHALL appear at the top of the first page
- **AND** the sort selection SHALL persist in session state

#### Scenario: Sorting with secondary sort on created_at
- **WHEN** multiple alerts have the same signal_date
- **THEN** the system SHALL use created_at as a secondary sort criterion
- **AND** this SHALL maintain a consistent, deterministic order

### Requirement: Alert Pagination Controls
The system SHALL provide pagination controls for navigating through multiple pages of alerts.

#### Scenario: Navigate to next page
- **WHEN** a user is viewing page 1 of alerts
- **AND** more than 20 alerts exist in the database
- **AND** the user clicks the "Next →" button
- **THEN** the system SHALL display page 2 with the next 20 alerts
- **AND** the page indicator SHALL update to show "Page 2 of X"

#### Scenario: Navigate to previous page
- **WHEN** a user is viewing page 3 of alerts
- **AND** the user clicks the "← Previous" button
- **THEN** the system SHALL display page 2
- **AND** the page indicator SHALL update accordingly

#### Scenario: Pagination boundary conditions
- **WHEN** a user is on page 1
- **THEN** the "Previous" button SHALL be disabled or hidden
- **WHEN** a user is on the last page
- **THEN** the "Next" button SHALL be disabled or hidden

#### Scenario: Pagination state persistence
- **WHEN** a user navigates to page 3 of alerts
- **AND** switches to another tab (Dashboard or Chart Analysis)
- **AND** returns to the Alerts tab
- **THEN** the system SHALL remember and display page 3
- **AND** pagination state SHALL be stored in st.session_state

### Requirement: Alert Repository Operations
The system SHALL provide database operations for managing alert lifecycle including create, read, update, and delete.

#### Scenario: Atomic alert update for ticker
- **WHEN** the system updates alerts for a ticker
- **THEN** the system SHALL begin a database transaction
- **AND** the system SHALL delete all existing alerts for that ticker_id
- **AND** the system SHALL insert new alert records
- **AND** the system SHALL commit the transaction atomically
- **AND** if any step fails, the system SHALL rollback all changes

#### Scenario: Get paginated alerts with total count
- **WHEN** the system fetches alerts for display (page 2, 20 per page)
- **THEN** the system SHALL execute a query with LIMIT 20 OFFSET 20
- **AND** the system SHALL execute a separate COUNT query for total alerts
- **AND** both queries SHALL use the same WHERE clause and sorting
- **AND** the system SHALL return alerts and total count together

### Requirement: Integration with Signal Generation Logic
The system SHALL reuse the signal detection logic from the chart-analysis module to ensure consistency between chart markers and alerts.

#### Scenario: Alert signals match chart signals
- **WHEN** the system generates alerts for ticker "AAPL"
- **AND** a chart is loaded for "AAPL" in the Chart Analysis tab
- **THEN** the alert dates SHALL exactly match the signal marker dates on the chart
- **AND** signal types SHALL match (Long OPEN alert = green triangle on chart)
- **AND** prices SHALL match the close price on the signal date

#### Scenario: Shared caching benefits alert generation
- **WHEN** a user loads a chart for "TSLA" (fetches and caches data)
- **AND** subsequently triggers alert generation for "TSLA"
- **THEN** the alert generation SHALL use cached price data
- **AND** no additional API call SHALL be made for "TSLA"
- **AND** alert generation SHALL complete faster due to cache hit

### Requirement: Alert System Performance Standards
The system SHALL meet defined performance targets for alert operations.

#### Scenario: Alert display load time
- **WHEN** the Alerts tab is loaded with 1000 alerts in the database
- **THEN** the first page of 20 alerts SHALL load and display in less than 1 second
- **AND** the total count query SHALL complete in less than 100 milliseconds

#### Scenario: Refresh All completion time
- **WHEN** a user triggers Refresh All with 100 tickers in the database
- **THEN** the complete refresh operation SHALL finish in less than 5 minutes
- **AND** this includes 500ms rate limiting delay between tickers
- **AND** progress SHALL be visible throughout the operation

#### Scenario: Background alert generation performance
- **WHEN** a user adds 10 tickers via CSV upload
- **THEN** ticker insertion SHALL complete immediately (<1 second)
- **AND** background alert generation threads SHALL complete within 30 seconds
- **AND** the UI SHALL remain responsive during generation

### Requirement: Error Handling for Alert Operations
The system SHALL handle errors gracefully during alert generation and display.

#### Scenario: API failure during alert generation
- **WHEN** the system attempts to generate alerts for a ticker
- **AND** the API request fails after all retries
- **THEN** the system SHALL log the error with ticker symbol and error details
- **AND** the system SHALL not create any alert records for that ticker
- **AND** if in Refresh All, the system SHALL continue with remaining tickers

#### Scenario: Database error during alert update
- **WHEN** the system attempts to update alerts
- **AND** a database error occurs (e.g., connection lost)
- **THEN** the system SHALL rollback any partial changes
- **AND** the system SHALL display an error message to the user
- **AND** existing alerts SHALL remain unchanged

#### Scenario: Signal calculation error
- **WHEN** indicator calculation fails for a ticker (insufficient data, NaN errors)
- **THEN** the system SHALL catch the exception
- **AND** the system SHALL log the error with full context
- **AND** the system SHALL not create alerts for that ticker
- **AND** a user-friendly error message SHALL be shown in Refresh All summary

### Requirement: Alert Lifecycle Management
The system SHALL manage the complete lifecycle of alerts from creation through deletion.

#### Scenario: Alert created with metadata
- **WHEN** an alert is created for ticker "NVDA" with Long OPEN signal
- **THEN** the alert record SHALL include:
  - ticker_id (foreign key)
  - ticker_symbol "NVDA" (denormalized)
  - alert_type "Long - OPEN"
  - signal_date (date when signal occurred)
  - price (close price on signal_date)
  - created_at (current timestamp)

#### Scenario: Alert updated when signal changes
- **WHEN** a ticker's most recent signal changes from Long OPEN to Short OPEN
- **THEN** the old Long OPEN alert SHALL be deleted
- **AND** a new Short OPEN alert SHALL be created
- **AND** the created_at timestamp SHALL reflect the current time
- **AND** the signal_date SHALL reflect when the Short OPEN signal actually occurred

#### Scenario: Alert deleted when ticker deleted
- **WHEN** a user deletes ticker "GOOG" from the Dashboard
- **THEN** the ticker record SHALL be soft-deleted (is_active = 0)
- **AND** all alert records for "GOOG" SHALL be hard-deleted via CASCADE
- **AND** deleted alerts SHALL not appear in the Alerts tab

### Requirement: Alerts Tab UI Components
The system SHALL provide a complete UI for the Alerts tab with sorting, refresh, and display controls.

#### Scenario: Alerts tab header with controls
- **WHEN** the Alerts tab is rendered
- **THEN** the tab SHALL display a title "🔔 Trading Alerts"
- **AND** the tab SHALL show total alert count "Total Alerts: X"
- **AND** the tab SHALL provide a sort dropdown with options "Latest First" and "Oldest First"
- **AND** the tab SHALL provide a "🔄 Refresh All" button styled as primary (blue)

#### Scenario: Refresh All button confirmation
- **WHEN** a user clicks the "Refresh All" button
- **THEN** the system SHALL immediately begin the refresh operation (no confirmation dialog)
- **AND** a progress bar SHALL appear
- **AND** the Refresh All button SHALL be disabled during the operation

#### Scenario: Results summary after Refresh All
- **WHEN** Refresh All completes
- **THEN** the system SHALL display a success message showing count of successfully refreshed tickers
- **AND** if any errors occurred, the system SHALL display an error count
- **AND** an expandable "View Errors" section SHALL show which tickers failed and why

