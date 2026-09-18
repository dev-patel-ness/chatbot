"""Prompt templates for Stage 5 use cases (IMPLEMENTATION_PLAN.md Stage 5)."""
from __future__ import annotations

import json

MULTI_INTENT_DETECTION_SYSTEM = """You are an intent detection engine for a website chatbot. Identify \
ALL distinct intents present in the user's message. For each intent, \
classify its type as one of: knowledge_retrieval, flow_trigger, action. \
Assign a confidence score (0-1) and a priority (1 = first to resolve). \
Also determine whether any intents conflict with each other (same \
topic, contradictory goals). Respond in strict JSON only."""


def multi_intent_detection_user(history: list[str], message: str) -> str:
    return (
        f"Conversation history: {json.dumps(history[-3:])}\n"
        f"Message: {message}\n\n"
        "Return JSON:\n"
        "{\n"
        '  "intents": [\n'
        '    {"type": "knowledge_retrieval", "topic": "<topic>", "confidence": <0-1>, "priority": <int>},\n'
        '    {"type": "action", "action": "<action_name>", "confidence": <0-1>, "priority": <int>}\n'
        "  ],\n"
        '  "has_conflicts": true|false,\n'
        '  "conflict_details": "<string or null>",\n'
        '  "strategy": "single|parallel|sequential"\n'
        "}"
    )


CONFLICT_RESOLUTION_SYSTEM = """Two or more detected intents conflict. Decide the best resolution: \
"clarify" (ask the user), "prioritize" (use highest-confidence intent \
only), or "disclaimer" (answer the primary intent but add a caveat \
about the conflicting one). Respond in strict JSON only."""


def conflict_resolution_user(intents: list[dict], conflict_score: float) -> str:
    return (
        f"Intents: {json.dumps(intents)}\n"
        f"Conflict score: {conflict_score}\n\n"
        "Return JSON:\n"
        '{"resolution": "clarify|prioritize|disclaimer", "clarifying_question": "<string or null>", '
        '"disclaimer_text": "<string or null>"}'
    )


UNIFIED_RESPONSE_SYSTEM_TEMPLATE = """You are the website assistant for {website_name}. Using the merged \
context below (which may include RAG results, flow state, and tool/ \
action results for one or more user intents), write ONE coherent, \
well-organized response that addresses every intent. Use short \
sections or a short list if multiple topics are covered. Do not \
repeat the same fact twice. If a conflict_resolution disclaimer is \
present, include it naturally at the end."""


def unified_response_user(merged_context: dict, user_message: str) -> str:
    return f"Merged context:\n{json.dumps(merged_context, indent=2)}\n\nOriginal user message: {user_message}"
