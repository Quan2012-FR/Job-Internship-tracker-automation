from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from src.core.http_client import HttpClient


class HttpClientTests(unittest.TestCase):
    def test_get_uses_default_connect_and_read_timeout(self) -> None:
        session = Mock()
        response = object()
        session.get.return_value = response
        client = HttpClient(session=session, connect_timeout_seconds=5, timeout_seconds=25, delay_seconds=0.0)

        with patch("src.core.http_client.time.sleep") as sleep_mock:
            result = client.get("https://example.com/jobs")

        self.assertIs(result, response)
        session.get.assert_called_once_with("https://example.com/jobs", timeout=(5, 25))
        sleep_mock.assert_called_once_with(0.0)

    def test_get_preserves_caller_timeout_override(self) -> None:
        session = Mock()
        response = object()
        session.get.return_value = response
        client = HttpClient(session=session, connect_timeout_seconds=5, timeout_seconds=25, delay_seconds=0.0)

        with patch("src.core.http_client.time.sleep"):
            result = client.get("https://example.com/jobs", timeout=(1, 2))

        self.assertIs(result, response)
        session.get.assert_called_once_with("https://example.com/jobs", timeout=(1, 2))


if __name__ == "__main__":
    unittest.main()
