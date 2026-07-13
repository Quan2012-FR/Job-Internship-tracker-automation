from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


DEFAULT_ENGINEERING_KEYWORDS: List[str] = [
    "engineer",
    "engineering",
    "mechanical",
    "electrical",
    "manufacturing",
    "industrial",
    "systems",
    "automation",
    "robotics",
    "controls",
    "test engineer",
    "quality engineer",
    "design engineer",
    "process engineer",
    "aerospace",
]


DEFAULT_KEYWORD_CATEGORIES: Dict[str, List[str]] = {
    "engineering": DEFAULT_ENGINEERING_KEYWORDS,
    "medical": [
        "medical",
        "healthcare",
        "clinical",
        "patient care",
        "nursing",
        "nurse",
        "registered nurse",
        "medical assistant",
        "lab technician",
        "pharmacy",
        "radiology",
    ],
    "business": [
        "business",
        "business analyst",
        "finance",
        "accounting",
        "sales",
        "marketing",
        "operations",
        "project manager",
        "supply chain",
        "human resources",
    ],
    "chemical_engineer": [
        "chemical engineer",
        "chemical engineering",
        "process engineer",
        "process engineering",
        "chemist",
        "chemistry",
        "chemical manufacturing",
    ],
    "manufacturing_engineer": [
        "manufacturing engineer",
        "manufacturing engineering",
        "production engineer",
        "process engineer",
        "industrial engineer",
        "lean manufacturing",
        "quality engineer",
    ],
    "rn": [
        "rn",
        "registered nurse",
        "staff nurse",
        "nurse residency",
        "clinical nurse",
    ],
    "construction_laborer": [
        "construction laborer",
        "construction worker",
        "general laborer",
        "site laborer",
        "field laborer",
        "crew member",
    ],
}


ACTIVE_KEYWORD_CATEGORIES: List[str] = ["engineering"]
CUSTOM_KEYWORDS: List[str] = []


PRIORITY_THRESHOLD = 60
PREFERRED_COMPANIES: List[str] = []
PREFERRED_LOCATIONS: List[str] = []
INTERNSHIP_WEIGHT = 10
FULLTIME_WEIGHT = 8
DEADLINE_WEIGHT = 30
RECENCY_WEIGHT = 20
KEYWORD_MATCH_WEIGHT = 25
ENGINEERING_MATCH_WEIGHT = KEYWORD_MATCH_WEIGHT
COMPANY_PREFERENCE_WEIGHT = 10
LOCATION_PREFERENCE_WEIGHT = 10


@dataclass(slots=True)
class WorkbookMapping:
    sheet_name: Optional[str] = None
    company_column: Optional[str] = None
    careers_url_column: Optional[str] = None


@dataclass(slots=True)
class DiscoveryConfig:
    enabled: bool = True
    cache_ttl_days: int = 30
    revalidate_after_days: int = 7
    max_candidates: int = 12
    search_fallback: bool = True
    validate_urls: bool = True


@dataclass(slots=True)
class AppConfig:
    source_workbook: Path = Path("companies.xlsx")
    output_workbook: Path = Path("engineering_job_dashboard.xlsx")
    database_path: Path = Path("jobs.db")
    logs_dir: Path = Path("logs")
    headless_browser: bool = True
    request_delay_seconds: float = 0.6
    request_timeout_seconds: int = 25
    browser_timeout_ms: int = 15000
    max_companies: Optional[int] = None
    engineering_keywords: List[str] = field(default_factory=lambda: DEFAULT_ENGINEERING_KEYWORDS.copy())
    keyword_categories: Dict[str, List[str]] = field(
        default_factory=lambda: {name: keywords.copy() for name, keywords in DEFAULT_KEYWORD_CATEGORIES.items()}
    )
    active_keyword_categories: List[str] = field(default_factory=lambda: ACTIVE_KEYWORD_CATEGORIES.copy())
    custom_keywords: List[str] = field(default_factory=lambda: CUSTOM_KEYWORDS.copy())
    priority_threshold: int = PRIORITY_THRESHOLD
    preferred_companies: List[str] = field(default_factory=lambda: PREFERRED_COMPANIES.copy())
    preferred_locations: List[str] = field(default_factory=lambda: PREFERRED_LOCATIONS.copy())
    internship_weight: int = INTERNSHIP_WEIGHT
    fulltime_weight: int = FULLTIME_WEIGHT
    deadline_weight: int = DEADLINE_WEIGHT
    recency_weight: int = RECENCY_WEIGHT
    keyword_match_weight: int = KEYWORD_MATCH_WEIGHT
    engineering_match_weight: int = ENGINEERING_MATCH_WEIGHT
    company_preference_weight: int = COMPANY_PREFERENCE_WEIGHT
    location_preference_weight: int = LOCATION_PREFERENCE_WEIGHT
    workbook_mapping: WorkbookMapping = field(default_factory=WorkbookMapping)
    discovery: DiscoveryConfig = field(default_factory=DiscoveryConfig)
    use_playwright_fallback: bool = False
    default_headers: Dict[str, str] = field(
        default_factory=lambda: {
            "User-Agent": "engineering-job-tracker/1.0",
            "Accept": "application/json, text/html;q=0.9,*/*;q=0.8",
        }
    )


def build_config(
    source_workbook: Optional[str] = None,
    output_workbook: Optional[str] = None,
    database_path: Optional[str] = None,
    workbook_mapping: Optional[WorkbookMapping] = None,
    discovery: Optional[DiscoveryConfig] = None,
    max_companies: Optional[int] = None,
    active_keyword_categories: Optional[List[str]] = None,
    custom_keywords: Optional[List[str]] = None,
    use_playwright_fallback: Optional[bool] = None,
    headless_browser: Optional[bool] = None,
) -> AppConfig:
    cfg = AppConfig()
    if source_workbook:
        cfg.source_workbook = Path(source_workbook)
    if output_workbook:
        cfg.output_workbook = Path(output_workbook)
    if database_path:
        cfg.database_path = Path(database_path)
    if workbook_mapping:
        cfg.workbook_mapping = workbook_mapping
    if discovery:
        cfg.discovery = discovery
    if max_companies is not None:
        cfg.max_companies = max_companies
    if active_keyword_categories is not None:
        cfg.active_keyword_categories = active_keyword_categories
    if custom_keywords is not None:
        cfg.custom_keywords = custom_keywords
    if use_playwright_fallback is not None:
        cfg.use_playwright_fallback = use_playwright_fallback
    if headless_browser is not None:
        cfg.headless_browser = headless_browser
    return cfg
