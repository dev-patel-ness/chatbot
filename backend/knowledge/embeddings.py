"""Bedrock Embeddings client (architecture.md §8, use case 3.2)."""
from __future__ import annotations

import json

import boto3

EMBEDDING_DIMENSIONS = 1024


class BedrockEmbeddings:
    def __init__(self, model_id: str = "amazon.titan-embed-text-v2:0", region_name: str = "us-east-1") -> None:
        self.model_id = model_id
        self._client = boto3.client("bedrock-runtime", region_name=region_name)

    def embed(self, text: str) -> list[float]:
        body = json.dumps({"inputText": text, "dimensions": EMBEDDING_DIMENSIONS, "normalize": True})
        response = self._client.invoke_model(
            modelId=self.model_id, body=body, contentType="application/json", accept="application/json"
        )
        payload = json.loads(response["body"].read())
        return payload["embedding"]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        # Titan embeddings only accept a single input per call.
        return [self.embed(text) for text in texts]
