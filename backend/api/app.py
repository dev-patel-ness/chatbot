"""FastAPI backend service — ties together Stages 1-8 + Admin Portal (architecture.md §2).

Usage:
    python -m api.main
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routers import admin_auth, chat, conversations, flows, knowledge, reporting, websites

app = FastAPI(title="Generic AI Website Chatbot Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # MVP only — restrict to known widget/admin origins in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serves widget/chatbot.js so embed snippets can reference this backend directly.
_WIDGET_DIR = Path(__file__).resolve().parent.parent.parent / "widget"
if _WIDGET_DIR.exists():
    app.mount("/widget", StaticFiles(directory=str(_WIDGET_DIR)), name="widget")

app.include_router(chat.router)
app.include_router(admin_auth.router)
app.include_router(websites.router)
app.include_router(flows.router)
app.include_router(knowledge.router)
app.include_router(conversations.router)
app.include_router(reporting.router)

