from __future__ import annotations

from urllib.parse import urlparse

from src.scrapers.base import ScrapedJob, extract_deadline_value


def _workday_endpoint(careers_url: str) -> str:
    parsed = urlparse(careers_url)
    host = parsed.netloc
    parts = [p for p in parsed.path.split("/") if p]

    # Common format: /recruiting/{tenant}/{site}
    if len(parts) >= 3 and parts[0].lower() == "recruiting":
        tenant = parts[1]
        site = parts[2]
        return f"https://{host}/wday/cxs/{tenant}/{site}/jobs"

    # Alternate format for myworkdayjobs hosts: /{tenant}/{site}
    if len(parts) >= 2 and "myworkdayjobs" in host.lower():
        tenant = parts[0]
        site = parts[1]
        return f"https://{host}/wday/cxs/{tenant}/{site}/jobs"

    return ""


def can_handle(url: str) -> bool:
    u = url.lower()
    return "workday" in u or "myworkdayjobs" in u


def fetch_jobs(company: str, careers_url: str, http_client, logger) -> list[ScrapedJob]:
    endpoint = _workday_endpoint(careers_url)
    if not endpoint:
        return []

    try:
        resp = http_client.get(endpoint)
        if resp.status_code >= 400:
            return []
        payload = resp.json()
    except Exception as exc:
        logger.warning("Workday request failed for %s: %s", company, exc)
        return []

    jobs: list[ScrapedJob] = []
    for item in payload.get("jobPostings", []):
        title = str(item.get("title") or "").strip()
        ext_path = str(item.get("externalPath") or "").strip()
        location = str(item.get("locationsText") or "").strip()
        deadline = extract_deadline_value(item)
        if not title or not ext_path:
            continue
        job_url = endpoint.replace("/jobs", ext_path)
        jobs.append(
            ScrapedJob(
                title=title,
                location=location,
                employment_type="",
                url=job_url,
                application_deadline=deadline,
            )
        )
    return jobs
