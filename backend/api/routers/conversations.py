"""Conversation viewer endpoints (Admin Portal)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from conversations.db import get_connection, get_conversation, get_messages, init_schema, list_conversations

from ..auth import require_admin

router = APIRouter(prefix="/api/conversations", tags=["conversations"], dependencies=[Depends(require_admin)])


@router.get("")
def list_all(website_id: str) -> list[dict]:
    conn = get_connection()
    try:
        init_schema(conn)
        return [c.model_dump() for c in list_conversations(conn, website_id)]
    finally:
        conn.close()


@router.get("/{conversation_id}")
def get_one(conversation_id: int) -> dict:
    conn = get_connection()
    try:
        init_schema(conn)
        conversation = get_conversation(conn, conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        messages = get_messages(conn, conversation_id)
        return {"conversation": conversation.model_dump(), "messages": [m.model_dump() for m in messages]}
    finally:
        conn.close()
