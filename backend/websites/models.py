"""Data models for the Admin Portal's website onboarding pipeline."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

# pending -> crawling -> understanding -> embedding -> discovering_flows -> ready
# any stage can transition to "failed" with error_message set.
WEBSITE_STATUSES = (
    "pending",
    "crawling",
    "understanding",
    "embedding",
    "discovering_flows",
    "ready",
    "failed",
)


class Website(BaseModel):
    id: int
    website_id: str
    url: str
    name: str
    max_pages: int
    max_depth: int
    status: str
    error_message: str | None = None
    page_count: int = 0
    created_at: datetime
    updated_at: datetime
