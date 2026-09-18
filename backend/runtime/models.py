"""Data models for Stage 5 — LangGraph Runtime + Multi-Intent Handling (architecture.md §11-12)."""
from __future__ import annotations

from pydantic import BaseModel, Field


class Intent(BaseModel):
    type: str  # knowledge_retrieval | flow_trigger | action
    topic: str | None = None
    action: str | None = None
    confidence: float = 0.5
    priority: int = 1


class IntentDetectionResult(BaseModel):
    intents: list[Intent] = Field(default_factory=list)
    has_conflicts: bool = False
    conflict_details: str | None = None
    strategy: str = "single"  # single | parallel | sequential


class ConflictResolution(BaseModel):
    resolution: str  # clarify | prioritize | disclaimer
    clarifying_question: str | None = None
    disclaimer_text: str | None = None


class NodeOutput(BaseModel):
    intent: Intent
    node: str  # rag | flow | tool
    text: str
    sources: list[str] = Field(default_factory=list)


class RuntimeResult(BaseModel):
    user_message: str
    intents: list[Intent]
    strategy: str
    has_conflicts: bool
    conflict_resolution: ConflictResolution | None = None
    node_outputs: list[NodeOutput] = Field(default_factory=list)
    final_response: str
    sources: list[str] = Field(default_factory=list)
