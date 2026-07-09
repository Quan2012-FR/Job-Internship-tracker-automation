from __future__ import annotations

from src.scrapers import generic, greenhouse, icims, lever, taleo, workday
from src.scrapers.base import ScrapedJob


SCRAPERS = [workday, greenhouse, lever, icims, taleo]


def fetch_jobs_for_company(company: str, careers_url: str, http_client, logger) -> list[ScrapedJob]:
    for scraper in SCRAPERS:
        if scraper.can_handle(careers_url):
            jobs = scraper.fetch_jobs(company, careers_url, http_client, logger)
            if jobs:
                return jobs
    return generic.fetch_jobs(company, careers_url, http_client, logger)
