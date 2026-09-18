"""PostgreSQL storage + CRUD for conversations (architecture.md §15)."""
from __future__ import annotations

import psycopg

from knowledge.db import get_connection  # reuse shared connection/DSN setup

from .models import Conversation, FlowExecutionRecord, Message, ToolExecutionRecord

__all__ = ["get_connection", "init_schema", "create_conversation", "add_message", "get_messages"]


def init_schema(conn: psycopg.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id BIGSERIAL PRIMARY KEY,
            website_id TEXT NOT NULL,
            started_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id BIGSERIAL PRIMARY KEY,
            conversation_id BIGINT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS flow_executions (
            id BIGSERIAL PRIMARY KEY,
            conversation_id BIGINT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
            flow_name TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tool_executions (
            id BIGSERIAL PRIMARY KEY,
            conversation_id BIGINT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
            tool_name TEXT NOT NULL,
            result TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS messages_conversation_idx ON messages (conversation_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS conversations_website_idx ON conversations (website_id)")


def create_conversation(conn: psycopg.Connection, website_id: str) -> int:
    row = conn.execute(
        "INSERT INTO conversations (website_id) VALUES (%s) RETURNING id", (website_id,)
    ).fetchone()
    return row[0]


def add_message(conn: psycopg.Connection, conversation_id: int, role: str, content: str) -> None:
    conn.execute(
        "INSERT INTO messages (conversation_id, role, content) VALUES (%s, %s, %s)",
        (conversation_id, role, content),
    )


def get_messages(conn: psycopg.Connection, conversation_id: int) -> list[Message]:
    rows = conn.execute(
        "SELECT id, conversation_id, role, content, created_at FROM messages "
        "WHERE conversation_id = %s ORDER BY id",
        (conversation_id,),
    ).fetchall()
    return [Message(id=r[0], conversation_id=r[1], role=r[2], content=r[3], created_at=r[4]) for r in rows]


def log_flow_execution(conn: psycopg.Connection, conversation_id: int, flow_name: str, status: str = "started") -> None:
    conn.execute(
        "INSERT INTO flow_executions (conversation_id, flow_name, status) VALUES (%s, %s, %s)",
        (conversation_id, flow_name, status),
    )


def log_tool_execution(conn: psycopg.Connection, conversation_id: int, tool_name: str, result: str) -> None:
    conn.execute(
        "INSERT INTO tool_executions (conversation_id, tool_name, result) VALUES (%s, %s, %s)",
        (conversation_id, tool_name, result),
    )


def list_conversations(conn: psycopg.Connection, website_id: str) -> list[Conversation]:
    rows = conn.execute(
        "SELECT id, website_id, started_at FROM conversations WHERE website_id = %s ORDER BY id DESC",
        (website_id,),
    ).fetchall()
    return [Conversation(id=r[0], website_id=r[1], started_at=r[2]) for r in rows]


def get_conversation(conn: psycopg.Connection, conversation_id: int) -> Conversation | None:
    row = conn.execute(
        "SELECT id, website_id, started_at FROM conversations WHERE id = %s", (conversation_id,)
    ).fetchone()
    return Conversation(id=row[0], website_id=row[1], started_at=row[2]) if row else None
