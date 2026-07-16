from __future__ import annotations

import unittest
from unittest.mock import Mock

from src.scrapers import generic


class GenericScraperTests(unittest.TestCase):
    def test_extracts_wabtec_style_job_links_from_plain_html(self) -> None:
        html = """
        <html>
          <body>
            <a href="/job/test-engineer-in-erie-pa-jid-3383">Test Engineer</a>
            <a href="/job/test-engineer-in-erie-pa-jid-3383">Read more</a>
            <a href="/engineering">Engineering</a>
          </body>
        </html>
        """
        http_client = Mock()
        http_client.get.return_value = Mock(status_code=200, text=html)
        logger = Mock()

        jobs = generic.fetch_jobs("Wabtec", "https://careers.wabtec.com/jobs", http_client, logger)

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].title, "Test Engineer")
        self.assertEqual(jobs[0].url, "https://careers.wabtec.com/job/test-engineer-in-erie-pa-jid-3383")

    def test_extracts_caterpillar_style_job_links_from_plain_html(self) -> None:
        html = """
        <html>
          <body>
            <div class="card-job">
              <h2><a href="/en/jobs/r0000382769/facilities-engineer/">Facilities Engineer</a></h2>
            </div>
            <a href="/en/career-areas/engineering/">Engineering</a>
          </body>
        </html>
        """
        http_client = Mock()
        http_client.get.return_value = Mock(status_code=200, text=html)
        logger = Mock()

        jobs = generic.fetch_jobs("Caterpillar", "https://careers.caterpillar.com/en/jobs/", http_client, logger)

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].title, "Facilities Engineer")
        self.assertEqual(jobs[0].url, "https://careers.caterpillar.com/en/jobs/r0000382769/facilities-engineer/")


if __name__ == "__main__":
    unittest.main()
