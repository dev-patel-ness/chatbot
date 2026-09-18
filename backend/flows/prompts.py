"""Prompt templates for Stage 4 use cases (IMPLEMENTATION_PLAN.md Stage 4)."""
from __future__ import annotations

import json

FLOW_DISCOVERY_SYSTEM = """You design conversational chatbot flows from website structure data. \
A flow has a name, a list of trigger phrases, and an ordered list of \
steps (show_options, retrieve_information, ask_followup, collect_input, \
call_action). Respond in strict JSON only."""


def flow_discovery_user(section_name: str, pages: list[dict]) -> str:
    return (
        f"Website section: {section_name}\n"
        f"Related pages: {json.dumps(pages)}\n\n"
        "Return JSON:\n"
        "{\n"
        '  "flow_name": "<string>",\n'
        '  "trigger": ["<phrase1>", "<phrase2>"],\n'
        '  "steps": [{"type": "<step_type>", "options": [...]}]\n'
        "}"
    )


TRIGGER_EXPANSION_SYSTEM = """Generate 5 additional natural-language phrases a real user might type \
to trigger the given flow. Keep them short and conversational. \
Respond as a JSON array of strings only."""


def trigger_expansion_user(flow_name: str, existing_triggers: list[str]) -> str:
    return f"Flow name: {flow_name}\nExisting triggers: {existing_triggers}"
