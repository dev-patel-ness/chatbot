"""Data models for Stage 2 — Website Understanding (architecture.md §7)."""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

ALLOWED_PAGE_TYPES = ("service", "industry", "insight", "about", "contact", "home", "other")


class PageClassification(BaseModel):
    page: str
    type: str
    confidence: float


class PageActions(BaseModel):
    page: str
    actions: list[str] = Field(default_factory=list)

    @field_validator("actions", mode="before")
    @classmethod
    def _normalize_actions(cls, value: list) -> list[str]:
        # Some models occasionally return {"type": ..., "element": ...} instead of a plain string.
        normalized = []
        for item in value or []:
            if isinstance(item, str):
                normalized.append(item)
            elif isinstance(item, dict):
                normalized.append(str(item.get("type") or item.get("action") or item))
        return normalized


class PageRelationship(BaseModel):
    from_url: str = Field(alias="from")
    to_url: str = Field(alias="to")
    relation: str

    model_config = {"populate_by_name": True}


class PageUnderstanding(BaseModel):
    """Combined Stage 2 result for a single page."""

    url: str
    title: str
    classification: PageClassification
    actions: list[str] = Field(default_factory=list)


class UnderstandingResult(BaseModel):
    pages: list[PageUnderstanding] = Field(default_factory=list)
    relationships: list[PageRelationship] = Field(default_factory=list)
