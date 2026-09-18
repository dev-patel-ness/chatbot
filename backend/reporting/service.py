"""Conversation-level analytics (architecture.md §16)."""
from __future__ import annotations

import psycopg
from understanding.bedrock_client import BedrockClient

from conversations.db import get_messages

from .prompts import (
    CONVERSATION_SUMMARY_SYSTEM,
    FAQ_EXTRACTION_SYSTEM,
    conversation_summary_user,
    faq_extraction_user,
)


def aggregate_metrics(conn: psycopg.Connection, website_id: str) -> dict:
    total_conversations = conn.execute(
        "SELECT COUNT(*) FROM conversations WHERE website_id = %s", (website_id,)
    ).fetchone()[0]

    total_messages = conn.execute(
        """
        SELECT COUNT(*) FROM messages m
        JOIN conversations c ON c.id = m.conversation_id
        WHERE c.website_id = %s
        """,
        (website_id,),
    ).fetchone()[0]

    avg_messages_per_conversation = (total_messages / total_conversations) if total_conversations else 0

    most_used_flows = conn.execute(
        """
        SELECT fe.flow_name, COUNT(*) as uses
        FROM flow_executions fe
        JOIN conversations c ON c.id = fe.conversation_id
        WHERE c.website_id = %s
        GROUP BY fe.flow_name
        ORDER BY uses DESC
        LIMIT 5
        """,
        (website_id,),
    ).fetchall()

    most_used_tools = conn.execute(
        """
        SELECT te.tool_name, COUNT(*) as uses
        FROM tool_executions te
        JOIN conversations c ON c.id = te.conversation_id
        WHERE c.website_id = %s
        GROUP BY te.tool_name
        ORDER BY uses DESC
        LIMIT 5
        """,
        (website_id,),
    ).fetchall()

    return {
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "average_messages_per_conversation": round(avg_messages_per_conversation, 2),
        "most_used_flows": [{"flow_name": r[0], "uses": r[1]} for r in most_used_flows],
        "most_used_tools": [{"tool_name": r[0], "uses": r[1]} for r in most_used_tools],
    }


def extract_faqs(llm_client: BedrockClient, conn: psycopg.Connection, website_id: str, sample_size: int = 100) -> dict:
    rows = conn.execute(
        """
        SELECT m.content FROM messages m
        JOIN conversations c ON c.id = m.conversation_id
        WHERE c.website_id = %s AND m.role = 'user'
        ORDER BY m.id DESC LIMIT %s
        """,
        (website_id, sample_size),
    ).fetchall()
    messages = [r[0] for r in rows]
    if not messages:
        return {"top_topics": []}
    return llm_client.invoke_json(FAQ_EXTRACTION_SYSTEM, faq_extraction_user(messages))


def summarize_conversation(llm_client: BedrockClient, conn: psycopg.Connection, conversation_id: int) -> str:
    messages = get_messages(conn, conversation_id)
    transcript = "\n".join(f"{m.role}: {m.content}" for m in messages)
    return llm_client.invoke(CONVERSATION_SUMMARY_SYSTEM, conversation_summary_user(transcript), max_tokens=200)
