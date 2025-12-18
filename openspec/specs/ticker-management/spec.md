# ticker-management Specification

## Purpose
TBD - created by archiving change add-ticker-management-infrastructure. Update Purpose after archive.
## Requirements
### Requirement: Database Schema for Ticker Storage
The system SHALL provide a SQLite database with persistent storage for stock ticker symbols and related metadata.

#### Scenario: First-time database initialization
- **WHEN** the application starts for the first time
- **THEN** the system SHALL automatically create the database file with tickers and price_cache tables
- **AND** the tables SHALL include appropriate indexes for performance
- **AND** the database SHALL enforce UNIQUE constraint on ticker symbols

#### Scenario: Duplicate ticker prevention
- **WHEN** a user attempts to insert a ticker symbol that already exists
- **THEN** the system SHALL reject the insertion and return a duplicate error
- **AND** the existing ticker record SHALL remain unchanged

### Requirement: Comma-Separated Ticker Input
The system SHALL accept bulk ticker input as comma-separated strings through a text area interface.

#### Scenario: Valid comma-separated ticker input
- **WHEN** a user enters "AAPL, TSLA, MSFT, GOOGL" in the text area
- **THEN** the system SHALL parse and normalize each ticker (trim whitespace, convert to uppercase)
- **AND** the system SHALL validate each ticker format
- **AND** the system SHALL insert valid tickers into the database
- **AND** the system SHALL display a summary showing count of added, duplicated, and invalid tickers

#### Scenario: Mixed valid and invalid ticker input
- **WHEN** a user enters "AAPL, INVALID!!!, TSLA, , MSFT" in the text area
- **THEN** the system SHALL successfully add valid tickers (AAPL, TSLA, MSFT)
- **AND** the system SHALL reject invalid tickers (INVALID!!!, empty string)
- **AND** the system SHALL display error messages identifying which tickers were invalid and why

### Requirement: CSV File Ticker Upload
The system SHALL accept bulk ticker input via CSV file upload with automatic parsing and validation.

#### Scenario: CSV upload with header row
- **WHEN** a user uploads a CSV file with a "symbol" or "ticker" header column
- **THEN** the system SHALL parse the CSV using the first column after the header
- **AND** the system SHALL display a preview of the first 10 tickers before confirmation
- **AND** the system SHALL insert all valid tickers after user confirmation
- **AND** the system SHALL provide a summary of results

#### Scenario: CSV upload with encoding issues
- **WHEN** a user uploads a CSV file with non-UTF-8 encoding
- **THEN** the system SHALL attempt to parse with UTF-8 first
- **AND** if UTF-8 fails, the system SHALL fallback to latin-1 encoding
- **AND** if all encoding attempts fail, the system SHALL display a clear error message

#### Scenario: CSV upload size limit
- **WHEN** a user attempts to upload a CSV file larger than 5MB
- **THEN** the system SHALL reject the upload
- **AND** the system SHALL display an error message indicating the file size limit

### Requirement: Ticker Validation Rules
The system SHALL validate all ticker symbols against defined format rules before storage.

#### Scenario: Valid ticker format
- **WHEN** the system validates a ticker like "AAPL", "TSLA", "BRK.B"
- **THEN** the system SHALL accept the ticker as valid
- **AND** the system SHALL normalize it to uppercase
- **AND** the system SHALL proceed with database insertion

#### Scenario: Invalid ticker format - too long
- **WHEN** the system validates a ticker with more than 5 characters (excluding dots)
- **THEN** the system SHALL reject the ticker as invalid
- **AND** the system SHALL return an error message "Ticker symbol too long"

#### Scenario: Invalid ticker format - special characters
- **WHEN** the system validates a ticker containing special characters like "@", "#", "$"
- **THEN** the system SHALL reject the ticker as invalid
- **AND** the system SHALL return an error message "Ticker contains invalid characters"

#### Scenario: Invalid ticker format - empty string
- **WHEN** the system validates an empty or whitespace-only string
- **THEN** the system SHALL reject the ticker as invalid
- **AND** the system SHALL return an error message "Ticker cannot be empty"

### Requirement: User Dashboard Tab Interface
The system SHALL provide a Dashboard tab in the Streamlit interface for managing stored tickers with filtering, sorting, and deletion capabilities.

#### Scenario: Display all tickers in paginated table
- **WHEN** a user navigates to the Dashboard tab
- **THEN** the system SHALL display a table of all active tickers
- **AND** the table SHALL show columns: Symbol, Added Date, Last Updated, Actions
- **AND** the system SHALL display a total ticker count
- **AND** the system SHALL paginate results with 50 tickers per page

#### Scenario: No tickers available
- **WHEN** a user navigates to the Dashboard tab and no tickers exist
- **THEN** the system SHALL display a message "No tickers found. Please add tickers."
- **AND** the system SHALL show the ticker input interface

### Requirement: Ticker Filtering
The system SHALL allow users to filter tickers by symbol name and date range.

#### Scenario: Search tickers by partial symbol match
- **WHEN** a user enters "APP" in the search box
- **THEN** the system SHALL display all tickers containing "APP" (case-insensitive)
- **AND** results MAY include "AAPL", "SNAPPLE", etc.
- **AND** the system SHALL update the display immediately

#### Scenario: Filter tickers by date range
- **WHEN** a user selects a date range (e.g., added between 2025-01-01 and 2025-06-01)
- **THEN** the system SHALL display only tickers added within that date range
- **AND** the system SHALL update the total count accordingly

