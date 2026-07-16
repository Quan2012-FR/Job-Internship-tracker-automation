from __future__ import annotations

import hashlib
import re
from urllib.parse import urlparse


URL_RE = re.compile(r"https?://[^\s)\]>\"']+", re.IGNORECASE)
COMPANY_NAME_ALIASES = {
    "catepillar": "Caterpillar",
    "idaho national labrotory": "Idaho National Laboratory",
    "karios power": "Kairos Power",
    "rolls royce": "Rolls-Royce",
}


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def canonicalize_company_name(value: str) -> str:
    normalized = normalize_text(value)
    if not normalized:
        return ""
    return COMPANY_NAME_ALIASES.get(normalized.lower(), normalized)


def extract_first_url(text: str) -> str:
    if not text:
        return ""
    direct = text.strip()
    if direct.lower().startswith("http://") or direct.lower().startswith("https://"):
        return direct
    match = URL_RE.search(text)
    return match.group(0).strip() if match else ""


def build_job_id(company: str, title: str, location: str, url: str) -> str:
    raw = "|".join(
        [
            normalize_text(company).lower(),
            normalize_text(title).lower(),
            normalize_text(location).lower(),
            normalize_text(url).lower(),
        ]
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def fallback_company_from_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower().replace("www.", "")
    if not host:
        return "Unknown Company"
    return host.split(":")[0]
