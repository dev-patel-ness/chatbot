"""PostgreSQL storage + CRUD for onboarded websites (Admin Portal)."""
from __future__ import annotations

import re
from urllib.parse import urlparse

import psycopg

from knowledge.db import get_connection  # reuse shared connection/DSN setup

from .models import Website

__all__ = ["get_connection", "init_schema", "create_website", "list_websites", "get_website", "delete_website"]


def init_schema(conn: psycopg.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS websites (
            id BIGSERIAL PRIMARY KEY,
            website_id TEXT UNIQUE NOT NULL,
            url TEXT NOT NULL,
            name TEXT NOT NULL,
            max_pages INTEGER NOT NULL DEFAULT 25,
            max_depth INTEGER NOT NULL DEFAULT 2,
            status TEXT NOT NULL DEFAULT 'pending',
            error_message TEXT,
            page_count INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )


def slugify_website_id(conn: psycopg.Connection, url: str) -> str:
    domain = urlparse(url).netloc or url
    slug = re.sub(r"^www\.", "", domain)
    slug = re.sub(r"[^a-z0-9]+", "_", slug.lower()).strip("_") or "site"

    candidate = slug
    suffix = 1
    while conn.execute("SELECT 1 FROM websites WHERE website_id = %s", (candidate,)).fetchone():
        suffix += 1
        candidate = f"{slug}_{suffix}"
    return candidate


def _row_to_website(row: tuple) -> Website:
    return Website(
        id=row[0], website_id=row[1], url=row[2], name=row[3], max_pages=row[4], max_depth=row[5],
        status=row[6], error_message=row[7], page_count=row[8], created_at=row[9], updated_at=row[10],
    )


_COLUMNS = "id, website_id, url, name, max_pages, max_depth, status, error_message, page_count, created_at, updated_at"


def create_website(conn: psycopg.Connection, url: str, name: str, max_pages: int, max_depth: int) -> Website:
    website_id = slugify_website_id(conn, url)
    row = conn.execute(
        f"""
        INSERT INTO websites (website_id, url, name, max_pages, max_depth, status)
        VALUES (%s, %s, %s, %s, %s, 'pending')
        RETURNING {_COLUMNS}
        """,
        (website_id, url, name, max_pages, max_depth),
    ).fetchone()
    return _row_to_website(row)


def list_websites(conn: psycopg.Connection) -> list[Website]:
    rows = conn.execute(f"SELECT {_COLUMNS} FROM websites ORDER BY id DESC").fetchall()
    return [_row_to_website(row) for row in rows]


def get_website(conn: psycopg.Connection, website_pk: int) -> Website | None:
    row = conn.execute(f"SELECT {_COLUMNS} FROM websites WHERE id = %s", (website_pk,)).fetchone()
    return _row_to_website(row) if row else None


def get_website_by_website_id(conn: psycopg.Connection, website_id: str) -> Website | None:
    row = conn.execute(f"SELECT {_COLUMNS} FROM websites WHERE website_id = %s", (website_id,)).fetchone()
    return _row_to_website(row) if row else None


def update_status(conn: psycopg.Connection, website_pk: int, status: str, error_message: str | None = None) -> None:
    conn.execute(
        "UPDATE websites SET status = %s, error_message = %s, updated_at = now() WHERE id = %s",
        (status, error_message, website_pk),
    )


def update_page_count(conn: psycopg.Connection, website_pk: int, page_count: int) -> None:
    conn.execute("UPDATE websites SET page_count = %s, updated_at = now() WHERE id = %s", (page_count, website_pk))


def delete_website(conn: psycopg.Connection, website_pk: int) -> None:
    conn.execute("DELETE FROM websites WHERE id = %s", (website_pk,))
