"""Knowledge-base test-query endpoint (Admin Portal debug tool)."""
from __future__ import annotations

import os

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from knowledge.db import get_connection, init_schema, search
from knowledge.embeddings import BedrockEmbeddings
from knowledge.rag import RagEngine
from understanding.bedrock_client import BedrockClient

from ..auth import require_admin

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"], dependencies=[Depends(require_admin)])

REGION = os.environ.get("AWS_REGION", "us-east-1")
CHAT_MODEL = os.environ.get("BEDROCK_CHAT_MODEL", "amazon.nova-pro-v1:0")
EMBEDDING_MODEL = os.environ.get("BEDROCK_EMBEDDING_MODEL", "amazon.titan-embed-text-v2:0")


class QueryRequest(BaseModel):
    website_id: str
    website_name: str = "Website"
    question: str
    top_k: int = 5


@router.post("/query")
def query(req: QueryRequest) -> dict:
    conn = get_connection()
    try:
        init_schema(conn)
        embeddings = BedrockEmbeddings(model_id=EMBEDDING_MODEL, region_name=REGION)
        llm_client = BedrockClient(model_id=CHAT_MODEL, region_name=REGION)

        query_embedding = embeddings.embed(req.question)
        retrieved = search(conn, query_embedding, req.website_id, top_k=req.top_k)

        rag_engine = RagEngine(embeddings, llm_client, website_name=req.website_name)
        answer = rag_engine.answer(conn, req.question, req.website_id, top_k=req.top_k)

        return {
            "answer": answer.answer,
            "sources": answer.sources,
            "retrieved_chunks": [c.model_dump() for c in retrieved],
        }
    finally:
        conn.close()
