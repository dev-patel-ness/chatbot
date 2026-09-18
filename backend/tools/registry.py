"""Registry mapping action intents to mock API endpoints (architecture.md §13)."""
from __future__ import annotations

ACTIONS: dict[str, dict] = {
    "book_demo": {"path": "/api/book-demo", "method": "POST", "required_fields": ["name", "email", "preferred_date"]},
    "contact": {"path": "/api/contact", "method": "POST", "required_fields": ["name", "email", "message"]},
    "view_services": {"path": "/api/services", "method": "GET", "required_fields": []},
}

_KEYWORD_MAP = {
    "book_demo": ("demo", "book a demo", "schedule"),
    "contact": ("contact", "reach out", "talk to", "quote", "get in touch"),
    "view_services": ("list services", "view services", "show services", "what services"),
}


def select_action(action_text: str) -> str | None:
    """Maps a free-form action phrase (from intent detection) to a known registry action."""
    text = (action_text or "").lower()
    for action_key, keywords in _KEYWORD_MAP.items():
        if any(keyword in text for keyword in keywords):
            return action_key
    return None
