from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ScrapedJob:
    title: str
    location: str
    employment_type: str
    url: str
    description: str = ""
