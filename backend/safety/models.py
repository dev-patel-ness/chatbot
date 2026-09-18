"""Data models for Stage 7 — Safety Layer (architecture.md §14)."""
from __future__ import annotations

from pydantic import BaseModel

DEFAULT_UNSAFE_FALLBACK = (
    "I can't provide internal instructions, but I can help you with information about this website."
)


class InputSafetyResult(BaseModel):
    classification: str  # SAFE | UNSAFE
    reason: str | None = None

    @property
    def is_safe(self) -> bool:
        return self.classification.upper() == "SAFE"


class OutputSafetyResult(BaseModel):
    is_safe: bool
    final_response: str
