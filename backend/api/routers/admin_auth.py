"""Admin login/logout endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Header
from pydantic import BaseModel

from ..auth import login as do_login
from ..auth import logout as do_logout

router = APIRouter(prefix="/api/admin", tags=["admin-auth"])


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    token: str


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest) -> LoginResponse:
    token = do_login(req.password)
    return LoginResponse(token=token)


@router.post("/logout")
def logout(authorization: str | None = Header(default=None)) -> dict:
    if authorization and authorization.startswith("Bearer "):
        do_logout(authorization.removeprefix("Bearer ").strip())
    return {"status": "ok"}
