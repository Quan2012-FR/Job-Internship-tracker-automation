from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timedelta
from urllib.parse import quote_plus, urljoin, urlparse

from bs4 import BeautifulSoup

from config import DiscoveryConfig
from src.core import database as db
from src.core.models import CompanyTarget
from src.core.utils import normalize_text

PLATFORM_HINTS = {
    "workday": ("workday", "myworkdayjobs"),
    "greenhouse": ("greenhouse",),
    "lever": ("lever.co",),
    "icims": ("icims",),
    "taleo": ("taleo",),
}

CAREERS_PATHS = (
    "/careers",
    "/career",
    "/jobs",
    "/join-us",
    "/work-with-us",
    "/company/careers",
    "/en/careers",
    "/en/jobs",
)


def detect_platform(url: str) -> str:
    lower_url = url.lower()
    for platform, hints in PLATFORM_HINTS.items():
        if any(hint in lower_url for hint in hints):
            return platform
    return "generic"


def resolve_careers_url(
    target: CompanyTarget,
    conn: sqlite3.Connection,
    http_client,
    logger,
    cfg: DiscoveryConfig,
) -> str:
    provided_url = normalize_text(target.careers_url)
    if provided_url:
        success = _is_probably_careers_page(provided_url, http_client, cfg.validate_urls, logger)
        db.upsert_career_url_cache(
            conn,
            target.company,
            provided_url,
            detect_platform(provided_url),
            datetime.now(),
            success,
            "workbook",
        )
        return provided_url

    if not cfg.enabled:
        return ""

    cached = db.get_cached_career_url(conn, target.company)
    if cached:
        cached_url = str(cached["careers_url"] or "")
        last_success = bool(cached["last_success"])
        last_validated = _parse_datetime(str(cached["last_validated"] or ""))
        age = datetime.now() - last_validated if last_validated else None
        if cached_url and last_success and age is not None and age <= timedelta(days=cfg.cache_ttl_days):
            if age <= timedelta(days=cfg.revalidate_after_days):
                return cached_url
            if _is_probably_careers_page(cached_url, http_client, cfg.validate_urls, logger):
                db.upsert_career_url_cache(
                    conn,
                    target.company,
                    cached_url,
                    detect_platform(cached_url),
                    datetime.now(),
                    True,
                    str(cached["source"] or "cache"),
                )
                return cached_url

    discovered = discover_careers_url(target.company, http_client, logger, cfg)
    if discovered:
        db.upsert_career_url_cache(
            conn,
            target.company,
            discovered,
            detect_platform(discovered),
            datetime.now(),
            True,
            "discovery",
        )
        return discovered

    return ""


def discover_careers_url(company: str, http_client, logger, cfg: DiscoveryConfig) -> str:
    for candidate in _candidate_urls(company, cfg.max_candidates):
        if _is_probably_careers_page(candidate, http_client, cfg.validate_urls, logger):
            return candidate

    if not cfg.search_fallback:
        return ""

    for candidate in _search_candidates(company, http_client, logger):
        if _is_probably_careers_page(candidate, http_client, cfg.validate_urls, logger):
            return candidate
    return ""


def _candidate_urls(company: str, limit: int) -> list[str]:
    slug = _company_slug(company)
    compact = slug.replace("-", "")
    domains = []
    for host in (compact, slug):
        if host and host not in domains:
            domains.append(host)

    candidates: list[str] = []
    for domain in domains:
        for prefix in ("https://www.", "https://"):
            base = f"{prefix}{domain}.com"
            candidates.extend(urljoin(base, path) for path in CAREERS_PATHS)
    return candidates[: max(0, limit)]


def _search_candidates(company: str, http_client, logger) -> list[str]:
    query = quote_plus(f"{company} careers jobs")
    search_urls = (
        f"https://www.bing.com/search?q={query}",
        f"https://duckduckgo.com/html/?q={query}",
    )
    candidates: list[str] = []
    for search_url in search_urls:
        try:
            response = http_client.get(search_url)
            if response.status_code >= 400:
                continue
            soup = BeautifulSoup(response.text, "html.parser")
            for anchor in soup.find_all("a", href=True):
                href = str(anchor.get("href") or "")
                parsed = urlparse(href)
                if parsed.scheme not in {"http", "https"}:
                    continue
                lower = href.lower()
                if any(word in lower for word in ("career", "jobs", "workday", "greenhouse", "lever.co", "icims")):
                    candidates.append(href)
        except Exception as exc:
            logger.debug("Search fallback failed for %s via %s: %s", company, search_url, exc)
    return _dedupe_urls(candidates)[:10]


def _is_probably_careers_page(url: str, http_client, validate: bool, logger) -> bool:
    if not validate:
        return True
    try:
        response = http_client.get(url, allow_redirects=True)
        if response.status_code >= 400:
            return False
        final_url = response.url or url
        text = response.text[:200000].lower()
        platform = detect_platform(final_url)
        if platform != "generic":
            return True
        return any(word in text for word in ("career", "jobs", "open positions", "job openings", "internship"))
    except Exception as exc:
        logger.debug("Careers URL validation failed for %s: %s", url, exc)
        return False


def _company_slug(company: str) -> str:
    text = normalize_text(company).lower()
    text = re.sub(r"\b(inc|inc\.|llc|ltd|ltd\.|corp|corp\.|corporation|company|co\.|gmbh|ag|se)\b", "", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def _dedupe_urls(urls: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for url in urls:
        key = url.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(url)
    return deduped


def _parse_datetime(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None
