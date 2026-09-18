"""Orchestrates Stage 6 action execution: select -> extract -> call -> summarize."""
from __future__ import annotations

import logging

from understanding.bedrock_client import BedrockClient

from .client import MockApiClient
from .models import ToolResult
from .prompts import (
    PARAMETER_EXTRACTION_SYSTEM,
    RESULT_SUMMARIZATION_SYSTEM,
    parameter_extraction_user,
    result_summarization_user,
)
from .registry import ACTIONS, select_action

logger = logging.getLogger(__name__)


class ToolExecutor:
    def __init__(self, llm_client: BedrockClient, api_client: MockApiClient) -> None:
        self.llm_client = llm_client
        self.api_client = api_client

    def execute(self, action_text: str, conversation: list[str]) -> ToolResult:
        action_key = select_action(action_text)
        if action_key is None:
            return ToolResult(
                action_key=None,
                text=f"I'm not able to perform '{action_text}' yet — please contact us directly for that request.",
            )

        action = ACTIONS[action_key]
        parameters: dict = {}

        if action["required_fields"]:
            system_prompt = PARAMETER_EXTRACTION_SYSTEM.format(
                action_name=action_key, required_fields=action["required_fields"]
            )
            user_prompt = parameter_extraction_user(conversation)
            data = self.llm_client.invoke_json(system_prompt, user_prompt)

            # Some models occasionally return fields at the top level instead of nested
            # under "parameters" — fall back to reading required fields directly.
            parameters = data.get("parameters") or {
                field: data.get(field) for field in action["required_fields"] if data.get(field)
            }
            missing = [f for f in action["required_fields"] if not parameters.get(f)]

            if missing:
                fields_text = ", ".join(missing)
                return ToolResult(
                    action_key=action_key,
                    text=f"To proceed with '{action_key.replace('_', ' ')}', could you please share your {fields_text}?",
                    needs_followup=True,
                )

        api_result = self.api_client.call(action["method"], action["path"], json_body=parameters or None)
        logger.info("Called %s %s -> %s", action["method"], action["path"], api_result)

        summary_user = result_summarization_user(action_key, api_result)
        summary_text = self.llm_client.invoke(RESULT_SUMMARIZATION_SYSTEM, summary_user, max_tokens=200)

        return ToolResult(action_key=action_key, text=summary_text, api_result=api_result)
