"""Intent-level handlers that dispatch to RAG, Flow, or Tool (architecture.md §11-12)."""
from __future__ import annotations

import logging

import psycopg
from flows.db import list_flows
from knowledge.rag import RagEngine
from tools.executor import ToolExecutor

from .models import Intent, NodeOutput

logger = logging.getLogger(__name__)


def handle_rag(rag_engine: RagEngine, conn: psycopg.Connection, website_id: str, intent: Intent, extra_context: str = "") -> NodeOutput:
    question = intent.topic or "Tell me more"
    if extra_context:
        question = f"{extra_context}\n\n{question}"
    answer = rag_engine.answer(conn, question, website_id)
    return NodeOutput(intent=intent, node="rag", text=answer.answer, sources=answer.sources)


def handle_flow(conn: psycopg.Connection, website_id: str, intent: Intent) -> NodeOutput:
    published = [f for f in list_flows(conn, website_id) if f.published]
    query_text = (intent.topic or intent.action or "").lower()

    best_match = None
    best_score = 0
    for flow in published:
        haystack = " ".join(flow.trigger + [flow.flow_name]).lower()
        score = sum(1 for word in query_text.split() if word and word in haystack)
        if score > best_score:
            best_score = score
            best_match = flow

    if best_match is None:
        return NodeOutput(
            intent=intent,
            node="flow",
            text=f"No published flow currently matches '{query_text}'.",
        )

    first_step = best_match.steps[0] if best_match.steps else None
    options_text = f" Options: {first_step.options}" if first_step and first_step.options else ""
    text = f"Starting flow '{best_match.flow_name}'.{options_text}"
    return NodeOutput(intent=intent, node="flow", text=text)


def handle_tool(tool_executor: ToolExecutor, intent: Intent, conversation: list[str]) -> NodeOutput:
    action_text = intent.action or intent.topic or "requested action"
    result = tool_executor.execute(action_text, conversation)
    return NodeOutput(intent=intent, node="tool", text=result.text)
