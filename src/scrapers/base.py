from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ScrapedJob:
    title: str
    location: str
    employment_type: str
    url: str
    description: str = ""
    application_deadline: str = ""


DEADLINE_KEYS = (
    "applicationDeadline",
    "application_deadline",
    "validThrough",
    "closeDate",
    "closingDate",
    "expirationDate",
    "postingExpirationDate",
    "jobPostingEndDate",
    "endDate",
    "scheduledUnpostingDate",
)


def extract_deadline_value(payload: dict) -> str:
    for key in DEADLINE_KEYS:
        value = payload.get(key)
        if value:
            return str(value).strip()
    return ""
