from __future__ import annotations

import runpy
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent / "Job-Internship-tracker-automation-main"
TRACKER_SCRIPT = PROJECT_DIR / "update_jobs.py"


if __name__ == "__main__":
    sys.path.insert(0, str(PROJECT_DIR))
    runpy.run_path(str(TRACKER_SCRIPT), run_name="__main__")
