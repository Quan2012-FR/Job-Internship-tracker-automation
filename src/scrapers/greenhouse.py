from __future__ import annotations

from urllib.parse import urlparse

from src.scrapers.base import ScrapedJob, extract_deadline_value


def _extract_board_token(careers_url: str) -> str:
    parsed = urlparse(careers_url)
    parts = [p for p in parsed.path.split("/") if p]
    if not parts:
        return ""
    # Expected: /company/<token> or /<token>
    if len(parts) >= 2 and parts[0].lower() == "company":
        return parts[1]
    return parts[-1]


def can_handle(url: str) -> bool:
    u = url.lower()
    return "greenhouse" in u


def fetch_jobs(company: str, careers_url: str, http_client, logger) -> list[ScrapedJob]:
    token = _extract_board_token(careers_url)
    if not token:
        return []

    endpoint = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
    try:
        resp = http_client.get(endpoint)
        if resp.status_code >= 400:
            return []
        payload = resp.json()
    except Exception as exc:
        logger.warning("Greenhouse request failed for %s: %s", company, exc)
        return []

    jobs: list[ScrapedJob] = []
    for item in payload.get("jobs", []):
        title = str(item.get("title") or "").strip()
        absolute_url = str(item.get("absolute_url") or "").strip()
        location = str((item.get("location") or {}).get("name") or "").strip()
        deadline = extract_deadline_value(item)
        if not title or not absolute_url:
            continue
        jobs.append(
            ScrapedJob(
                title=title,
                location=location,
                employment_type="",
                url=absolute_url,
                application_deadline=deadline,
            )
        )
    return jobs
