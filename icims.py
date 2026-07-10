from __future__ import annotations

from src.scrapers import generic
from src.scrapers.base import ScrapedJob


def can_handle(url: str) -> bool:
    u = url.lower()
    return "icims" in u


def fetch_jobs(company: str, careers_url: str, http_client, logger) -> list[ScrapedJob]:
    # Many iCIMS portals are dynamic and vary per tenant.
    # Fallback to JSON-LD extraction from public page markup.
    return generic.fetch_jobs(company, careers_url, http_client, logger)
