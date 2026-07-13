# Engineering Job and Internship Tracker

A local Python tool that finds engineering internships and full-time jobs from company career pages, stores them in a database, and creates an organized Excel dashboard.

Everything runs on your computer. No paid APIs or cloud services are required.

## What This Project Does

The tracker:

1. Reads a list of companies from an Excel workbook.
2. Visits each company’s career page.
3. Searches for engineering-related jobs and internships.
4. Saves the results in a SQLite database.
5. Creates a separate Excel dashboard for reviewing and tracking applications.

Your original company workbook is treated as **read-only input** and is never changed.

The tracker does not automatically apply for jobs or submit forms.

---

# Quick Start

## 1. Install Python

Install Python 3.10 or newer.

During installation on Windows, make sure **Add Python to PATH** is selected.

You can check your Python version by running:

```powershell
python --version
```

On macOS or Linux, you may need to use:

```bash
python3 --version
```

## 2. Open the Project Folder

Open PowerShell, Command Prompt, Terminal, or the VS Code terminal inside the project folder.

For example, the folder should contain:

```text
update_jobs.py
config.py
requirements.txt
src
```

## 3. Create a Virtual Environment

A virtual environment keeps this project’s Python packages separate from your other projects.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

After activation, your terminal should show something similar to:

```text
(.venv) PS C:\Your\Project\Folder>
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 4. Install the Required Packages

Run:

```bash
pip install -r requirements.txt
```

Then install the Chromium browser used by the optional Playwright fallback:

```bash
python -m playwright install chromium
```

## 5. Prepare Your Company Workbook

Create an Excel workbook containing at least a company-name column.

A basic workbook might look like this:

| Company     | Careers URL                                 |
| ----------- | ------------------------------------------- |
| Caterpillar | https://www.caterpillar.com/en/careers.html |
| Rolls-Royce | https://careers.rolls-royce.com             |
| Eaton       |                                             |
| Cummins     |                                             |

The careers URL is optional. When it is missing, the tracker can attempt to find the company’s career page.

Common supported column names include:

* `Company`
* `Employer`
* `Careers URL`
* `Apply where`
* `Job URL`

A sample workbook is included at:

```text
sample_data/example_company_list.xlsx
```

## 6. Run the Tracker

Use the `--input` option followed by the path to your company workbook.

Example:

```bash
python update_jobs.py --input companies.xlsx
```

Using the included sample workbook:

```bash
python update_jobs.py --input sample_data/example_company_list.xlsx
```

If the path contains spaces, place quotation marks around the entire path:

```powershell
python update_jobs.py --input "C:\Projects\Job Tracker\companies.xlsx"
```

Do not add the workbook path directly inside `update_jobs.py`. Pass it through the terminal using `--input`.

## 7. Open the Dashboard

After the program finishes, open:

```text
engineering_job_dashboard.xlsx
```

The dashboard contains the jobs found during the scan and allows you to track application statuses and notes.

---

# Features

* Reads company names and career-page URLs from an Excel workbook.
* Never modifies the original input workbook.
* Supports rows containing only a company name.
* Attempts to discover missing career-page URLs.
* Caches discovered URLs in SQLite for future runs.
* Supports Workday, Greenhouse, Lever, iCIMS, and Taleo.
* Uses structured job endpoints when available.
* Falls back to JSON-LD extraction for other career pages.
* Can optionally use Playwright for JavaScript-heavy websites.
* Filters results using configurable broad and role-specific keyword categories.
* Stores job history and prevents duplicate entries.
* Tracks whether jobs are active or inactive.
* Scores jobs based on urgency, recency, engineering relevance, employment type, company preference, and location preference.
* Creates an organized Excel dashboard.
* Preserves application statuses and notes between dashboard refreshes.
* Supports custom input, output, and database locations.
* Runs locally without paid APIs.
* Does not submit applications or interact with Simplify accounts.

---

# Basic Commands

## Use the Default Output Files

```bash
python update_jobs.py --input companies.xlsx
```

This normally creates:

```text
engineering_job_dashboard.xlsx
jobs.db
```

## Choose Your Own Output and Database Names

```bash
python update_jobs.py --input companies.xlsx --output my_dashboard.xlsx --database my_jobs.db
```

## Process Only a Limited Number of Companies

This is useful when testing the program:

```bash
python update_jobs.py --input companies.xlsx --max-companies 10
```

## Enable the Browser Fallback

Some company websites load jobs using JavaScript. Playwright can open these pages in a browser when normal scraping finds no jobs.

```bash
python update_jobs.py --input companies.xlsx --playwright-fallback
```

To see the browser while it runs:

```bash
python update_jobs.py --input companies.xlsx --playwright-fallback --show-browser
```

## Use Custom Workbook Headers

Suppose your workbook uses:

* Worksheet: `Tabelle1`
* Company column: `Company`
* URL column: `Apply where`

Run:

```bash
python update_jobs.py --input companies.xlsx --sheet Tabelle1 --company-column Company --url-column "Apply where"
```

---

# Command-Line Options

| Option                       | Purpose                                                         |
| ---------------------------- | --------------------------------------------------------------- |
| `--input`                    | Path to the source Excel workbook. This option is required.     |
| `--output`                   | Path for the generated dashboard workbook.                      |
| `--database`                 | Path for the SQLite database.                                   |
| `--sheet`                    | Name of the worksheet to read.                                  |
| `--company-column`           | Exact header used for company names.                            |
| `--url-column`               | Exact header used for career-page URLs.                         |
| `--max-companies`            | Limits how many companies are processed.                        |
| `--categories`               | Comma-separated keyword categories to search.                   |
| `--keywords`                 | Comma-separated custom keywords added to the selected categories. |
| `--no-discovery`             | Requires workbook URLs and disables career-page discovery.      |
| `--no-search-fallback`       | Disables the search-engine discovery fallback.                  |
| `--cache-ttl-days`           | Number of days a successful cached career URL remains trusted.  |
| `--revalidate-after-days`    | Number of days before a cached URL is checked again.            |
| `--max-discovery-candidates` | Maximum number of possible career URLs tested for each company. |
| `--playwright-fallback`      | Uses a browser when normal scraping finds no jobs.              |
| `--show-browser`             | Displays the browser window during Playwright processing.       |

To see the command-line help screen, run:

```bash
python update_jobs.py --help
```

---

# Source Workbook Requirements

The source workbook is used only as input and is never modified.

## Required Information

The workbook must contain:

* A company-name column

## Optional Information

The workbook may also contain:

* A career-page URL column

If the URL is missing, the tracker can attempt to discover the company’s career page.

## Example Workbook

| Company      | Apply where                     |
| ------------ | ------------------------------- |
| Boeing       | https://jobs.boeing.com         |
| GE Aerospace | https://careers.geaerospace.com |
| RTX          |                                 |
| John Deere   |                                 |

The program can automatically recognize several common header names. You can also specify the exact headers using `--company-column` and `--url-column`.

Workbook mappings can also be configured in `config.py` using `WorkbookMapping`.

---

# Career-Page Discovery

When a company does not have a career-page URL in the workbook, the tracker can attempt to find one.

The discovery process may:

1. Generate likely career-page URLs.
2. Test those URLs.
3. Use a search fallback when necessary.
4. Save successful results in SQLite.

Discovery can be disabled with:

```bash
python update_jobs.py --input companies.xlsx --no-discovery
```

The search fallback can be disabled separately with:

```bash
python update_jobs.py --input companies.xlsx --no-search-fallback
```

Career-page discovery is best effort. Some companies may still require a correct URL to be entered manually.

---

# Career URL Cache

The SQLite database contains a `career_url_cache` table.

It stores:

* Company name
* Career-page URL
* Detected platform
* Date last validated
* Date last successful
* URL source

Successful URLs are reused during future scans until the configured cache period expires.

Older cached URLs are checked again before the program attempts a new discovery.

---

# Dashboard Sheets

The generated Excel dashboard contains the following worksheets.

## 1. THIS WEEK

Shows active jobs that:

* Were first discovered within the last seven days
* Have not been marked `Applied`

Columns:

* Company
* Position Title
* Location
* Days Remaining
* Priority Score
* Job URL
* Application Status

Jobs are sorted by highest Priority Score first.

## 2. READY TO APPLY

Shows active jobs that:

* Meet the configured Priority Score threshold
* Have not been marked `Applied`

Columns:

* Company
* Position Title
* Location
* Employment Type
* Date Found
* Application Deadline
* Days Remaining
* Priority Score
* Job URL
* Application Status
* Notes

Jobs are sorted by the nearest deadline and then by Priority Score.

## 3. NEEDS REVIEW

Shows jobs first discovered within the last seven days.

Columns:

* Date Found
* Company
* Position Title
* Location
* Employment Type
* Job URL
* Application Status
* Notes

New jobs begin with the status:

```text
Not Started
```

## 4. NEW JOBS

Shows jobs when they enter the database for the first time.

It includes the same tracking columns as the `NEEDS REVIEW` sheet.

## 5. ALL ACTIVE JOBS

Shows every job currently considered active.

Columns:

* Company
* Position Title
* Location
* Employment Type
* Date First Seen
* Last Seen
* Application Deadline
* Days Remaining
* Priority Score
* Job URL
* Application Status

## 6. STATISTICS

Displays a summary of the most recent scan.

Example:

| Metric              | Value               |
| ------------------- | ------------------- |
| Companies Checked   | 42                  |
| Jobs Found This Run | 126                 |
| New Jobs This Run   | 18                  |
| Total Active Jobs   | 201                 |
| Last Scan Date      | 2026-07-09T18:20:00 |
| Priority Threshold  | Configured value    |

---

# Application Tracking

Job URLs are clickable inside Excel.

The following application statuses are supported:

* Not Started
* Application Opened
* Applied
* Interviewing
* Rejected
* Offer
* Withdrawn

You can also enter notes in the dashboard.

Before creating a refreshed dashboard, the tracker reads your existing statuses and notes and saves them to the database. This prevents your updates from being erased during the next scan.

Do not delete or rename important tracking columns unless you also update the program.

---

# Deadline Colors

When an application deadline is available, the dashboard color-codes the `Days Remaining` value:

* Red: 0–7 days remaining
* Yellow: 8–14 days remaining
* Green: 15 or more days remaining

When no deadline is available, the dashboard displays:

```text
Unknown
```

---

# Simplify Workflow

This tracker can be used beside the Simplify browser extension, but it does not control Simplify.

A typical workflow is:

1. Run the tracker.

```bash
python update_jobs.py --input companies.xlsx
```

2. Open `engineering_job_dashboard.xlsx`.
3. Review the `THIS WEEK` sheet.
4. Review the `READY TO APPLY` sheet.
5. Click a job URL.
6. Complete the application manually in your browser.
7. Return to the dashboard.
8. Update the job’s Application Status.
9. Add notes when needed.
10. Run the tracker again later to refresh the job listings.

The tracker handles discovery, prioritization, history, and organization. It never submits an application.

---

# Priority Scoring

Job scoring can be adjusted in `config.py`.

Available settings include:

* `PRIORITY_THRESHOLD`
* `PREFERRED_COMPANIES`
* `PREFERRED_LOCATIONS`
* `INTERNSHIP_WEIGHT`
* `FULLTIME_WEIGHT`
* `DEADLINE_WEIGHT`
* `RECENCY_WEIGHT`
* `KEYWORD_MATCH_WEIGHT`
* `ENGINEERING_MATCH_WEIGHT`
* `COMPANY_PREFERENCE_WEIGHT`
* `LOCATION_PREFERENCE_WEIGHT`

Higher weights give that category more influence over the final Priority Score.

For example, increasing `LOCATION_PREFERENCE_WEIGHT` makes jobs in preferred locations receive a larger score increase.

Beginners can leave the default values unchanged.

---

# Job Keyword Filtering

The tracker uses centralized keyword rules to decide whether a position matches your search focus.

By default, it searches the `engineering` category. You can change the active categories in `config.py` or pass them from the command line.

Broad categories include:

* `engineering`
* `medical`
* `business`

Role-specific categories include:

* `chemical_engineer`
* `manufacturing_engineer`
* `rn`
* `construction_laborer`

Category names can be written with underscores, hyphens, or spaces. For example, `manufacturing_engineer`, `manufacturing-engineer`, and `manufacturing engineer` are treated the same.

Examples:

```bash
python update_jobs.py --input companies.xlsx --categories engineering,manufacturing_engineer
```

```bash
python update_jobs.py --input companies.xlsx --categories medical,rn --keywords phlebotomy,telehealth
```

```bash
python update_jobs.py --input companies.xlsx --categories business --keywords "product manager,customer success"
```

In `config.py`, edit:

```python
ACTIVE_KEYWORD_CATEGORIES = ["engineering"]
CUSTOM_KEYWORDS = []
```

To add or change built-in categories, edit `DEFAULT_KEYWORD_CATEGORIES`.

Review the keyword settings if relevant jobs are being excluded or unrelated jobs are being included.

---

# Supported Career Platforms

The project includes platform-specific support for:

* Workday
* Greenhouse
* Lever
* iCIMS
* Taleo

It also supports:

* Generic JSON-LD job extraction
* Rendered-page fallback using Playwright

Not every career website behaves the same way. Some companies may block automated requests, require authentication, or use unsupported website structures.

---

# Database

The project uses SQLite, which stores information in a local `.db` file.

The default database is:

```text
jobs.db
```

You do not need to install a separate database program.

## Stored Job Information

The database stores:

* `job_id`
* `company`
* `title`
* `location`
* `employment_type`
* `url`
* `first_seen`
* `last_seen`
* `active`
* `application_deadline`
* `days_remaining`
* `priority_score`
* `application_status`
* `notes`

## Database Behavior

* New jobs are inserted.
* Existing jobs have their latest information updated.
* Application statuses and notes are preserved.
* Jobs not found during the current scan may be marked inactive.
* Inactive jobs remain in the database as historical records.
* Existing databases are migrated using additive columns when the schema changes.

The database should normally be kept between runs. Deleting it removes the tracker’s stored job history.

---

# Logging

Each run creates or updates a daily log file inside the `logs` folder.

Example:

```text
logs/run_20260709.log
```

The log can include:

* Start time
* End time
* Companies checked
* Jobs found
* New jobs
* Jobs marked inactive
* Errors
* Failed URLs

Check the log file when a company fails or returns no jobs.

---

# Project Structure

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

## Important Files

### `update_jobs.py`

The main file used to run the tracker.

```bash
python update_jobs.py --input companies.xlsx
```

### `config.py`

Contains settings for job filtering categories, custom keywords, workbook mapping, and Priority Score weights.

### `requirements.txt`

Lists the Python packages required by the project.

### `jobs.db`

Stores job history, application statuses, notes, and cached career-page URLs.

### `engineering_job_dashboard.xlsx`

The generated Excel dashboard.

---

# Adding Another Scraper

This section is intended for developers who want to support an additional career platform.

## 1. Create the Scraper File

Add a new file inside:

```text
src/scrapers
```

Example:

```text
src/scrapers/myplatform.py
```

## 2. Implement the Required Methods

The scraper should implement:

```python
can_handle(url: str) -> bool
```

and:

```python
fetch_jobs(
    company,
    careers_url,
    http_client,
    logger
) -> list[ScrapedJob]
```

## 3. Register the Scraper

Add the scraper to:

```text
src/scrapers/registry.py
```

---

# Troubleshooting

## Error: Required Argument `--input` Is Missing

Example error:

```text
update_jobs.py: error: the following arguments are required: --input
```

Run the program with the workbook path:

```bash
python update_jobs.py --input companies.xlsx
```

## Error: Unrecognized Arguments

This commonly happens when a Windows path contains spaces and is not surrounded by quotation marks.

Incorrect:

```powershell
python update_jobs.py --input C:\Projects\Job Tracker\companies.xlsx
```

Correct:

```powershell
python update_jobs.py --input "C:\Projects\Job Tracker\companies.xlsx"
```

## The Workbook Cannot Be Found

Confirm that:

* The filename is correct.
* The file extension is included.
* The path is surrounded by quotation marks when it contains spaces.
* The workbook is located at the path you entered.

You can also use the full path:

```powershell
python update_jobs.py --input "C:\Users\YourName\Documents\companies.xlsx"
```

## No Jobs Were Found

Check the following:

* Make sure the career-page URLs are valid.
* Open the URLs manually in your browser.
* Check your internet connection.
* Review the keyword categories and custom keyword list in `config.py`.
* Enable Playwright fallback.
* Review the daily log file.
* Confirm the website does not require a login.
* Confirm the website is not blocking automated requests.

Try:

```bash
python update_jobs.py --input companies.xlsx --playwright-fallback
```

## Some Companies Failed

It is normal for some career websites to fail because company pages use different systems and security settings.

Review:

```text
logs/run_YYYYMMDD.log
```

For failed companies, try:

* Updating the career-page URL in the source workbook.
* Using the company’s main job-search page instead of its general careers page.
* Enabling Playwright fallback.
* Running a smaller test with `--max-companies`.

Example:

```bash
python update_jobs.py --input companies.xlsx --max-companies 5 --playwright-fallback
```

## Missing Workbook Columns

Make sure the workbook contains a company-name column.

When the headers are unusual, specify them manually:

```bash
python update_jobs.py --input companies.xlsx --company-column Employer --url-column "Job Link"
```

## Import Errors

Reactivate the virtual environment.

### Windows

```powershell
.\.venv\Scripts\Activate.ps1
```

### macOS or Linux

```bash
source .venv/bin/activate
```

Then reinstall the packages:

```bash
pip install -r requirements.txt
```

## PowerShell Blocks Virtual Environment Activation

PowerShell may display an execution-policy error.

You can allow locally created scripts for your user account by running:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate the environment again:

```powershell
.\.venv\Scripts\Activate.ps1
```

Only change PowerShell execution policies when you understand and accept the security implications.

## Playwright Browser Is Missing

Run:

```bash
python -m playwright install chromium
```

## Dashboard Is Open During a Refresh

Excel may prevent the program from replacing the dashboard while the workbook is open.

Close the dashboard workbook and run the command again.

---

# Recommended First Test

Before processing a large workbook, test the program using a small number of companies:

```bash
python update_jobs.py --input sample_data/example_company_list.xlsx --max-companies 5
```

After confirming that the dashboard is created correctly, run the complete workbook:

```bash
python update_jobs.py --input companies.xlsx
```

For JavaScript-heavy pages:

```bash
python update_jobs.py --input companies.xlsx --playwright-fallback
```

---

# What This Project Does Not Do

This project does not:

* Submit job applications
* Fill out application forms
* Log in to company accounts
* Control the Simplify browser extension
* Send emails
* Modify the source workbook
* Require paid APIs
* Require cloud hosting

All processing runs locally on your computer.

---

# License

See the `LICENSE` file for the project’s license terms.
