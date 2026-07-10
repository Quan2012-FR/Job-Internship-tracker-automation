from __future__ import annotations

import argparse
from pathlib import Path

from config import DiscoveryConfig, WorkbookMapping, build_config
from src.core.pipeline import run_update


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan company career pages and build an engineering jobs dashboard."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to source company workbook (read-only input).",
    )
    parser.add_argument(
        "--output",
        default="engineering_job_dashboard.xlsx",
        help="Path to output dashboard workbook.",
    )
    parser.add_argument(
        "--database",
        default="jobs.db",
        help="Path to SQLite database file.",
    )
    parser.add_argument("--sheet", help="Worksheet name to read. Defaults to the first matching sheet.")
    parser.add_argument("--company-column", help="Header name for the company column.")
    parser.add_argument("--url-column", help="Header name for the optional careers URL column.")
    parser.add_argument("--max-companies", type=int, help="Limit how many companies are processed in this run.")
    parser.add_argument(
        "--no-discovery",
        action="store_true",
        help="Do not discover careers URLs when the workbook URL is missing.",
    )
    parser.add_argument(
        "--no-search-fallback",
        action="store_true",
        help="Skip search-engine based careers URL discovery fallback.",
    )
    parser.add_argument(
        "--cache-ttl-days",
        type=int,
        default=30,
        help="Days to trust successful cached career URLs before fresh discovery is attempted.",
    )
    parser.add_argument(
        "--revalidate-after-days",
        type=int,
        default=7,
        help="Days before a cached careers URL is revalidated when used.",
    )
    parser.add_argument(
        "--max-discovery-candidates",
        type=int,
        default=12,
        help="Maximum candidate careers URLs to probe per company.",
    )
    parser.add_argument(
        "--playwright-fallback",
        action="store_true",
        help="Use Playwright rendering when static scraping finds no jobs.",
    )
    parser.add_argument(
        "--show-browser",
        action="store_true",
        help="Show the browser window when Playwright fallback is enabled.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cfg = build_config(
        source_workbook=args.input,
        output_workbook=args.output,
        database_path=args.database,
        workbook_mapping=WorkbookMapping(
            sheet_name=args.sheet,
            company_column=args.company_column,
            careers_url_column=args.url_column,
        ),
        discovery=DiscoveryConfig(
            enabled=not args.no_discovery,
            cache_ttl_days=args.cache_ttl_days,
            revalidate_after_days=args.revalidate_after_days,
            max_candidates=args.max_discovery_candidates,
            search_fallback=not args.no_search_fallback,
        ),
        max_companies=args.max_companies,
        use_playwright_fallback=args.playwright_fallback,
        headless_browser=not args.show_browser,
    )

    stats = run_update(cfg)
    print("Run complete")
    print(f"Companies checked: {stats.companies_checked}")
    print(f"Jobs found this run: {stats.jobs_found_this_run}")
    print(f"New jobs this run: {stats.new_jobs_this_run}")
    print(f"Jobs marked inactive: {stats.jobs_marked_inactive}")
    print(f"Total active jobs: {stats.total_active_jobs}")
    print(f"Dashboard written: {Path(cfg.output_workbook)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
