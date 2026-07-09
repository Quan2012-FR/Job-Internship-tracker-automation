from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from openpyxl import Workbook

from src.core import database as db
from src.core.models import RunStats


REVIEW_COLUMNS = [
    "Date Found",
    "Company",
    "Position Title",
    "Location",
    "Employment Type",
    "Job URL",
    "Status",
    "Notes",
]

ACTIVE_COLUMNS = [
    "Company",
    "Position Title",
    "Location",
    "Employment Type",
    "Date First Seen",
    "Last Seen",
    "Job URL",
]


def _fill_review_sheet(sheet, rows) -> None:
    sheet.append(REVIEW_COLUMNS)
    for row in rows:
        sheet.append(
            [
                row["date_found"],
                row["company"],
                row["title"],
                row["location"],
                row["employment_type"],
                row["url"],
                "Not Reviewed",
                "",
            ]
        )


def _fill_active_sheet(sheet, rows) -> None:
    sheet.append(ACTIVE_COLUMNS)
    for row in rows:
        sheet.append(
            [
                row["company"],
                row["title"],
                row["location"],
                row["employment_type"],
                row["first_seen"],
                row["last_seen"],
                row["url"],
            ]
        )


def write_dashboard(conn: sqlite3.Connection, output_path: Path, stats: RunStats) -> None:
    wb = Workbook()

    ws_review = wb.active
    ws_review.title = "NEEDS REVIEW"

    ws_new = wb.create_sheet("NEW JOBS")
    ws_active = wb.create_sheet("ALL ACTIVE JOBS")
    ws_stats = wb.create_sheet("STATISTICS")

    last_7_days = datetime.now() - timedelta(days=7)
    review_rows = db.get_jobs_found_since(conn, last_7_days)
    new_rows = db.get_new_jobs_all_time(conn)
    active_rows = db.get_active_jobs(conn)

    _fill_review_sheet(ws_review, review_rows)
    _fill_review_sheet(ws_new, new_rows)
    _fill_active_sheet(ws_active, active_rows)

    ws_stats.append(["Metric", "Value"])
    ws_stats.append(["Companies Checked", stats.companies_checked])
    ws_stats.append(["Jobs Found This Run", stats.jobs_found_this_run])
    ws_stats.append(["New Jobs This Run", stats.new_jobs_this_run])
    ws_stats.append(["Total Active Jobs", stats.total_active_jobs])
    ws_stats.append(["Last Scan Date", stats.last_scan_date])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_path)
