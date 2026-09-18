"""CLI entry point for Stage 8 reporting.

Usage:
    python -m reporting.main summary --website-id ness
    python -m reporting.main --region us-east-1 faqs --website-id ness
    python -m reporting.main --region us-east-1 conversation --conversation-id 1
"""
from __future__ import annotations

import argparse
import json
import logging
import sys

from conversations.db import get_connection, init_schema as init_conversations_schema
from flows.db import init_schema as init_flows_schema
from understanding.bedrock_client import BedrockClient

from .service import aggregate_metrics, extract_faqs, summarize_conversation


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Conversation reporting (Stage 8).")
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--model", default="amazon.nova-pro-v1:0")
    subparsers = parser.add_subparsers(dest="command", required=True)

    summary_p = subparsers.add_parser("summary", help="Show aggregate metrics")
    summary_p.add_argument("--website-id", default="ness")

    faqs_p = subparsers.add_parser("faqs", help="Extract top FAQs across conversations")
    faqs_p.add_argument("--website-id", default="ness")

    conv_p = subparsers.add_parser("conversation", help="Summarize a single conversation")
    conv_p.add_argument("--conversation-id", type=int, required=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    conn = get_connection()
    init_conversations_schema(conn)
    init_flows_schema(conn)

    if args.command == "summary":
        print(json.dumps(aggregate_metrics(conn, args.website_id), indent=2))

    elif args.command == "faqs":
        client = BedrockClient(model_id=args.model, region_name=args.region)
        print(json.dumps(extract_faqs(client, conn, args.website_id), indent=2))

    elif args.command == "conversation":
        client = BedrockClient(model_id=args.model, region_name=args.region)
        print(summarize_conversation(client, conn, args.conversation_id))

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