### Requirement: Ticker Sorting
The system SHALL allow users to sort tickers by symbol or date in ascending/descending order.

#### Scenario: Sort tickers alphabetically A-Z
- **WHEN** a user selects "Symbol (A-Z)" from the sort dropdown
- **THEN** the system SHALL display tickers sorted alphabetically by symbol ascending
- **AND** the system SHALL maintain the current page position

#### Scenario: Sort tickers by newest first
- **WHEN** a user selects "Added Date (Newest First)" from the sort dropdown
- **THEN** the system SHALL display tickers sorted by added_date descending
- **AND** the most recently added ticker SHALL appear first

### Requirement: Individual Ticker Deletion
The system SHALL allow users to delete individual tickers with confirmation.

#### Scenario: Delete single ticker with confirmation
- **WHEN** a user clicks the delete button for a specific ticker
- **THEN** the system SHALL display a confirmation warning
- **AND** if user confirms, the system SHALL soft delete the ticker (set is_active=0)
- **AND** the system SHALL display a success message
- **AND** the ticker SHALL no longer appear in the active ticker list

#### Scenario: Cancel ticker deletion
- **WHEN** a user clicks the delete button but cancels the confirmation
- **THEN** the system SHALL not delete the ticker
- **AND** the ticker SHALL remain in the list unchanged

### Requirement: Bulk Ticker Deletion
The system SHALL allow users to select multiple tickers and delete them simultaneously.

#### Scenario: Bulk delete multiple tickers
- **WHEN** a user selects 3 tickers using the multi-select interface
- **AND** clicks the "Delete Selected" button
- **THEN** the system SHALL display a confirmation warning showing count of selected tickers
- **AND** if user confirms, the system SHALL soft delete all selected tickers
- **AND** the system SHALL display a success message with count deleted
- **AND** none of the deleted tickers SHALL appear in the active ticker list

### Requirement: Pagination Controls
The system SHALL provide pagination controls for navigating through large ticker lists.

#### Scenario: Navigate to next page
- **WHEN** a user is on page 1 with 50 tickers displayed
- **AND** there are more than 50 tickers total
- **AND** the user clicks the "Next" button
- **THEN** the system SHALL display page 2 with the next 50 tickers
- **AND** the page indicator SHALL show "Page 2 of X"

#### Scenario: Navigate to previous page
- **WHEN** a user is on page 3
- **AND** clicks the "Previous" button
- **THEN** the system SHALL display page 2
- **AND** the pagination state SHALL persist in session state

#### Scenario: First and last page boundary conditions
- **WHEN** a user is on page 1
- **THEN** the "Previous" button SHALL be disabled or hidden
- **WHEN** a user is on the last page
- **THEN** the "Next" button SHALL be disabled or hidden

### Requirement: Application Tab Navigation
The system SHALL provide a tabbed interface with three sections: Chart Analysis, Alerts, and Dashboard.

#### Scenario: Navigate between tabs
- **WHEN** a user clicks on the "Dashboard" tab
- **THEN** the system SHALL display the dashboard interface
- **AND** session state SHALL persist ticker selections and filters
- **WHEN** the user switches to "Chart Analysis" tab
- **THEN** the system SHALL display placeholder content
- **AND** the system SHALL maintain the dashboard state in the background

### Requirement: Transaction Integrity
The system SHALL ensure all database operations are atomic with automatic rollback on errors.

#### Scenario: Bulk insert with mid-operation error
- **WHEN** a user attempts to insert 100 tickers
- **AND** an error occurs on the 50th insertion
- **THEN** the system SHALL rollback all 49 successful insertions
- **AND** the database SHALL remain in its pre-operation state
- **AND** the system SHALL display an error message with details

#### Scenario: Successful bulk operation commit
- **WHEN** a user successfully inserts 100 valid tickers
- **THEN** the system SHALL commit all insertions in a single transaction
- **AND** all 100 tickers SHALL be immediately queryable
- **AND** the system SHALL update the last_updated timestamp

### Requirement: Error Handling and User Feedback
The system SHALL provide clear, actionable error messages for all failure scenarios.

#### Scenario: Database connection failure
- **WHEN** the database file cannot be accessed or is corrupted
- **THEN** the system SHALL display a user-friendly error message
- **AND** the system SHALL log the detailed error to a log file
- **AND** the system SHALL provide guidance on potential fixes

#### Scenario: CSV parsing error
- **WHEN** a user uploads a malformed CSV file
- **THEN** the system SHALL display an error message indicating the specific parsing issue
- **AND** the system SHALL suggest correct CSV format
- **AND** the system SHALL not crash or display raw error traces

### Requirement: Performance Standards
The system SHALL meet defined performance benchmarks for common operations.

#### Scenario: Bulk insert performance
- **WHEN** a user inserts 100 tickers via CSV upload
- **THEN** the operation SHALL complete in less than 5 seconds
- **AND** the system SHALL display a progress indicator during processing

#### Scenario: Dashboard load performance
- **WHEN** the database contains 1000 tickers
- **AND** a user navigates to the Dashboard tab
- **THEN** the paginated view SHALL load in less than 1 second
- **AND** filtering operations SHALL update results in less than 500 milliseconds

#### Scenario: Search performance
- **WHEN** a user searches across 5000 tickers
- **THEN** the search results SHALL appear in less than 500 milliseconds
- **AND** the system SHALL use indexed queries for performance

