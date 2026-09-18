"""Data models for Stage 8 — Conversation Persistence (architecture.md §15)."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class Conversation(BaseModel):
    id: int
    website_id: str
    started_at: datetime


class Message(BaseModel):
    id: int
    conversation_id: int
    role: str  # user | assistant
    content: str
    created_at: datetime


class FlowExecutionRecord(BaseModel):
    id: int
    conversation_id: int
    flow_name: str
    status: str
    created_at: datetime


class ToolExecutionRecord(BaseModel):
    id: int
    conversation_id: int
    tool_name: str
    result: str
    created_at: datetime
