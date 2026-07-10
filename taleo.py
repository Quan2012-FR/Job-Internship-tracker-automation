from __future__ import annotations

from src.scrapers import generic
from src.scrapers.base import ScrapedJob


def can_handle(url: str) -> bool:
    u = url.lower()
    return "taleo" in u


def fetch_jobs(company: str, careers_url: str, http_client, logger) -> list[ScrapedJob]:
    # Taleo implementations differ significantly by tenant.
    # Use generic JSON-LD fallback by default.
    return generic.fetch_jobs(company, careers_url, http_client, logger)
