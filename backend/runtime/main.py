"""CLI entry point for Stage 5+7: LangGraph Runtime + Multi-Intent Detection & Safety.

Usage:
    python -m runtime.main --region us-east-1 ask --message "Tell me about Salesforce services and book a demo" \\
        --website-id ness --website-name Ness
"""
from __future__ import annotations

import argparse
import json
import logging
import sys

from knowledge.db import get_connection
from knowledge.embeddings import BedrockEmbeddings
from knowledge.rag import RagEngine
from understanding.bedrock_client import BedrockClient
from tools.client import MockApiClient
from tools.executor import ToolExecutor
from safety.checker import SafetyChecker

from .graph import build_runtime_graph
from .nodes import RuntimeDeps


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LangGraph multi-intent chatbot runtime (Stage 5).")
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--verbose", action="store_true")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ask_p = subparsers.add_parser("ask", help="Send one message through the runtime")
    ask_p.add_argument("--message", required=True)
    ask_p.add_argument("--website-id", default="ness")
    ask_p.add_argument("--website-name", default="Ness")
    ask_p.add_argument("--model", default="amazon.nova-pro-v1:0")
    ask_p.add_argument("--embedding-model", default="amazon.titan-embed-text-v2:0")
    ask_p.add_argument("--history", default="", help="Optional prior turns, separated by '||'")
    ask_p.add_argument("--mock-api-url", default="http://127.0.0.1:8000")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if args.command == "ask":
        conn = get_connection()
        llm_client = BedrockClient(model_id=args.model, region_name=args.region)
        embeddings = BedrockEmbeddings(model_id=args.embedding_model, region_name=args.region)
        rag_engine = RagEngine(embeddings, llm_client, website_name=args.website_name)
        tool_executor = ToolExecutor(llm_client, MockApiClient(args.mock_api_url))
        safety_checker = SafetyChecker(llm_client)

        deps = RuntimeDeps(
            llm_client=llm_client,
            rag_engine=rag_engine,
            tool_executor=tool_executor,
            safety_checker=safety_checker,
            conn=conn,
            website_id=args.website_id,
            website_name=args.website_name,
        )
        runtime = build_runtime_graph(deps)

        history = [h for h in args.history.split("||") if h] if args.history else []
        final_state = runtime.invoke({
            "website_id": args.website_id,
            "website_name": args.website_name,
            "user_message": args.message,
            "history": history,
        })

        print(f"\nUser: {args.message}\n")
        if final_state.get("input_blocked"):
            print("--- Input Safety ---")
            print("BLOCKED: message failed the input safety check.")
        else:
            print("--- Detected intents ---")
            print(json.dumps(final_state["intent_result"], indent=2))
            if final_state.get("conflict_resolution"):
                print("\n--- Conflict resolution ---")
                print(json.dumps(final_state["conflict_resolution"], indent=2))
        print("\n--- Final response ---")
        print(final_state["final_response"])
        print(f"\nSources: {final_state.get('sources', [])}")

        conn.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
