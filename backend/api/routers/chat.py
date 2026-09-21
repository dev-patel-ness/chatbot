"""Public chat endpoint used by the embeddable widget (architecture.md §17) — no admin auth."""
from __future__ import annotations

import os

from fastapi import APIRouter
from pydantic import BaseModel

from conversations.db import (
    add_message,
    create_conversation,
    get_connection,
    get_messages,
    init_schema as init_conversations_schema,
    log_flow_execution,
    log_tool_execution,
)
from flows.db import init_schema as init_flows_schema
from knowledge.embeddings import BedrockEmbeddings
from knowledge.rag import RagEngine
from runtime.graph import build_runtime_graph
from runtime.nodes import RuntimeDeps
from safety.checker import SafetyChecker
from safety.db import init_schema as init_safety_schema
from tools.client import MockApiClient
from tools.executor import ToolExecutor
from understanding.bedrock_client import BedrockClient

router = APIRouter(tags=["chat"])

REGION = os.environ.get("AWS_REGION", "us-east-1")
CHAT_MODEL = os.environ.get("BEDROCK_CHAT_MODEL", "amazon.nova-pro-v1:0")
EMBEDDING_MODEL = os.environ.get("BEDROCK_EMBEDDING_MODEL", "amazon.titan-embed-text-v2:0")
MOCK_API_URL = os.environ.get("MOCK_API_URL", "http://127.0.0.1:8000")


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


@router.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    conn = get_connection()
    try:
        init_conversations_schema(conn)
        init_flows_schema(conn)
        init_safety_schema(conn)

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
                "conversation_id": conversation_id,
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


@router.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
