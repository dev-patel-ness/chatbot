"""RAG answer-generation prompt (IMPLEMENTATION_PLAN.md Stage 3, use case 3.4)."""
from __future__ import annotations

RAG_ANSWER_SYSTEM_TEMPLATE = """You are a helpful website assistant for {website_name}. Answer the \
user's question using ONLY the provided context chunks. If the \
answer is not present in the context, say you don't have that \
information and suggest contacting the company. Never invent facts. \
Always cite the source URL for factual claims."""


def rag_answer_user(question: str, chunks: list[dict]) -> str:
    context = "\n\n".join(f"[{c['url']}]\n{c['text']}" for c in chunks)
    return (
        f"Question: {question}\n\n"
        f"Context:\n{context}\n\n"
        'Answer concisely in 2-4 sentences, followed by a "Sources:" list of URLs used.'
    )
