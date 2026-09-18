"""Ingests Stage 1 pages + Stage 2 understanding into the pgvector knowledge base."""
from __future__ import annotations

import logging
from pathlib import Path

import psycopg
from ingestion.models import PageData
from understanding.models import UnderstandingResult

from .chunking import chunk_page
from .db import insert_chunk
from .embeddings import BedrockEmbeddings
from .models import KnowledgeChunk

logger = logging.getLogger(__name__)


def _load_content_types(understanding_path: str | Path) -> dict[str, str]:
    path = Path(understanding_path)
    if not path.exists():
        return {}
    result = UnderstandingResult.model_validate_json(path.read_text(encoding="utf-8"))
    return {p.url: p.classification.type for p in result.pages}


def _load_pages(pages_dir: str | Path) -> list[PageData]:
    pages = []
    for json_file in sorted(Path(pages_dir).glob("*.json")):
        page = PageData.model_validate_json(json_file.read_text(encoding="utf-8"))
        if not page.error:
            pages.append(page)
    return pages


class KnowledgeIngestor:
    def __init__(self, embeddings: BedrockEmbeddings, conn: psycopg.Connection) -> None:
        self.embeddings = embeddings
        self.conn = conn

    def ingest(self, pages_dir: str | Path, understanding_path: str | Path, website_id: str) -> int:
        content_types = _load_content_types(understanding_path)
        pages = _load_pages(pages_dir)

        stored = 0
        for page in pages:
            content_type = content_types.get(page.url, "other")
            chunks: list[KnowledgeChunk] = chunk_page(page, content_type=content_type)
            for chunk in chunks:
                chunk.website_id = website_id
                embedding = self.embeddings.embed(chunk.text)
                insert_chunk(self.conn, chunk, embedding)
                stored += 1
            logger.info("Ingested %s -> %d chunks", page.url, len(chunks))

        return stored
