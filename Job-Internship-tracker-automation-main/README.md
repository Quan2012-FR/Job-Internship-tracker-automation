# Engineering Job Tracker

Local, reusable Python automation for tracking engineering internships and jobs from company career pages.

This project treats your source workbook as read-only input and generates a separate dashboard workbook plus a SQLite history database.

## Features

- Reads company and careers URLs from an Excel workbook in read-only mode.
- Supports platform scrapers for Workday, Greenhouse, Lever, iCIMS, and Taleo.
- Uses structured endpoints when available, with fallback JSON-LD extraction.
- Filters only engineering-related positions with centralized keyword rules.
- Stores job history in SQLite to avoid duplicates and track active/inactive state.
- Generates a separate dashboard workbook with weekly review and summary sheets.
- CLI supports custom input/output/database paths.
- No paid APIs. No cloud required. Runs locally.

## Project Structure

```text
engineering-job-tracker/
├── src/
│   ├── core/
│   │   ├── database.py
│   │   ├── dashboard.py
│   │   ├── extractor.py
│   │   ├── filtering.py
│   │   ├── http_client.py
│   │   ├── logging_utils.py
│   │   ├── models.py
│   │   ├── pipeline.py
│   │   └── utils.py
│   └── scrapers/
│       ├── base.py
│       ├── generic.py
│       ├── greenhouse.py
│       ├── icims.py
│       ├── lever.py
│       ├── registry.py
│       ├── taleo.py
│       └── workday.py
├── sample_data/
│   └── example_company_list.xlsx
├── logs/
├── update_jobs.py
├── config.py
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

## Installation

### Windows

1. Install Python 3.10+.
2. Open PowerShell in the project folder.
3. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

4. Install dependencies:

```powershell
pip install -r requirements.txt
```

### macOS / Linux

1. Install Python 3.10+.
2. Open Terminal in the project folder.
3. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run with required input workbook:

```bash
python update_jobs.py --input companies.xlsx
```

Optional output and database paths:

```bash
python update_jobs.py --input companies.xlsx --output engineering_job_dashboard.xlsx --database jobs.db
```

## Source Workbook Expectations

The source workbook is read-only input and is never modified.

Expected fields:

- Company name column (for example: Company, Employer)
- Careers URL column (for example: Apply where, Careers URL, Job URL)

The extractor auto-detects common header names and can be customized in config.py using WorkbookMapping.

## Dashboard Output

The generated dashboard workbook contains:

1. NEEDS REVIEW
- Jobs first discovered within the last 7 days
- Columns: Date Found, Company, Position Title, Location, Employment Type, Job URL, Status, Notes
- Default Status: Not Reviewed

2. NEW JOBS
- All jobs that entered the database for the first time
- Same columns and default status

3. ALL ACTIVE JOBS
- Currently active jobs
- Columns: Company, Position Title, Location, Employment Type, Date First Seen, Last Seen, Job URL

4. STATISTICS
- Companies Checked
- Jobs Found This Run
- New Jobs This Run
- Total Active Jobs
- Last Scan Date

## Database Schema

SQLite file (jobs.db by default) stores:

- job_id (primary key)
- company
- title
- location
- employment_type
- url
- first_seen
- last_seen
- active (1 or 0)

Behavior:

- New jobs are inserted.
- Existing jobs update last_seen and stay active.
- Previously known jobs not found in current run are marked inactive.
- Historical data is preserved.

## Supported Platforms

- Workday
- Greenhouse
- Lever
- iCIMS
- Taleo

Design is modular for adding more platforms.

## Logging

Each run creates a daily log file:

- logs/run_YYYYMMDD.log

Includes:

- Start and end time
- Companies checked
- Jobs found
- New jobs
- Jobs marked inactive
- Errors

## Adding a New Scraper Module

1. Add file in src/scrapers, for example myplatform.py.
2. Implement:
- can_handle(url: str) -> bool
- fetch_jobs(company, careers_url, http_client, logger) -> list[ScrapedJob]
3. Register in src/scrapers/registry.py.

## Output Example

Statistics sheet sample:

| Metric | Value |
|---|---|
| Companies Checked | 42 |
| Jobs Found This Run | 126 |
| New Jobs This Run | 18 |
| Total Active Jobs | 201 |
| Last Scan Date | 2026-07-09T18:20:00 |

## Troubleshooting

- No jobs found:
  - Verify careers URLs are valid and public.
  - Confirm network access is available.
  - Check engineering keyword list in config.py.
- Missing columns:
  - Ensure your workbook has a company and URL column.
  - Configure WorkbookMapping in config.py if headers are custom.
- Import errors:
  - Re-activate virtual environment and reinstall requirements.

## Notes

- This tool does not send emails.
- This tool does not apply for jobs.
- This tool does not modify the source workbook.
- All processing runs locally.
