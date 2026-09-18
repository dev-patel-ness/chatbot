"""HTTP client for calling the mock actions API (architecture.md §13)."""
from __future__ import annotations

import requests


class MockApiClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000") -> None:
        self.base_url = base_url.rstrip("/")

    def call(self, method: str, path: str, json_body: dict | None = None) -> dict:
        url = f"{self.base_url}{path}"
        response = requests.request(method.upper(), url, json=json_body, timeout=10)
        if not response.ok:
            raise requests.exceptions.HTTPError(
                f"{response.status_code} error calling {method} {path}: {response.text}", response=response
            )
        return response.json()
