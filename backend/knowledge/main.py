"""CLI entry point for Stage 3: Knowledge / RAG Pipeline.

Usage:
    python -m knowledge.main ingest --pages-dir ./output/pages \\
        --understanding ./output/understanding/understanding.json --website-id ness

    python -m knowledge.main ask --question "What Salesforce services does Ness offer?" --website-id ness
"""
from __future__ import annotations

import argparse
import logging
import sys

from understanding.bedrock_client import BedrockClient

from .db import clear_website, get_connection, init_schema
from .embeddings import BedrockEmbeddings
from .ingest import KnowledgeIngestor
from .rag import RagEngine


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Knowledge/RAG pipeline (Stage 3).")
    parser.add_argument("--region", default="us-east-1", help="AWS region with Bedrock access")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Chunk, embed, and store pages into pgvector")
    ingest_parser.add_argument("--pages-dir", default="./output/pages")
    ingest_parser.add_argument("--understanding", default="./output/understanding/understanding.json")
    ingest_parser.add_argument("--website-id", default="ness")
    ingest_parser.add_argument("--embedding-model", default="amazon.titan-embed-text-v2:0")
    ingest_parser.add_argument("--reset", action="store_true", help="Delete existing chunks for this website first")

    ask_parser = subparsers.add_parser("ask", help="Ask a question answered via RAG")
    ask_parser.add_argument("--question", required=True)
    ask_parser.add_argument("--website-id", default="ness")
    ask_parser.add_argument("--website-name", default="Ness")
    ask_parser.add_argument("--embedding-model", default="amazon.titan-embed-text-v2:0")
    ask_parser.add_argument("--answer-model", default="amazon.nova-pro-v1:0")
    ask_parser.add_argument("--top-k", type=int, default=5)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    conn = get_connection()
    init_schema(conn)

    if args.command == "ingest":
        if args.reset:
            clear_website(conn, args.website_id)
        embeddings = BedrockEmbeddings(model_id=args.embedding_model, region_name=args.region)
        ingestor = KnowledgeIngestor(embeddings, conn)
        stored = ingestor.ingest(args.pages_dir, args.understanding, args.website_id)
        print(f"Stored {stored} chunks for website_id={args.website_id}")

    elif args.command == "ask":
        embeddings = BedrockEmbeddings(model_id=args.embedding_model, region_name=args.region)
        client = BedrockClient(model_id=args.answer_model, region_name=args.region)
        engine = RagEngine(embeddings, client, website_name=args.website_name)
        result = engine.answer(conn, args.question, args.website_id, top_k=args.top_k)
        print(f"\nQ: {result.question}\n\nA: {result.answer}\n\nSources tracked: {result.sources}")

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
