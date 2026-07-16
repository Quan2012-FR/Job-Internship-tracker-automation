from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests

from config import build_config
from src.core.models import CompanyTarget
from src.core.pipeline import run_update


class PipelineTests(unittest.TestCase):
    def test_failed_company_does_not_prevent_next_company(self) -> None:
        targets = [
            CompanyTarget(company="Broken Co", careers_url="", source_sheet="Sheet1", source_row=2, metadata={}),
            CompanyTarget(company="Healthy Co", careers_url="", source_sheet="Sheet1", source_row=3, metadata={}),
        ]
        logger = Mock()
        conn = Mock()

        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = build_config(
                source_workbook=str(Path(tmpdir) / "input.xlsx"),
                output_workbook=str(Path(tmpdir) / "output.xlsx"),
                database_path=str(Path(tmpdir) / "jobs.db"),
                max_companies=2,
            )

            with (
                patch("src.core.pipeline.setup_logging", return_value=logger),
                patch("src.core.pipeline.extract_company_targets", return_value=targets),
                patch("src.core.pipeline.build_http_client", return_value=object()),
                patch("src.core.pipeline.build_search_keywords", return_value=["engineer"]),
                patch(
                    "src.core.pipeline.resolve_careers_url",
                    side_effect=[requests.exceptions.SSLError("bad cert"), "https://ok.example/jobs"],
                ),
                patch("src.core.pipeline.fetch_jobs_for_company", return_value=[]),
                patch("src.core.pipeline.write_dashboard"),
                patch("src.core.pipeline.db.connect_db", return_value=conn),
                patch("src.core.pipeline.db.init_db"),
                patch("src.core.pipeline.db.upsert_jobs", return_value=(0, set())),
                patch("src.core.pipeline.db.mark_inactive_missing", return_value=0),
                patch("src.core.pipeline.db.get_total_active_jobs", return_value=0),
            ):
                stats = run_update(cfg)

        self.assertEqual(stats.companies_checked, 2)
        self.assertEqual(stats.errors_encountered, 1)
        self.assertGreaterEqual(logger.warning.call_count, 1)

        progress_messages = [call.args for call in logger.info.call_args_list if call.args]
        self.assertIn(("Processing company %d/%d: %s", 1, 2, "Broken Co"), progress_messages)
        self.assertIn(("Processing company %d/%d: %s", 2, 2, "Healthy Co"), progress_messages)
        conn.close.assert_called_once()

    def test_keyboard_interrupt_is_not_swallowed(self) -> None:
        targets = [CompanyTarget(company="Interrupt Co", careers_url="", source_sheet="Sheet1", source_row=2, metadata={})]
        logger = Mock()
        conn = Mock()

        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = build_config(
                source_workbook=str(Path(tmpdir) / "input.xlsx"),
                output_workbook=str(Path(tmpdir) / "output.xlsx"),
                database_path=str(Path(tmpdir) / "jobs.db"),
                max_companies=1,
            )

            with (
                patch("src.core.pipeline.setup_logging", return_value=logger),
                patch("src.core.pipeline.extract_company_targets", return_value=targets),
                patch("src.core.pipeline.build_http_client", return_value=object()),
                patch("src.core.pipeline.build_search_keywords", return_value=["engineer"]),
                patch("src.core.pipeline.resolve_careers_url", side_effect=KeyboardInterrupt),
                patch("src.core.pipeline.write_dashboard"),
                patch("src.core.pipeline.db.connect_db", return_value=conn),
                patch("src.core.pipeline.db.init_db"),
            ):
                with self.assertRaises(KeyboardInterrupt):
                    run_update(cfg)

        conn.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
