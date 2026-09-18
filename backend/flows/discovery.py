"""Orchestrates Stage 4 flow discovery from Stage 2 website-understanding output."""
from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path

import psycopg
from understanding.bedrock_client import BedrockClient
from understanding.models import UnderstandingResult

from .db import create_flow
from .models import Flow, FlowStep
from .prompts import (
    FLOW_DISCOVERY_SYSTEM,
    TRIGGER_EXPANSION_SYSTEM,
    flow_discovery_user,
    trigger_expansion_user,
)

logger = logging.getLogger(__name__)

# Actions that indicate a page is worth its own dedicated action-oriented flow.
_ACTION_TRIGGERED_TYPES = ("contact", "book_demo", "request_quote", "apply", "subscribe")


class FlowDiscoveryEngine:
    def __init__(self, client: BedrockClient) -> None:
        self.client = client

    def _propose_flow(self, section_name: str, pages: list[dict]) -> tuple[str, list[str], list[FlowStep]]:
        user_prompt = flow_discovery_user(section_name, pages)
        data = self.client.invoke_json(FLOW_DISCOVERY_SYSTEM, user_prompt)
        steps = [FlowStep.model_validate(s) for s in data.get("steps", [])]
        return data["flow_name"], data.get("trigger", []), steps

    def expand_triggers(self, flow_name: str, existing_triggers: list[str]) -> list[str]:
        user_prompt = trigger_expansion_user(flow_name, existing_triggers)
        data = self.client.invoke_json(TRIGGER_EXPANSION_SYSTEM, user_prompt)
        new_triggers = data if isinstance(data, list) else data.get("triggers", [])
        return list(dict.fromkeys(existing_triggers + [t for t in new_triggers if isinstance(t, str)]))

    def run(self, conn: psycopg.Connection, understanding_path: str | Path, website_id: str) -> list[Flow]:
        result = UnderstandingResult.model_validate_json(Path(understanding_path).read_text(encoding="utf-8"))

        groups: dict[str, list] = defaultdict(list)
        for page in result.pages:
            groups[page.classification.type].append(page)

        created: list[Flow] = []

        # One overview flow per page-type section (e.g. all "service" pages together).
        for section_name, pages in groups.items():
            payload = [{"title": p.title, "url": p.url, "actions": p.actions} for p in pages]
            try:
                flow_name, trigger, steps = self._propose_flow(section_name, payload)
                trigger = self.expand_triggers(flow_name, trigger)
                flow = create_flow(conn, website_id, flow_name, trigger, steps)
                created.append(flow)
                logger.info("Created section flow '%s' (%d steps)", flow.flow_name, len(flow.steps))
            except Exception:
                logger.exception("Failed to discover flow for section %s", section_name)

        # One dedicated action-oriented flow per page that supports contact/demo/etc.
        for page in result.pages:
            if not any(a in _ACTION_TRIGGERED_TYPES for a in page.actions):
                continue
            payload = [{"title": page.title, "url": page.url, "actions": page.actions}]
            try:
                flow_name, trigger, steps = self._propose_flow(page.title, payload)
                trigger = self.expand_triggers(flow_name, trigger)
                flow = create_flow(conn, website_id, flow_name, trigger, steps)
                created.append(flow)
                logger.info("Created page flow '%s' (%d steps)", flow.flow_name, len(flow.steps))
            except Exception:
                logger.exception("Failed to discover flow for page %s", page.url)

        return created
