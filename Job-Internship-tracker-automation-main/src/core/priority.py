from __future__ import annotations

from datetime import date, datetime

from config import AppConfig
from src.core.models import JobPosting
from src.core.utils import normalize_text


APPLICATION_STATUSES = [
    "Not Started",
    "Application Opened",
    "Applied",
    "Interviewing",
    "Rejected",
    "Offer",
    "Withdrawn",
]


def parse_deadline(value: str, today: date | None = None) -> tuple[str, int | None]:
    raw_value = normalize_text(value)
    if not raw_value:
        return "", None

    today = today or date.today()
    parsed = _parse_date(raw_value)
    if parsed is None:
        return raw_value, None

    return parsed.isoformat(), max((parsed - today).days, 0)


def score_job(job: JobPosting, description: str, keywords: list[str], cfg: AppConfig, now: datetime | None = None) -> int:
    now = now or datetime.now()
    factors = [
        (cfg.deadline_weight, _deadline_factor(job.days_remaining)),
        (cfg.recency_weight, _recency_factor(job.first_seen, now)),
        (cfg.engineering_match_weight, _engineering_match_factor(job.title, description, keywords)),
        (cfg.internship_weight, _term_factor(job, ("intern", "internship", "co-op", "coop"))),
        (cfg.fulltime_weight, _term_factor(job, ("full-time", "full time", "fulltime", "new grad"))),
    ]
    if cfg.preferred_companies:
        factors.append((cfg.company_preference_weight, _preference_factor(job.company, cfg.preferred_companies)))
    if cfg.preferred_locations:
        factors.append((cfg.location_preference_weight, _preference_factor(job.location, cfg.preferred_locations)))
    total_weight = sum(max(weight, 0) for weight, _ in factors)
    if total_weight <= 0:
        return 0
    weighted = sum(max(weight, 0) * max(0.0, min(value, 1.0)) for weight, value in factors)
    return max(0, min(100, round((weighted / total_weight) * 100)))


def _parse_date(value: str) -> date | None:
    cleaned = value.strip()
    for suffix in ("Z", "+00:00"):
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)]
            break
    if "T" in cleaned:
        cleaned = cleaned.split("T", 1)[0]

    formats = (
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%d %B %Y",
        "%d %b %Y",
    )
    for fmt in formats:
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    return None


def _deadline_factor(days_remaining: int | None) -> float:
    if days_remaining is None:
        return 0.25
    if days_remaining <= 7:
        return 1.0
    if days_remaining <= 14:
        return 0.8
    if days_remaining <= 30:
        return 0.55
    if days_remaining <= 60:
        return 0.35
    return 0.15


def _recency_factor(first_seen: datetime, now: datetime) -> float:
    age_days = max((now - first_seen).days, 0)
    if age_days <= 1:
        return 1.0
    if age_days <= 7:
        return 0.8
    if age_days <= 14:
        return 0.55
    if age_days <= 30:
        return 0.3
    return 0.1


def _engineering_match_factor(title: str, description: str, keywords: list[str]) -> float:
    haystack = f"{normalize_text(title)} {normalize_text(description)}".lower()
    if not haystack:
        return 0.0
    matches = {keyword.lower() for keyword in keywords if keyword.lower() in haystack}
    return min(1.0, len(matches) / 3)


def _term_factor(job: JobPosting, terms: tuple[str, ...]) -> float:
    haystack = f"{job.title} {job.employment_type}".lower()
    return 1.0 if any(term in haystack for term in terms) else 0.0


def _preference_factor(value: str, preferences: list[str]) -> float:
    if not preferences:
        return 0.0
    normalized_value = value.lower()
    return 1.0 if any(pref.lower() in normalized_value for pref in preferences) else 0.0