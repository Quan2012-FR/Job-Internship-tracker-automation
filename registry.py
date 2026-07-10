from __future__ import annotations

from src.scrapers import browser, generic, greenhouse, icims, lever, taleo, workday
from src.scrapers.base import ScrapedJob


SCRAPERS = [workday, greenhouse, lever, icims, taleo]


def fetch_jobs_for_company(
    company: str,
    careers_url: str,
    http_client,
    logger,
    use_browser_fallback: bool = False,
    headless: bool = True,
    timeout_ms: int = 15000,
) -> list[ScrapedJob]:
    for scraper in SCRAPERS:
        if scraper.can_handle(careers_url):
            jobs = scraper.fetch_jobs(company, careers_url, http_client, logger)
            if jobs:
                return jobs
    jobs = generic.fetch_jobs(company, careers_url, http_client, logger)
    if jobs or not use_browser_fallback:
        return jobs
    logger.info("Static scraping found no jobs for %s; trying Playwright fallback", company)
    return browser.fetch_jobs(company, careers_url, logger, headless=headless, timeout_ms=timeout_ms)
