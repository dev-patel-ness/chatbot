"""FastAPI backend service — ties together Stages 1-8 for the chatbot widget (architecture.md §2).

Usage:
    python -m api.main
"""
from __future__ import annotations

import logging
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from conversations.db import (
    add_message,
    create_conversation,
    get_connection,
    get_conversation,
    get_messages,
    init_schema as init_conversations_schema,
    list_conversations,
    log_flow_execution,
    log_tool_execution,
)
from flows.db import init_schema as init_flows_schema
from knowledge.embeddings import BedrockEmbeddings
from knowledge.rag import RagEngine
from reporting.service import aggregate_metrics, extract_faqs, summarize_conversation
from runtime.graph import build_runtime_graph
from runtime.nodes import RuntimeDeps
from safety.checker import SafetyChecker
from tools.client import MockApiClient
from tools.executor import ToolExecutor
from understanding.bedrock_client import BedrockClient

logger = logging.getLogger(__name__)

REGION = os.environ.get("AWS_REGION", "us-east-1")
CHAT_MODEL = os.environ.get("BEDROCK_CHAT_MODEL", "amazon.nova-pro-v1:0")
EMBEDDING_MODEL = os.environ.get("BEDROCK_EMBEDDING_MODEL", "amazon.titan-embed-text-v2:0")
MOCK_API_URL = os.environ.get("MOCK_API_URL", "http://127.0.0.1:8000")

app = FastAPI(title="Generic AI Website Chatbot Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # MVP only — restrict to known widget origins in production
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    website_id: str
    website_name: str = "Ness"
    message: str
    conversation_id: int | None = None


class ChatResponse(BaseModel):
    conversation_id: int
    response: str
    sources: list[str] = []


def _build_deps(conn, website_id: str, website_name: str) -> RuntimeDeps:
    llm_client = BedrockClient(model_id=CHAT_MODEL, region_name=REGION)
    embeddings = BedrockEmbeddings(model_id=EMBEDDING_MODEL, region_name=REGION)
    rag_engine = RagEngine(embeddings, llm_client, website_name=website_name)
    tool_executor = ToolExecutor(llm_client, MockApiClient(MOCK_API_URL))
    safety_checker = SafetyChecker(llm_client)
    return RuntimeDeps(
        llm_client=llm_client,
        rag_engine=rag_engine,
        tool_executor=tool_executor,
        safety_checker=safety_checker,
        conn=conn,
        website_id=website_id,
        website_name=website_name,
    )


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    conn = get_connection()
    try:
        init_conversations_schema(conn)
        init_flows_schema(conn)

        conversation_id = req.conversation_id or create_conversation(conn, req.website_id)
        history = [m.content for m in get_messages(conn, conversation_id)]

        deps = _build_deps(conn, req.website_id, req.website_name)
        runtime = build_runtime_graph(deps)
        final_state = runtime.invoke(
            {
                "website_id": req.website_id,
                "website_name": req.website_name,
                "user_message": req.message,
                "history": history,
            }
        )

        add_message(conn, conversation_id, "user", req.message)
        add_message(conn, conversation_id, "assistant", final_state["final_response"])

        for output in final_state.get("node_outputs", []):
            intent = output.get("intent", {})
            label = intent.get("topic") or intent.get("action") or "unknown"
            if output.get("node") == "flow":
                log_flow_execution(conn, conversation_id, flow_name=label, status="handled")
            elif output.get("node") == "tool":
                log_tool_execution(conn, conversation_id, tool_name=label, result=output.get("text", ""))

        return ChatResponse(
            conversation_id=conversation_id,
            response=final_state["final_response"],
            sources=final_state.get("sources", []),
        )
    finally:
        conn.close()


@app.get("/api/conversations")
def api_list_conversations(website_id: str) -> list[dict]:
    conn = get_connection()
    try:
        init_conversations_schema(conn)
        return [c.model_dump() for c in list_conversations(conn, website_id)]
    finally:
        conn.close()


@app.get("/api/conversations/{conversation_id}")
def api_get_conversation(conversation_id: int) -> dict:
    conn = get_connection()
    try:
        init_conversations_schema(conn)
        conversation = get_conversation(conn, conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        messages = get_messages(conn, conversation_id)
        return {"conversation": conversation.model_dump(), "messages": [m.model_dump() for m in messages]}
    finally:
        conn.close()


@app.get("/api/reporting/summary")
def api_reporting_summary(website_id: str) -> dict:
    conn = get_connection()
    try:
        init_conversations_schema(conn)
        return aggregate_metrics(conn, website_id)
    finally:
        conn.close()


@app.get("/api/reporting/faqs")
def api_reporting_faqs(website_id: str) -> dict:
    conn = get_connection()
    try:
        init_conversations_schema(conn)
        llm_client = BedrockClient(model_id=CHAT_MODEL, region_name=REGION)
        return extract_faqs(llm_client, conn, website_id)
    finally:
        conn.close()


@app.get("/api/reporting/conversations/{conversation_id}/summary")
def api_reporting_conversation_summary(conversation_id: int) -> dict:
    conn = get_connection()
    try:
        init_conversations_schema(conn)
        llm_client = BedrockClient(model_id=CHAT_MODEL, region_name=REGION)
        return {"conversation_id": conversation_id, "summary": summarize_conversation(llm_client, conn, conversation_id)}
    finally:
        conn.close()


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
