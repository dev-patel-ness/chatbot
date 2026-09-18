"""Input/output safety checks that wrap the chatbot runtime (architecture.md §14)."""
from __future__ import annotations

import logging

from understanding.bedrock_client import BedrockClient

from .models import DEFAULT_UNSAFE_FALLBACK, InputSafetyResult, OutputSafetyResult
from .prompts import (
    INPUT_SAFETY_SYSTEM,
    OUTPUT_SAFETY_SYSTEM,
    input_safety_user,
    output_safety_user,
)

logger = logging.getLogger(__name__)


class SafetyChecker:
    def __init__(self, llm_client: BedrockClient) -> None:
        self.llm_client = llm_client

    def check_input(self, message: str) -> InputSafetyResult:
        data = self.llm_client.invoke_json(INPUT_SAFETY_SYSTEM, input_safety_user(message))
        result = InputSafetyResult.model_validate(data)
        if not result.is_safe:
            logger.warning("Input flagged UNSAFE: %s (reason=%s)", message, result.reason)
        return result

    def check_output(self, draft_response: str) -> OutputSafetyResult:
        try:
            data = self.llm_client.invoke_json(OUTPUT_SAFETY_SYSTEM, output_safety_user(draft_response))
            result = OutputSafetyResult.model_validate(data)
        except Exception:
            logger.exception("Output safety check failed to parse; failing safe with fallback")
            return OutputSafetyResult(is_safe=False, final_response=DEFAULT_UNSAFE_FALLBACK)
        if not result.is_safe:
            logger.warning("Output flagged UNSAFE, replacing with fallback")
        return result
