from __future__ import annotations

from src.core.utils import normalize_text


def is_engineering_job(title: str, keywords: list[str], description: str = "") -> bool:
    haystack = f"{normalize_text(title)} {normalize_text(description)}".lower()
    return any(keyword.lower() in haystack for keyword in keywords)
