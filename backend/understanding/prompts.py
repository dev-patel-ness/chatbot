"""Prompt templates for Stage 2 use cases (IMPLEMENTATION_PLAN.md §Stage 2)."""
from __future__ import annotations

import json

PAGE_CLASSIFICATION_SYSTEM = """You are a website structure analyst. Classify web pages into one \
of these types only: service, industry, insight, about, contact, \
home, other. Respond with strict JSON, no explanations."""


def page_classification_user(url: str, title: str, headings: list[str], content_excerpt: str) -> str:
    return (
        f"URL: {url}\n"
        f"Title: {title}\n"
        f"Headings: {headings}\n"
        f"Content excerpt: {content_excerpt}\n\n"
        'Return JSON:\n{"page": "<title>", "type": "<one of the allowed types>", "confidence": <0-1>}'
    )


ACTION_IDENTIFICATION_SYSTEM = """You identify high-level user actions supported by a webpage based on \
its buttons, forms, and links. Choose ONLY from this fixed vocabulary: \
learn_more, contact, book_demo, request_quote, search, subscribe, \
download, apply, view_services, other. Only include an action if the \
buttons/forms/links actually support it. Do not list every navigation \
link as a separate action \u2014 collapse repeated navigation into \
"view_services" at most once. Respond in strict JSON as a FLAT ARRAY \
OF STRINGS only (e.g. ["contact", "view_services"]), never as objects."""


def action_identification_user(page_type: str, buttons: list[str], forms: list[dict], links: list[str]) -> str:
    return (
        f"Page type: {page_type}\n"
        f"Buttons: {buttons}\n"
        f"Forms (presence indicates a 'search' or 'contact' action): {forms}\n"
        f"Sample link labels (for context only, do not enumerate each one): {links[:8]}\n\n"
        'Return JSON exactly in this shape:\n{"page": "<title>", "actions": ["learn_more", "contact"]}'
    )



RELATIONSHIP_MAPPING_SYSTEM = """You map relationships between website pages using their URLs, \
navigation position, and content similarity. Output a strict JSON \
adjacency list. Do not invent pages that were not provided."""


def relationship_mapping_user(pages: list[dict]) -> str:
    return (
        f"Pages: {json.dumps(pages)}\n\n"
        'Return JSON:\n{"relationships": [{"from": "<url>", "to": "<url>", "relation": "parent|child|related"}]}'
    )
