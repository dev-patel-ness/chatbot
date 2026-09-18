"""Orchestrates Stage 2 website-understanding calls to AWS Bedrock."""
from __future__ import annotations

import logging
from pathlib import Path

from ingestion.models import PageData

from .bedrock_client import BedrockClient
from .models import (
    PageActions,
    PageClassification,
    PageRelationship,
    PageUnderstanding,
    UnderstandingResult,
)
from .prompts import (
    ACTION_IDENTIFICATION_SYSTEM,
    PAGE_CLASSIFICATION_SYSTEM,
    RELATIONSHIP_MAPPING_SYSTEM,
    action_identification_user,
    page_classification_user,
    relationship_mapping_user,
)

logger = logging.getLogger(__name__)

_CONTENT_EXCERPT_CHARS = 1500


class WebsiteUnderstanding:
    def __init__(self, client: BedrockClient) -> None:
        self.client = client

    def load_pages(self, pages_dir: str | Path) -> list[PageData]:
        pages_path = Path(pages_dir)
        pages: list[PageData] = []
        for json_file in sorted(pages_path.glob("*.json")):
            page = PageData.model_validate_json(json_file.read_text(encoding="utf-8"))
            if not page.error:
                pages.append(page)
        return pages

    def classify_page(self, page: PageData) -> PageClassification:
        user_prompt = page_classification_user(
            url=page.url,
            title=page.title,
            headings=page.headings[:15],
            content_excerpt=page.content[:_CONTENT_EXCERPT_CHARS],
        )
        data = self.client.invoke_json(PAGE_CLASSIFICATION_SYSTEM, user_prompt)
        return PageClassification.model_validate(data)

    def identify_actions(self, page: PageData, page_type: str) -> PageActions:
        user_prompt = action_identification_user(
            page_type=page_type,
            buttons=[b.text for b in page.buttons],
            forms=[f.model_dump() for f in page.forms],
            links=[l.text for l in page.links[:25]],
        )
        data = self.client.invoke_json(ACTION_IDENTIFICATION_SYSTEM, user_prompt)
        data.setdefault("page", page.title)
        return PageActions.model_validate(data)

    def map_relationships(self, pages: list[PageUnderstanding]) -> list[PageRelationship]:
        payload = [{"url": p.url, "title": p.title, "type": p.classification.type} for p in pages]
        data = self.client.invoke_json(RELATIONSHIP_MAPPING_SYSTEM, relationship_mapping_user(payload))
        relationships = data.get("relationships", []) if isinstance(data, dict) else data
        return [PageRelationship.model_validate(r) for r in relationships]

    def run(self, pages_dir: str | Path) -> UnderstandingResult:
        pages = self.load_pages(pages_dir)
        result = UnderstandingResult()

        for page in pages:
            try:
                classification = self.classify_page(page)
                actions = self.identify_actions(page, classification.type)
                result.pages.append(
                    PageUnderstanding(
                        url=page.url,
                        title=page.title,
                        classification=classification,
                        actions=actions.actions,
                    )
                )
                logger.info("Understood %s -> type=%s actions=%s", page.url, classification.type, actions.actions)
            except Exception:
                logger.exception("Failed to analyze page %s", page.url)

        if result.pages:
            try:
                result.relationships = self.map_relationships(result.pages)
            except Exception:
                logger.exception("Failed to map page relationships")

        return result
