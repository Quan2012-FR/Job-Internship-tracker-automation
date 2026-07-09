from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from src.core.models import JobPosting


def connect_db(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            company TEXT NOT NULL,
            title TEXT NOT NULL,
            location TEXT,
            employment_type TEXT,
            url TEXT NOT NULL,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_active ON jobs(active)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_last_seen ON jobs(last_seen)")
    conn.commit()


def upsert_jobs(
    conn: sqlite3.Connection,
    jobs: list[JobPosting],
    scan_time: datetime,
) -> tuple[int, set[str]]:
    new_count = 0
    seen_ids: set[str] = set()

    for job in jobs:
        seen_ids.add(job.job_id)
        existing = conn.execute("SELECT job_id FROM jobs WHERE job_id = ?", (job.job_id,)).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE jobs
                SET company = ?,
                    title = ?,
                    location = ?,
                    employment_type = ?,
                    url = ?,
                    last_seen = ?,
                    active = 1
                WHERE job_id = ?
                """,
                (
                    job.company,
                    job.title,
                    job.location,
                    job.employment_type,
                    job.url,
                    scan_time.isoformat(),
                    job.job_id,
                ),
            )
        else:
            new_count += 1
            conn.execute(
                """
                INSERT INTO jobs (job_id, company, title, location, employment_type, url, first_seen, last_seen, active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    job.job_id,
                    job.company,
                    job.title,
                    job.location,
                    job.employment_type,
                    job.url,
                    scan_time.isoformat(),
                    scan_time.isoformat(),
                ),
            )

    conn.commit()
    return new_count, seen_ids


def mark_inactive_missing(conn: sqlite3.Connection, seen_ids: set[str]) -> int:
    active_rows = conn.execute("SELECT job_id FROM jobs WHERE active = 1").fetchall()
    active_ids = {row["job_id"] for row in active_rows}
    to_deactivate = active_ids - seen_ids
    if not to_deactivate:
        return 0

    conn.executemany("UPDATE jobs SET active = 0 WHERE job_id = ?", [(jid,) for jid in to_deactivate])
    conn.commit()
    return len(to_deactivate)


def get_total_active_jobs(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COUNT(*) AS c FROM jobs WHERE active = 1").fetchone()
    return int(row["c"] if row else 0)


def get_active_jobs(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT company, title, location, employment_type, first_seen, last_seen, url
        FROM jobs
        WHERE active = 1
        ORDER BY company, title
        """
    ).fetchall()


def get_new_jobs_all_time(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT first_seen AS date_found, company, title, location, employment_type, url
        FROM jobs
        ORDER BY first_seen DESC, company
        """
    ).fetchall()


def get_jobs_found_since(conn: sqlite3.Connection, since_dt: datetime) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT first_seen AS date_found, company, title, location, employment_type, url
        FROM jobs
        WHERE first_seen >= ?
        ORDER BY first_seen DESC, company
        """,
        (since_dt.isoformat(),),
    ).fetchall()
