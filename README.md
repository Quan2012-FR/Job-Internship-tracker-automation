# Engineering Job Tracker

Local, reusable Python automation for tracking engineering internships and jobs from company career pages.

This project treats your source workbook as read-only input and generates a separate dashboard workbook plus a SQLite history database.

## Features

- Reads company and careers URLs from an Excel workbook in read-only mode.
- Supports company-name-only rows with best-effort careers URL discovery and SQLite caching.
- Supports platform scrapers for Workday, Greenhouse, Lever, iCIMS, and Taleo.
- Uses structured endpoints when available, with fallback JSON-LD extraction.
- Optional Playwright fallback can render JavaScript-heavy career pages when static scraping finds no jobs.
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
python -m playwright install chromium
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
python -m playwright install chromium
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

Custom workbook mapping:

```bash
python update_jobs.py --input companies.xlsx --sheet Tabelle1 --company-column Company --url-column "Apply where"
```

Company-name-only discovery and JavaScript fallback controls:

```bash
python update_jobs.py --input companies.xlsx --playwright-fallback --max-companies 25
```

Useful flags:

- `--sheet`: worksheet name to read.
- `--company-column`: exact header for the company name column.
- `--url-column`: exact header for the optional careers URL column.
- `--max-companies`: limit the number of companies processed in a run.
- `--no-discovery`: require workbook URLs and skip careers URL discovery.
- `--no-search-fallback`: skip search-engine based discovery fallback.
- `--cache-ttl-days`: days to trust a successful cached careers URL.
- `--revalidate-after-days`: days before revalidating a cached URL when used.
- `--max-discovery-candidates`: maximum generated candidate URLs to probe per company.
- `--playwright-fallback`: render pages with Playwright if static scraping finds no jobs.
- `--show-browser`: show the browser window when Playwright fallback is enabled.

## Source Workbook Expectations

The source workbook is read-only input and is never modified.

Expected fields:

- Company name column (for example: Company, Employer)
- Optional careers URL column (for example: Apply where, Careers URL, Job URL)

The extractor auto-detects common header names and can be customized with CLI flags or in config.py using WorkbookMapping. If a careers URL is blank or the URL column is missing, the tool can attempt local best-effort discovery from generated candidate URLs and a search fallback.

## Careers URL Cache

SQLite stores discovered and workbook-provided careers URLs in `career_url_cache`:

- company
- careers_url
- platform
- last_validated
- last_success
- source

Successful cached URLs are reused across runs until the configured TTL expires. Stale cached URLs are revalidated before fresh discovery is attempted.

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
- Generic JSON-LD and rendered-page fallback

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
