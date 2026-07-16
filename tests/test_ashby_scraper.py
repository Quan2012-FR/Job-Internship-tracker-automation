from __future__ import annotations

import json
import unittest
from unittest.mock import Mock

from src.scrapers import ashby


class AshbyScraperTests(unittest.TestCase):
    def test_extracts_jobs_from_app_data(self) -> None:
        payload = {
            "jobBoard": {
                "jobPostings": [
                    {
                        "id": "posting-123",
                        "title": "Controls Engineer",
                        "locationName": "Oak Ridge",
                        "locationExternalName": "Oak Ridge, TN",
                        "employmentType": "FullTime",
                        "applicationDeadline": "2026-08-01",
                        "isListed": True,
                    }
                ]
            }
        }
        html = f"""
        <html>
          <body>
            <script>
              window.__appData = {json.dumps(payload)};
              fetch("manifest.json");
            </script>
          </body>
        </html>
        """
        http_client = Mock()
        http_client.get.return_value = Mock(status_code=200, text=html)
        logger = Mock()

        jobs = ashby.fetch_jobs("Atomic Semi", "https://jobs.ashbyhq.com/atomicsemi", http_client, logger)

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].title, "Controls Engineer")
        self.assertEqual(jobs[0].location, "Oak Ridge, TN")
        self.assertEqual(jobs[0].employment_type, "FullTime")
        self.assertEqual(jobs[0].application_deadline, "2026-08-01")
        self.assertEqual(jobs[0].url, "https://jobs.ashbyhq.com/atomicsemi/posting-123")


if __name__ == "__main__":
    unittest.main()
