"""RAG retrieval + answer generation (architecture.md §8, use cases 3.3 & 3.4)."""
from __future__ import annotations

import psycopg
from understanding.bedrock_client import BedrockClient

from .db import search
from .embeddings import BedrockEmbeddings
from .models import RagAnswer
from .prompts import RAG_ANSWER_SYSTEM_TEMPLATE, rag_answer_user


class RagEngine:
    def __init__(self, embeddings: BedrockEmbeddings, client: BedrockClient, website_name: str) -> None:
        self.embeddings = embeddings
        self.client = client
        self.website_name = website_name

    def answer(self, conn: psycopg.Connection, question: str, website_id: str, top_k: int = 5) -> RagAnswer:
        query_embedding = self.embeddings.embed(question)
        retrieved = search(conn, query_embedding, website_id, top_k=top_k)

        if not retrieved:
            return RagAnswer(
                question=question,
                answer="I don't have that information yet, please contact the company directly.",
                sources=[],
            )

        system_prompt = RAG_ANSWER_SYSTEM_TEMPLATE.format(website_name=self.website_name)
        user_prompt = rag_answer_user(question, [c.model_dump() for c in retrieved])
        answer_text = self.client.invoke(system_prompt, user_prompt, max_tokens=500)

        sources = list(dict.fromkeys(c.url for c in retrieved))
        return RagAnswer(question=question, answer=answer_text, sources=sources)
