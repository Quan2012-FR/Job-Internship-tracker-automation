from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

import requests


@dataclass(slots=True)
class HttpClient:
    session: requests.Session
    timeout_seconds: int
    delay_seconds: float

    def get(self, url: str, **kwargs):
        response = self.session.get(url, timeout=self.timeout_seconds, **kwargs)
        time.sleep(self.delay_seconds)
        return response


def build_http_client(headers: Optional[dict[str, str]], timeout_seconds: int, delay_seconds: float) -> HttpClient:
    session = requests.Session()
    if headers:
        session.headers.update(headers)
    return HttpClient(session=session, timeout_seconds=timeout_seconds, delay_seconds=delay_seconds)
