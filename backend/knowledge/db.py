"""PostgreSQL + pgvector storage layer (architecture.md §8)."""
from __future__ import annotations

import os

import psycopg
from pgvector import Vector
from pgvector.psycopg import register_vector

from .embeddings import EMBEDDING_DIMENSIONS
from .models import KnowledgeChunk, RetrievedChunk

DEFAULT_DSN = "postgresql://chatbot:chatbot_dev_password@localhost:5432/chatbot"


def get_connection(dsn: str | None = None) -> psycopg.Connection:
    conn = psycopg.connect(dsn or os.environ.get("CHATBOT_DB_DSN", DEFAULT_DSN), autocommit=True)
    conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    register_vector(conn)
    return conn


def init_schema(conn: psycopg.Connection) -> None:
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS knowledge_chunks (
            id BIGSERIAL PRIMARY KEY,
            website_id TEXT NOT NULL,
            url TEXT NOT NULL,
            page_title TEXT,
            section TEXT,
            content_type TEXT,
            text TEXT NOT NULL,
            embedding VECTOR({EMBEDDING_DIMENSIONS}) NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS knowledge_chunks_website_idx ON knowledge_chunks (website_id)"
    )


def clear_website(conn: psycopg.Connection, website_id: str) -> None:
    conn.execute("DELETE FROM knowledge_chunks WHERE website_id = %s", (website_id,))


def insert_chunk(conn: psycopg.Connection, chunk: KnowledgeChunk, embedding: list[float]) -> None:
    conn.execute(
        """
        INSERT INTO knowledge_chunks (website_id, url, page_title, section, content_type, text, embedding)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (chunk.website_id, chunk.url, chunk.page_title, chunk.section, chunk.content_type, chunk.text, Vector(embedding)),
    )


def search(
    conn: psycopg.Connection, query_embedding: list[float], website_id: str, top_k: int = 5
) -> list[RetrievedChunk]:
    rows = conn.execute(
        """
        SELECT url, page_title, section, content_type, website_id, text,
               1 - (embedding <=> %s) AS similarity
        FROM knowledge_chunks
        WHERE website_id = %s
        ORDER BY embedding <=> %s
        LIMIT %s
        """,
        (Vector(query_embedding), website_id, Vector(query_embedding), top_k),
    ).fetchall()

    return [
        RetrievedChunk(
            url=row[0],
            page_title=row[1],
            section=row[2],
            content_type=row[3],
            website_id=row[4],
            text=row[5],
            similarity=row[6],
        )
        for row in rows
    ]
