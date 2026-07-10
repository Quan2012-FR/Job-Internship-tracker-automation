from __future__ import annotations

import json
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.scrapers.base import ScrapedJob

JOB_LINK_TERMS = (
    "job",
    "career",
    "position",
    "opening",
    "intern",
    "engineer",
)


def fetch_jobs(company: str, careers_url: str, logger, headless: bool = True, timeout_ms: int = 15000) -> list[ScrapedJob]:
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning("Playwright fallback requested but playwright is not installed.")
        return []

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=headless)
            try:
                page = browser.new_page()
                page.goto(careers_url, wait_until="domcontentloaded", timeout=timeout_ms)
                try:
                    page.wait_for_load_state("networkidle", timeout=timeout_ms)
                except PlaywrightTimeoutError:
                    logger.debug("Timed out waiting for network idle at %s", careers_url)
                html = page.content()
            finally:
                browser.close()
    except Exception as exc:
        logger.warning("Playwright fallback failed for %s (%s): %s", company, careers_url, exc)
        return []

    jobs = _extract_json_ld_jobs(careers_url, html)
    if jobs:
        return jobs
    return _extract_job_links(careers_url, html)


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
        for item in _walk_json(data):
            if not isinstance(item, dict) or item.get("@type") != "JobPosting":
                continue
            title = str(item.get("title") or "").strip()
            url = str(item.get("url") or careers_url).strip()
            employment_type = str(item.get("employmentType") or "").strip()
            location = _json_ld_location(item)
            description = str(item.get("description") or "").strip()
            if title and url:
                jobs.append(
                    ScrapedJob(
                        title=title,
                        location=location,
                        employment_type=employment_type,
                        url=urljoin(careers_url, url),
                        description=description,
                    )
                )
    return jobs


def _extract_job_links(careers_url: str, html: str) -> list[ScrapedJob]:
    soup = BeautifulSoup(html, "html.parser")
    jobs: list[ScrapedJob] = []
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        title = " ".join(anchor.get_text(" ", strip=True).split())
        href = str(anchor.get("href") or "").strip()
        if not title or len(title) > 180 or not href:
            continue
        combined = f"{title} {href}".lower()
        if not any(term in combined for term in JOB_LINK_TERMS):
            continue
        url = urljoin(careers_url, href)
        if url.lower() in seen:
            continue
        seen.add(url.lower())
        jobs.append(ScrapedJob(title=title, location="", employment_type="", url=url))
    return jobs


def _walk_json(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_json(child)


def _json_ld_location(item: dict) -> str:
    job_location = item.get("jobLocation")
    if isinstance(job_location, list) and job_location:
        job_location = job_location[0]
    if not isinstance(job_location, dict):
        return ""
    address = job_location.get("address", {})
    if not isinstance(address, dict):
        return ""
    parts = [
        str(address.get("addressLocality") or "").strip(),
        str(address.get("addressRegion") or "").strip(),
        str(address.get("addressCountry") or "").strip(),
    ]
    return ", ".join(part for part in parts if part)
