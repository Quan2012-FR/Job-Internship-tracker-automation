from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


@dataclass(slots=True)
class HttpClient:
    session: requests.Session
    connect_timeout_seconds: int
    timeout_seconds: int
    delay_seconds: float

    def get(self, url: str, **kwargs):
        kwargs.setdefault("timeout", (self.connect_timeout_seconds, self.timeout_seconds))
        response = self.session.get(url, **kwargs)
        time.sleep(self.delay_seconds)
        return response


def build_http_client(
    headers: Optional[dict[str, str]],
    connect_timeout_seconds: int,
    timeout_seconds: int,
    delay_seconds: float,
) -> HttpClient:
    session = requests.Session()
    retry = Retry(
        total=0,
        connect=0,
        read=0,
        redirect=2,
        status=0,
        other=0,
        backoff_factor=0,
        allowed_methods=frozenset({"GET", "HEAD", "OPTIONS"}),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.max_redirects = 5
    if headers:
        session.headers.update(headers)
    return HttpClient(
        session=session,
        connect_timeout_seconds=connect_timeout_seconds,
        timeout_seconds=timeout_seconds,
        delay_seconds=delay_seconds,
    )
