"""Data models for Stage 3 — Knowledge / RAG Pipeline (architecture.md §8)."""
from __future__ import annotations

from pydantic import BaseModel, Field


class KnowledgeChunk(BaseModel):
    """A single retrievable chunk with metadata (architecture.md §8 schema)."""

    text: str
    url: str
    page_title: str = ""
    section: str = ""
    content_type: str = "other"
    website_id: str = "ness"


class RetrievedChunk(KnowledgeChunk):
    similarity: float


class RagAnswer(BaseModel):
    question: str
    answer: str
    sources: list[str] = Field(default_factory=list)
