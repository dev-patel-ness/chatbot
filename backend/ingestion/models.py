"""Data models for crawled/scraped website pages (architecture.md §6 schema)."""
from __future__ import annotations

from pydantic import BaseModel, Field


class LinkElement(BaseModel):
    text: str
    href: str


class ButtonElement(BaseModel):
    text: str


class FormField(BaseModel):
    name: str | None = None
    type: str | None = None
    placeholder: str | None = None


class FormElement(BaseModel):
    action: str | None = None
    method: str | None = None
    fields: list[FormField] = Field(default_factory=list)


class PageData(BaseModel):
    """Structured extraction result for a single crawled page."""

    url: str
    title: str = ""
    headings: list[str] = Field(default_factory=list)
    content: str = ""
    links: list[LinkElement] = Field(default_factory=list)
    buttons: list[ButtonElement] = Field(default_factory=list)
    forms: list[FormElement] = Field(default_factory=list)
    navigation: list[LinkElement] = Field(default_factory=list)
    depth: int = 0
    status_code: int | None = None
    error: str | None = None


class CrawlResult(BaseModel):
    """Summary of an entire crawl run."""

    seed_url: str
    pages: list[PageData] = Field(default_factory=list)
    discovered_urls: list[str] = Field(default_factory=list)
    failed_urls: list[str] = Field(default_factory=list)
