from __future__ import annotations

import unittest
from unittest.mock import Mock

import requests

from src.core.discovery import _candidate_urls, _is_probably_careers_page


class DiscoveryTests(unittest.TestCase):
    def test_wabtec_known_careers_subdomain_is_prioritized(self) -> None:
        candidates = _candidate_urls("Wabtec", 5)
        self.assertIn("https://careers.wabtec.com/jobs", candidates)
        self.assertEqual(candidates[0], "https://careers.wabtec.com/jobs")

    def test_catepillar_alias_uses_caterpillar_careers_site(self) -> None:
        candidates = _candidate_urls("Catepillar", 5)
        self.assertEqual(candidates[0], "https://careers.caterpillar.com/en/jobs/")

    def test_validation_timeout_returns_false(self) -> None:
        http_client = Mock()
        http_client.get.side_effect = requests.exceptions.Timeout("connect timed out")
        logger = Mock()

        result = _is_probably_careers_page(
            "https://example.com/careers",
            http_client,
            True,
            logger,
            company="Example Corp",
        )

        self.assertFalse(result)
        logger.warning.assert_called_once()
        args = logger.warning.call_args.args
        self.assertIn("timed out", args[1].lower())
        self.assertEqual(args[1], "Careers URL candidate timed out")

    def test_validation_ssl_error_returns_false(self) -> None:
        http_client = Mock()
        http_client.get.side_effect = requests.exceptions.SSLError("certificate verify failed")
        logger = Mock()

        result = _is_probably_careers_page(
            "https://example.com/careers",
            http_client,
            True,
            logger,
            company="Example Corp",
        )

        self.assertFalse(result)
        logger.warning.assert_called_once()
        args = logger.warning.call_args.args
        self.assertIn("ssl", args[1].lower())

    def test_connection_error_with_timeout_text_is_logged_as_timeout(self) -> None:
        http_client = Mock()
        http_client.get.side_effect = requests.exceptions.ConnectionError("Read timed out")
        logger = Mock()

        result = _is_probably_careers_page(
            "https://example.com/careers",
            http_client,
            True,
            logger,
            company="Example Corp",
        )

        self.assertFalse(result)
        logger.warning.assert_called_once()
        args = logger.warning.call_args.args
        self.assertIn("timed out", args[1].lower())

    def test_successful_validation_returns_true(self) -> None:
        http_client = Mock()
        response = Mock(status_code=200, url="https://example.com/careers", text="Open positions and internships")
        http_client.get.return_value = response
        logger = Mock()

        result = _is_probably_careers_page(
            "https://example.com/careers",
            http_client,
            True,
            logger,
            company="Example Corp",
        )

        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
