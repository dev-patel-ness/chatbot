"""Data models for Stage 6 tool execution."""
from __future__ import annotations

from pydantic import BaseModel


class ToolResult(BaseModel):
    action_key: str | None
    text: str
    needs_followup: bool = False
    api_result: dict | None = None
