from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from update_jobs import resolve_input_path, resolve_project_path


class UpdateJobsPathTests(unittest.TestCase):
    def test_default_input_prefers_companies_workbook(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            (project_dir / "companies.xlsx").touch()
            (project_dir / "sample_data.xlsx").touch()

            resolved = resolve_input_path(None, project_dir=project_dir)

            self.assertEqual(resolved, (project_dir / "companies.xlsx").resolve())

    def test_default_input_falls_back_to_sample_workbook(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            (project_dir / "sample_data.xlsx").touch()

            resolved = resolve_input_path(None, project_dir=project_dir)

            self.assertEqual(resolved, (project_dir / "sample_data.xlsx").resolve())

    def test_relative_input_can_be_resolved_from_project_folder(self) -> None:
        with tempfile.TemporaryDirectory() as project_tmpdir, tempfile.TemporaryDirectory() as cwd_tmpdir:
            project_dir = Path(project_tmpdir)
            workbook = project_dir / "custom.xlsx"
            workbook.touch()

            resolved = resolve_input_path(
                "custom.xlsx",
                project_dir=project_dir,
                working_dir=Path(cwd_tmpdir),
            )

            self.assertEqual(resolved, workbook.resolve())

    def test_relative_output_is_anchored_to_project_folder(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            resolved = resolve_project_path("dashboard.xlsx", project_dir=project_dir)

            self.assertEqual(resolved, (project_dir / "dashboard.xlsx").resolve())


if __name__ == "__main__":
    unittest.main()
