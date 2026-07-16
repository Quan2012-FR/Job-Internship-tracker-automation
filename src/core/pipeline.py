from __future__ import annotations

from datetime import datetime

import requests

from config import AppConfig
from src.core import database as db
from src.core.dashboard import resolve_dashboard_output_path, write_dashboard
from src.core.discovery import resolve_careers_url
from src.core.extractor import extract_company_targets
from src.core.filtering import build_search_keywords, matches_job_keywords
from src.core.http_client import build_http_client
from src.core.logging_utils import setup_logging
from src.core.models import JobPosting, RunStats
from src.core.priority import parse_deadline, score_job
from src.core.utils import build_job_id, normalize_text
from src.scrapers.registry import fetch_jobs_for_company

REQUEST_EXCEPTIONS = requests.exceptions


def run_update(cfg: AppConfig) -> RunStats:
    logger = setup_logging(cfg.logs_dir)
    stats = RunStats()
    scan_start = datetime.now()
    cfg.output_workbook = resolve_dashboard_output_path(cfg.output_workbook, scan_start)

    logger.info("Run started")
    logger.info("Input workbook: %s", cfg.source_workbook)
    logger.info("Dashboard output: %s", cfg.output_workbook)
    logger.info("Database: %s", cfg.database_path)

    targets = extract_company_targets(str(cfg.source_workbook), cfg.workbook_mapping)
    if cfg.max_companies is not None:
        targets = targets[: cfg.max_companies]

    stats.companies_checked = len(targets)
    logger.info("Companies extracted: %d", len(targets))

    http_client = build_http_client(
        headers=cfg.default_headers,
        connect_timeout_seconds=cfg.connect_timeout_seconds,
        timeout_seconds=cfg.request_timeout_seconds,
        delay_seconds=cfg.request_delay_seconds,
    )

    all_jobs: list[JobPosting] = []
    search_keywords = build_search_keywords(
        cfg.active_keyword_categories,
        cfg.keyword_categories,
        cfg.custom_keywords,
        fallback_keywords=cfg.engineering_keywords,
    )
    conn = db.connect_db(cfg.database_path)
    db.init_db(conn)

    try:
        total_companies = len(targets)
        for index, target in enumerate(targets, start=1):
            logger.info("Processing company %d/%d: %s", index, total_companies, target.company)
            try:
                careers_url = resolve_careers_url(target, conn, http_client, logger, cfg.discovery)
                if not careers_url:
                    logger.warning("No careers URL resolved for %s at row %s", target.company, target.source_row)
                    continue

                scraped = fetch_jobs_for_company(
                    target.company,
                    careers_url,
                    http_client,
                    logger,
                    use_browser_fallback=cfg.use_playwright_fallback,
                    headless=cfg.headless_browser,
                    timeout_ms=cfg.browser_timeout_ms,
                )
                for s in scraped:
                    title = normalize_text(s.title)
                    if not title:
                        continue
                    if not matches_job_keywords(title=title, keywords=search_keywords, description=s.description):
                        continue

                    url = normalize_text(s.url)
                    if not url:
                        continue
                    location = normalize_text(s.location)
                    employment = normalize_text(s.employment_type)
                    job_id = build_job_id(target.company, title, location, url)
                    first_seen = db.get_job_first_seen(conn, job_id) or scan_start
                    deadline, days_remaining = parse_deadline(s.application_deadline, today=scan_start.date())
                    job = JobPosting(
                        job_id=job_id,
                        company=target.company,
                        title=title,
                        location=location,
                        employment_type=employment,
                        url=url,
                        first_seen=first_seen,
                        last_seen=scan_start,
                        active=True,
                        application_deadline=deadline,
                        days_remaining=days_remaining,
                    )
                    job.priority_score = score_job(job, s.description, search_keywords, cfg, now=scan_start)
                    all_jobs.append(job)
            except REQUEST_EXCEPTIONS.Timeout as exc:
                stats.errors_encountered += 1
                logger.warning(
                    "Timed out while processing company %s at row %s: %s",
                    target.company,
                    target.source_row,
                    exc,
                )
            except REQUEST_EXCEPTIONS.SSLError as exc:
                stats.errors_encountered += 1
                logger.warning(
                    "SSL failure while processing company %s at row %s: %s",
                    target.company,
                    target.source_row,
                    exc,
                )
            except REQUEST_EXCEPTIONS.TooManyRedirects as exc:
                stats.errors_encountered += 1
                logger.warning(
                    "Too many redirects while processing company %s at row %s: %s",
                    target.company,
                    target.source_row,
                    exc,
                )
            except REQUEST_EXCEPTIONS.ConnectionError as exc:
                stats.errors_encountered += 1
                if _is_timeout_like_error(exc):
                    logger.warning(
                        "Timed out while processing company %s at row %s: %s",
                        target.company,
                        target.source_row,
                        exc,
                    )
                else:
                    logger.warning(
                        "Connection failure while processing company %s at row %s: %s",
                        target.company,
                        target.source_row,
                        exc,
                    )
            except REQUEST_EXCEPTIONS.RequestException as exc:
                stats.errors_encountered += 1
                logger.warning(
                    "HTTP request failure while processing company %s at row %s: %s",
                    target.company,
                    target.source_row,
                    exc,
                )
            except Exception as exc:
                stats.errors_encountered += 1
                logger.exception(
                    "Failed processing company %s at row %s (%s): %s",
                    target.company,
                    target.source_row,
                    target.careers_url,
                    exc,
                )

        # Deduplicate within run by job_id.
        deduped: dict[str, JobPosting] = {job.job_id: job for job in all_jobs}
        jobs_this_run = list(deduped.values())
        stats.jobs_found_this_run = len(jobs_this_run)

        stats.new_jobs_this_run, seen_ids = db.upsert_jobs(conn, jobs_this_run, scan_start)
        stats.jobs_marked_inactive = db.mark_inactive_missing(conn, seen_ids)
        stats.total_active_jobs = db.get_total_active_jobs(conn)
        stats.last_scan_date = scan_start.isoformat(timespec="seconds")

        cfg.output_workbook = write_dashboard(conn, cfg.output_workbook, stats, cfg.priority_threshold)
    finally:
        conn.close()

    logger.info("Run finished")
    logger.info("End time: %s", datetime.now().isoformat(timespec="seconds"))
    logger.info("Companies checked: %d", stats.companies_checked)
    logger.info("Jobs found: %d", stats.jobs_found_this_run)
    logger.info("New jobs: %d", stats.new_jobs_this_run)
    logger.info("Jobs marked inactive: %d", stats.jobs_marked_inactive)
    logger.info("Errors encountered: %d", stats.errors_encountered)

    return stats


def _is_timeout_like_error(exc: Exception) -> bool:
    details = str(exc).lower()
    return "timed out" in details or "timeout" in details
