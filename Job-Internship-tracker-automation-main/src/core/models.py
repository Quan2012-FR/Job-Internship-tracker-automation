from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class CompanyTarget:
    company: str
    careers_url: str
    source_sheet: str
    source_row: int
    metadata: dict[str, str]


@dataclass(slots=True)
class JobPosting:
    job_id: str
    company: str
    title: str
    location: str
    employment_type: str
    url: str
    first_seen: datetime
    last_seen: datetime
    active: bool = True
    application_deadline: str = ""
    days_remaining: int | None = None
    priority_score: int = 0


@dataclass(slots=True)
class RunStats:
    companies_checked: int = 0
    jobs_found_this_run: int = 0
    new_jobs_this_run: int = 0
    jobs_marked_inactive: int = 0
    total_active_jobs: int = 0
    last_scan_date: str = ""
    errors_encountered: int = 0
