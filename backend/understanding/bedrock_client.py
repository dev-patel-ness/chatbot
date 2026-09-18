"""Thin wrapper around AWS Bedrock's Converse API (model-agnostic)."""
from __future__ import annotations

import json
import logging
import re

import boto3

logger = logging.getLogger(__name__)

_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


class BedrockClient:
    def __init__(self, model_id: str, region_name: str = "us-east-1") -> None:
        self.model_id = model_id
        self._client = boto3.client("bedrock-runtime", region_name=region_name)

    def invoke(self, system_prompt: str, user_prompt: str, max_tokens: int = 800, temperature: float = 0.2) -> str:
        response = self._client.converse(
            modelId=self.model_id,
            system=[{"text": system_prompt}],
            messages=[{"role": "user", "content": [{"text": user_prompt}]}],
            inferenceConfig={"maxTokens": max_tokens, "temperature": temperature},
        )
        return response["output"]["message"]["content"][0]["text"]

    def invoke_json(self, system_prompt: str, user_prompt: str, max_tokens: int = 800) -> dict | list:
        """Invokes the model and parses the response as JSON, tolerating markdown fences."""
        raw_text = self.invoke(system_prompt, user_prompt, max_tokens=max_tokens)
        cleaned = _JSON_FENCE_RE.sub("", raw_text).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.error("Failed to parse model output as JSON: %s", raw_text)
            raise
