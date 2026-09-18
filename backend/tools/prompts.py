"""Prompt templates for Stage 6 use cases (IMPLEMENTATION_PLAN.md Stage 6)."""
from __future__ import annotations

import json

PARAMETER_EXTRACTION_SYSTEM = """Extract the parameters required to call the "{action_name}" API from \
the conversation. Required fields: {required_fields}. If a field is \
missing, set it to null and add it to "missing_fields". Respond in \
strict JSON only, using EXACTLY this shape (parameters nested under \
the "parameters" key, one entry per required field):
{{"parameters": {{"<field>": "<value or null>"}}, "missing_fields": ["<field>", ...]}}"""


def parameter_extraction_user(conversation: list[str]) -> str:
    return f"Conversation: {json.dumps(conversation)}"


RESULT_SUMMARIZATION_SYSTEM = """Convert this raw API result into a short, friendly confirmation \
message for the user. Do not expose internal field names or raw JSON."""


def result_summarization_user(action_name: str, api_result: dict) -> str:
    return f"Action: {action_name}\nAPI result: {json.dumps(api_result)}"
