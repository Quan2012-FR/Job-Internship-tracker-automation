from __future__ import annotations

from src.core.utils import normalize_text


def build_search_keywords(
    active_categories: list[str],
    keyword_categories: dict[str, list[str]],
    custom_keywords: list[str] | None = None,
    fallback_keywords: list[str] | None = None,
) -> list[str]:
    keywords: list[str] = []
    for category in active_categories:
        keywords.extend(keyword_categories.get(_category_key(category), []))
    keywords.extend(custom_keywords or [])
    if not keywords and fallback_keywords:
        keywords.extend(fallback_keywords)
    return _dedupe_keywords(keywords)


def matches_job_keywords(title: str, keywords: list[str], description: str = "") -> bool:
    haystack = f"{normalize_text(title)} {normalize_text(description)}".lower()
    return any(keyword.lower() in haystack for keyword in keywords)


def is_engineering_job(title: str, keywords: list[str], description: str = "") -> bool:
    return matches_job_keywords(title=title, keywords=keywords, description=description)


def _dedupe_keywords(keywords: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for keyword in keywords:
        normalized = normalize_text(keyword).lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalize_text(keyword))
    return deduped


def _category_key(category: str) -> str:
    return normalize_text(category).lower().replace("-", "_").replace(" ", "_")
