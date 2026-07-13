from __future__ import annotations

import json
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.scrapers.base import ScrapedJob, extract_deadline_value


def can_handle(url: str) -> bool:
    return True


def fetch_jobs(company: str, careers_url: str, http_client, logger) -> list[ScrapedJob]:
    jobs: list[ScrapedJob] = []
    try:
        resp = http_client.get(careers_url)
        if resp.status_code >= 400:
            return jobs
        soup = BeautifulSoup(resp.text, "html.parser")
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
    except Exception as exc:
        logger.warning("Generic scraper failed for %s (%s): %s", company, careers_url, exc)
    return jobs
