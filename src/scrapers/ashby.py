from __future__ import annotations

import json
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from src.scrapers.base import ScrapedJob, extract_deadline_value


def can_handle(url: str) -> bool:
    return "jobs.ashbyhq.com" in url.lower()


def fetch_jobs(company: str, careers_url: str, http_client, logger) -> list[ScrapedJob]:
    try:
        resp = http_client.get(careers_url)
        if resp.status_code >= 400:
            return []
        payload = _extract_app_data(resp.text)
    except Exception as exc:
        logger.warning("Ashby request failed for %s: %s", company, exc)
        return []

    job_board = payload.get("jobBoard") or {}
    postings = job_board.get("jobPostings") or []
    board_base_url = _board_base_url(careers_url)

    jobs: list[ScrapedJob] = []
    for item in postings:
        if not isinstance(item, dict) or not item.get("isListed"):
            continue
        title = str(item.get("title") or "").strip()
        posting_id = str(item.get("id") or "").strip()
        if not title or not posting_id:
            continue

        location = str(item.get("locationExternalName") or item.get("locationName") or "").strip()
        employment_type = str(item.get("employmentType") or "").strip()
        deadline = extract_deadline_value(item)
        jobs.append(
            ScrapedJob(
                title=title,
                location=location,
                employment_type=employment_type,
                url=f"{board_base_url}/{posting_id}",
                application_deadline=deadline,
            )
        )
    return jobs


def _extract_app_data(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script"):
        content = script.string or script.get_text() or ""
        marker = "window.__appData = "
        marker_index = content.find(marker)
        if marker_index < 0:
            continue
        start = content.find("{", marker_index)
        end = content.find("};", start)
        if start < 0 or end < 0:
            continue
        return json.loads(content[start : end + 1])
    return {}


def _board_base_url(careers_url: str) -> str:
    parsed = urlparse(careers_url)
    path_parts = [part for part in parsed.path.split("/") if part]
    slug = path_parts[0] if path_parts else ""
    return f"{parsed.scheme}://{parsed.netloc}/{slug}".rstrip("/")
