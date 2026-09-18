"""Content chunking for the knowledge base (architecture.md §8, use case 3.1)."""
from __future__ import annotations

import re

from ingestion.models import PageData

from .models import KnowledgeChunk

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def chunk_text(text: str, target_chars: int = 800, overlap_chars: int = 150) -> list[str]:
    """Splits text into overlapping, sentence-aligned chunks of roughly target_chars."""
    sentences = _SENTENCE_SPLIT_RE.split(text.strip())
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        if not sentence:
            continue
        if len(current) + len(sentence) + 1 <= target_chars:
            current = f"{current} {sentence}".strip()
        else:
            if current:
                chunks.append(current)
            overlap = current[-overlap_chars:] if overlap_chars and current else ""
            current = f"{overlap} {sentence}".strip()

    if current:
        chunks.append(current)

    return chunks


def chunk_page(page: PageData, content_type: str = "other") -> list[KnowledgeChunk]:
    """Turns a scraped page into knowledge chunks tagged with source metadata."""
    section = page.headings[0] if page.headings else page.title
    raw_chunks = chunk_text(page.content)

    return [
        KnowledgeChunk(
            text=chunk,
            url=page.url,
            page_title=page.title,
            section=section,
            content_type=content_type,
        )
        for chunk in raw_chunks
        if chunk.strip()
    ]
