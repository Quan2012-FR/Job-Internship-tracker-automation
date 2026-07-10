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
    if use_playwright_fallback is not None:
        cfg.use_playwright_fallback = use_playwright_fallback
    if headless_browser is not None:
        cfg.headless_browser = headless_browser
    return cfg
