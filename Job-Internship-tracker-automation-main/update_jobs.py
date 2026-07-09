from __future__ import annotations

import argparse
from pathlib import Path

from config import build_config
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
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cfg = build_config(
        source_workbook=args.input,
        output_workbook=args.output,
        database_path=args.database,
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
