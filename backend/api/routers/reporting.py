"""Reporting + safety-event review endpoints (Admin Portal)."""
from __future__ import annotations

import os

from fastapi import APIRouter, Depends

from conversations.db import get_connection, init_schema as init_conversations_schema
from reporting.service import aggregate_metrics, extract_faqs, summarize_conversation
from safety.db import init_schema as init_safety_schema, list_safety_events
from understanding.bedrock_client import BedrockClient

from ..auth import require_admin

router = APIRouter(prefix="/api/reporting", tags=["reporting"], dependencies=[Depends(require_admin)])

REGION = os.environ.get("AWS_REGION", "us-east-1")
CHAT_MODEL = os.environ.get("BEDROCK_CHAT_MODEL", "amazon.nova-pro-v1:0")


@router.get("/summary")
def summary(website_id: str) -> dict:
    conn = get_connection()
    try:
        init_conversations_schema(conn)
        return aggregate_metrics(conn, website_id)
    finally:
        conn.close()


@router.get("/faqs")
def faqs(website_id: str) -> dict:
    conn = get_connection()
    try:
        init_conversations_schema(conn)
        llm_client = BedrockClient(model_id=CHAT_MODEL, region_name=REGION)
        return extract_faqs(llm_client, conn, website_id)
    finally:
        conn.close()


@router.get("/conversations/{conversation_id}/summary")
def conversation_summary(conversation_id: int) -> dict:
    conn = get_connection()
    try:
        init_conversations_schema(conn)
        llm_client = BedrockClient(model_id=CHAT_MODEL, region_name=REGION)
        return {"conversation_id": conversation_id, "summary": summarize_conversation(llm_client, conn, conversation_id)}
    finally:
        conn.close()


@router.get("/safety-events")
def safety_events(limit: int = 100) -> list[dict]:
    conn = get_connection()
    try:
        init_safety_schema(conn)
        return list_safety_events(conn, limit=limit)
    finally:
        conn.close()
