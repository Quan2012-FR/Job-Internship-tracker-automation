from __future__ import annotations

from urllib.parse import urlparse

from src.scrapers.base import ScrapedJob, extract_deadline_value


def _extract_site(careers_url: str) -> str:
    parsed = urlparse(careers_url)
    parts = [p for p in parsed.path.split("/") if p]
    if not parts:
        return ""
    # Common lever forms: /company or /company/jobs
    return parts[0]


def can_handle(url: str) -> bool:
    u = url.lower()
    return "lever.co" in u


def fetch_jobs(company: str, careers_url: str, http_client, logger) -> list[ScrapedJob]:
    site = _extract_site(careers_url)
    if not site:
        return []

    endpoint = f"https://api.lever.co/v0/postings/{site}?mode=json"
    try:
        resp = http_client.get(endpoint)
        if resp.status_code >= 400:
            return []
        payload = resp.json()
    except Exception as exc:
        logger.warning("Lever request failed for %s: %s", company, exc)
        return []

    jobs: list[ScrapedJob] = []
    for item in payload:
        title = str(item.get("text") or "").strip()
        url = str(item.get("hostedUrl") or "").strip()
        categories = item.get("categories") or {}
        location = str(categories.get("location") or "").strip()
        team = str(categories.get("team") or "").strip()
        deadline = extract_deadline_value(item)
        if not title or not url:
            continue
        jobs.append(ScrapedJob(title=title, location=location, employment_type=team, url=url, application_deadline=deadline))
    return jobs
