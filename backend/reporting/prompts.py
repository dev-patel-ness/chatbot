"""Prompt templates for Stage 8 reporting use cases (IMPLEMENTATION_PLAN.md Stage 8)."""
from __future__ import annotations

import json

FAQ_EXTRACTION_SYSTEM = """Analyze these user messages from many conversations and identify the \
top 10 most frequently asked topics/questions. Group similar \
phrasings together. Respond in strict JSON only."""


def faq_extraction_user(messages: list[str]) -> str:
    return (
        f"Messages: {json.dumps(messages)}\n\n"
        "Return JSON:\n"
        '{"top_topics": [{"topic": "<string>", "example_phrasings": ["...", "..."], '
        '"count_estimate": <int>}]}'
    )


CONVERSATION_SUMMARY_SYSTEM = """Summarize this conversation in 2-3 sentences for an internal admin \
dashboard. Include whether the user's goal was achieved and whether \
any flow or action was executed."""


def conversation_summary_user(transcript: str) -> str:
    return f"Conversation transcript: {transcript}"
