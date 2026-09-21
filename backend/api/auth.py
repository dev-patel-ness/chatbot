"""Simple admin authentication for the Admin Portal (password + in-memory session token)."""
from __future__ import annotations

import os
import secrets

from fastapi import Header, HTTPException

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

# In-memory session store — resets on server restart. Fine for a single-instance MVP.
_valid_tokens: set[str] = set()


def login(password: str) -> str:
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid password")
    token = secrets.token_urlsafe(32)
    _valid_tokens.add(token)
    return token


def logout(token: str) -> None:
    _valid_tokens.discard(token)


def require_admin(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing admin token")
    token = authorization.removeprefix("Bearer ").strip()
    if token not in _valid_tokens:
        raise HTTPException(status_code=401, detail="Invalid or expired admin token")
    return token
