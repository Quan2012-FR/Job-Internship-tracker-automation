from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timedelta
from urllib.parse import quote_plus, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from config import DiscoveryConfig
from src.core import database as db
from src.core.models import CompanyTarget
from src.core.utils import canonicalize_company_name, normalize_text

KNOWN_COMPANY_URLS = {
    "wabtec": (
        "https://careers.wabtec.com/jobs",
        "https://careers.wabtec.com/",
    ),
    "caterpillar": (
        "https://careers.caterpillar.com/en/jobs/",
        "https://careers.caterpillar.com/en/",
        "https://careers.caterpillar.com/en/career-areas/engineering/",
    ),
    "oak ridge national laboratory": (
        "https://jobs.ornl.gov/search/",
        "https://jobs.ornl.gov/",
    ),
    "naval nuclear laboratory": (
        "https://navalnuclearlab.energy.gov/job-search/",
        "https://navalnuclearlab.energy.gov/careers/",
    ),
    "radiant nuclear": ("https://jobs.ashbyhq.com/radiant",),
    "atomic semi": (
        "https://jobs.ashbyhq.com/atomicsemi",
        "https://atomicsemi.com/careers",
    ),
}

COMPANY_DISCOVERY_ALIASES = {
    "caterpillar": "caterpillar",
    "idaho national laboratory": "idaho national laboratory",
    "kairos power": "kairos power",
    "rolls-royce": "rolls royce",
}

PLATFORM_HINTS = {
    "workday": ("workday", "myworkdayjobs"),
    "greenhouse": ("greenhouse",),
    "lever": ("lever.co",),
    "icims": ("icims",),
    "taleo": ("taleo",),
    "smartrecruiters": ("smartrecruiters", "jobs.smartrecruiters.com"),
    "ashby": ("jobs.ashbyhq.com", "ashbyhq"),
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


REQUEST_EXCEPTIONS = requests.exceptions


def resolve_careers_url(
    target: CompanyTarget,
    conn: sqlite3.Connection,
    http_client,
    logger,
    cfg: DiscoveryConfig,
) -> str:
    provided_url = normalize_text(target.careers_url)
    if provided_url:
        success = _is_probably_careers_page(
            provided_url,
            http_client,
            cfg.validate_urls,
            logger,
            company=target.company,
        )
        db.upsert_career_url_cache(
            conn,
            target.company,
            provided_url,
            detect_platform(provided_url),
            datetime.now(),
            success,
            "workbook",
        )
        if success:
            return provided_url
        if not cfg.enabled:
            return ""

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
            if _is_probably_careers_page(
                cached_url,
                http_client,
                cfg.validate_urls,
                logger,
                company=target.company,
            ):
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
        if _is_probably_careers_page(candidate, http_client, cfg.validate_urls, logger, company=company):
            return candidate

    if not cfg.search_fallback:
        return ""

    for candidate in _search_candidates(company, http_client, logger):
        if _is_probably_careers_page(candidate, http_client, cfg.validate_urls, logger, company=company):
            return candidate
    return ""


def _candidate_urls(company: str, limit: int) -> list[str]:
    normalized_company = _normalize_company_for_discovery(company)
    known_candidates = list(KNOWN_COMPANY_URLS.get(normalized_company.lower(), ()))
    slug = _company_slug(normalized_company)
    compact = slug.replace("-", "")
    domains = []
    for host in (compact, slug):
        if host and host not in domains:
            domains.append(host)

    candidates: list[str] = []
    candidates.extend(known_candidates)
    for domain in domains:
        for prefix in ("https://careers.", "https://jobs.", "https://www.", "https://"):
            base = f"{prefix}{domain}.com"
            candidates.extend(urljoin(base, path) for path in CAREERS_PATHS)
            if prefix in {"https://careers.", "https://jobs."}:
                candidates.append(base.rstrip("/"))
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
                logger.info(
                    "Search fallback returned HTTP %s for %s via %s",
                    response.status_code,
                    company,
                    search_url,
                )
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
        except REQUEST_EXCEPTIONS.Timeout as exc:
            _log_request_failure(logger, company, search_url, "search fallback timed out", exc)
        except REQUEST_EXCEPTIONS.SSLError as exc:
            _log_request_failure(logger, company, search_url, "search fallback SSL failure", exc)
        except REQUEST_EXCEPTIONS.TooManyRedirects as exc:
            _log_request_failure(logger, company, search_url, "search fallback redirected excessively", exc)
        except REQUEST_EXCEPTIONS.ConnectionError as exc:
            _log_request_failure(logger, company, search_url, _connection_error_reason("search fallback", exc), exc)
        except REQUEST_EXCEPTIONS.RequestException as exc:
            _log_request_failure(logger, company, search_url, "search fallback request failed", exc)
        except Exception:
            logger.exception("Unexpected search fallback error for %s via %s", company, search_url)
    return _dedupe_urls(candidates)[:10]


def _is_probably_careers_page(url: str, http_client, validate: bool, logger, company: str = "") -> bool:
    if not validate:
        return True
    logger.info("Testing careers URL candidate for %s: %s", company or "unknown company", url)
    try:
        response = http_client.get(url, allow_redirects=True)
        if response.status_code >= 400:
            logger.info(
                "Careers URL candidate returned HTTP %s for %s: %s",
                response.status_code,
                company or "unknown company",
                url,
            )
            return False
        final_url = response.url or url
        text = response.text[:200000].lower()
        platform = detect_platform(final_url)
        if platform != "generic":
            return True
        return any(word in text for word in ("career", "jobs", "open positions", "job openings", "internship"))
    except REQUEST_EXCEPTIONS.Timeout as exc:
        _log_request_failure(logger, company, url, "careers URL candidate timed out", exc)
        return False
    except REQUEST_EXCEPTIONS.SSLError as exc:
        _log_request_failure(logger, company, url, "careers URL candidate SSL failure", exc)
        return False
    except REQUEST_EXCEPTIONS.TooManyRedirects as exc:
        _log_request_failure(logger, company, url, "careers URL candidate redirected excessively", exc)
        return False
    except REQUEST_EXCEPTIONS.ConnectionError as exc:
        _log_request_failure(logger, company, url, _connection_error_reason("careers URL candidate", exc), exc)
        return False
    except REQUEST_EXCEPTIONS.RequestException as exc:
        _log_request_failure(logger, company, url, "careers URL candidate request failed", exc)
        return False


def _log_request_failure(logger, company: str, url: str, reason: str, exc: Exception) -> None:
    formatted_reason = reason[:1].upper() + reason[1:] if reason else "Request failure"
    logger.warning("%s for %s: %s (%s)", formatted_reason, company or "unknown company", url, exc)


def _connection_error_reason(prefix: str, exc: Exception) -> str:
    details = str(exc).lower()
    if "timed out" in details or "timeout" in details:
        return f"{prefix} timed out"
    return f"{prefix} connection failure"


def _company_slug(company: str) -> str:
    text = normalize_text(company).lower()
    text = re.sub(r"\b(inc|inc\.|llc|ltd|ltd\.|corp|corp\.|corporation|company|co\.|gmbh|ag|se)\b", "", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def _normalize_company_for_discovery(company: str) -> str:
    normalized = canonicalize_company_name(company).lower()
    return COMPANY_DISCOVERY_ALIASES.get(normalized, normalized)


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
