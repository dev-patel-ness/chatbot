"""Persists safety check events for admin review (architecture.md §14)."""
from __future__ import annotations

import psycopg

from knowledge.db import get_connection  # reuse shared connection/DSN setup

__all__ = ["get_connection", "init_schema", "log_safety_event", "list_safety_events"]


def init_schema(conn: psycopg.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS safety_events (
            id BIGSERIAL PRIMARY KEY,
            conversation_id BIGINT,
            direction TEXT NOT NULL,
            message TEXT NOT NULL,
            reason TEXT,
            created_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )


def log_safety_event(
    conn: psycopg.Connection, conversation_id: int | None, direction: str, message: str, reason: str | None
) -> None:
    conn.execute(
        "INSERT INTO safety_events (conversation_id, direction, message, reason) VALUES (%s, %s, %s, %s)",
        (conversation_id, direction, message, reason),
    )


def list_safety_events(conn: psycopg.Connection, limit: int = 100) -> list[dict]:
    rows = conn.execute(
        "SELECT id, conversation_id, direction, message, reason, created_at "
        "FROM safety_events ORDER BY id DESC LIMIT %s",
        (limit,),
    ).fetchall()
    return [
        {"id": r[0], "conversation_id": r[1], "direction": r[2], "message": r[3], "reason": r[4], "created_at": r[5]}
        for r in rows
    ]
