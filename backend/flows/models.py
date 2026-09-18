"""Data models for Stage 4 — Flow Discovery + Editable Flows (architecture.md §9-10)."""
from __future__ import annotations

from pydantic import BaseModel, Field

ALLOWED_STEP_TYPES = ("show_options", "retrieve_information", "ask_followup", "collect_input", "call_action")


class FlowStep(BaseModel):
    type: str
    options: list[str] = Field(default_factory=list)


class Flow(BaseModel):
    id: int | None = None
    website_id: str
    flow_name: str
    trigger: list[str] = Field(default_factory=list)
    steps: list[FlowStep] = Field(default_factory=list)
    published: bool = False
