"""Runs the mock actions API with uvicorn: python -m mock_api.main"""
from __future__ import annotations

import uvicorn

if __name__ == "__main__":
    uvicorn.run("mock_api.app:app", host="127.0.0.1", port=8000, reload=False)
