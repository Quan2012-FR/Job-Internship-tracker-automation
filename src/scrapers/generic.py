from __future__ import annotations

import json
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from src.scrapers.base import ScrapedJob, extract_deadline_value

JOB_DETAIL_PATTERNS = (
    re.compile(r"/job/", re.IGNORECASE),
    re.compile(r"/jobs/r[0-9a-z-]+/", re.IGNORECASE),
    re.compile(r"jid-[0-9a-z-]+", re.IGNORECASE),
)

NON_JOB_TITLES = {
    "read more",
    "jobs",
    "career areas",
    "dealer jobs",
}

JOB_TITLE_TERMS = (
    "engineer",
    "intern",
    "internship",
    "technician",
    "manager",
    "analyst",
    "developer",
    "specialist",
    "assembler",
    "welder",
    "operator",
    "lead",
)


def can_handle(url: str) -> bool:
    return True


def fetch_jobs(company: str, careers_url: str, http_client, logger) -> list[ScrapedJob]:
    jobs: list[ScrapedJob] = []
    try:
        resp = http_client.get(careers_url)
        if resp.status_code >= 400:
            return jobs
        html = resp.text
        jobs.extend(_extract_json_ld_jobs(careers_url, html))
        if jobs:
            return _dedupe_jobs(jobs)
        jobs.extend(_extract_job_links(careers_url, html))
    except Exception as exc:
        logger.warning("Generic scraper failed for %s (%s): %s", company, careers_url, exc)
    return _dedupe_jobs(jobs)


def _extract_json_ld_jobs(careers_url: str, html: str) -> list[ScrapedJob]:
    soup = BeautifulSoup(html, "html.parser")
    jobs: list[ScrapedJob] = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        content = (script.string or "").strip()
        if not content:
            continue
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            continue

        data_items = data if isinstance(data, list) else [data]
        for item in data_items:
            if not isinstance(item, dict):
                continue
            if item.get("@type") != "JobPosting":
                continue
            title = str(item.get("title") or "").strip()
            location = ""
            job_loc = item.get("jobLocation")
            if isinstance(job_loc, dict):
                addr = job_loc.get("address", {})
                if isinstance(addr, dict):
                    location = str(addr.get("addressLocality") or addr.get("addressRegion") or "").strip()
            emp_type = str(item.get("employmentType") or "").strip()
            url = str(item.get("url") or careers_url).strip()
            desc = str(item.get("description") or "").strip()
            deadline = extract_deadline_value(item)
            if title and url:
                jobs.append(
                    ScrapedJob(
                        title=title,
                        location=location,
                        employment_type=emp_type,
                        url=urljoin(careers_url, url),
                        description=desc,
                        application_deadline=deadline,
                    )
                )
    return jobs


def _extract_job_links(careers_url: str, html: str) -> list[ScrapedJob]:
    soup = BeautifulSoup(html, "html.parser")
    jobs: list[ScrapedJob] = []
    seen_urls: set[str] = set()

    for anchor in soup.find_all("a", href=True):
        href = str(anchor.get("href") or "").strip()
        title = " ".join(anchor.get_text(" ", strip=True).split())
        if not href or not title:
            continue

        absolute_url = urljoin(careers_url, href)
        if absolute_url.lower() in seen_urls:
            continue
        if not _looks_like_job_link(absolute_url, title):
            continue

        seen_urls.add(absolute_url.lower())
        jobs.append(
            ScrapedJob(
                title=title,
                location="",
                employment_type="",
                url=absolute_url,
            )
        )
    return jobs


def _looks_like_job_link(url: str, title: str) -> bool:
    normalized_title = title.strip().lower()
    if not normalized_title or normalized_title in NON_JOB_TITLES:
        return False
    if len(title) > 180:
        return False

    parsed = urlparse(url)
    path = parsed.path or ""
    if any(pattern.search(path) for pattern in JOB_DETAIL_PATTERNS):
        return normalized_title != "read more"

    return any(term in normalized_title for term in JOB_TITLE_TERMS) and "/jobs/" in path.lower()


def _dedupe_jobs(jobs: list[ScrapedJob]) -> list[ScrapedJob]:
    deduped: dict[str, ScrapedJob] = {}
    for job in jobs:
        key = job.url.lower()
        existing = deduped.get(key)
        if existing is None:
            deduped[key] = job
            continue
        if existing.title.lower() == "read more" and job.title.lower() != "read more":
            deduped[key] = job
    return list(deduped.values())
