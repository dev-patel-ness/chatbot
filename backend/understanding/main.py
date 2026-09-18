"""CLI entry point for Stage 2: Website Understanding.

Usage:
    python -m understanding.main --pages-dir ./output/pages --output ./output/understanding \\
        --model amazon.nova-pro-v1:0 --region us-east-1
"""
from __future__ import annotations

import argparse
import logging
import sys

from .analyzer import WebsiteUnderstanding
from .bedrock_client import BedrockClient
from .storage import save_understanding_result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze crawled pages via AWS Bedrock (Stage 2 understanding).")
    parser.add_argument("--pages-dir", default="./output/pages", help="Directory of Stage 1 page JSON files")
    parser.add_argument("--output", default="./output/understanding", help="Directory to write understanding.json")
    parser.add_argument("--model", default="amazon.nova-pro-v1:0", help="Bedrock model ID")
    parser.add_argument("--region", default="us-east-1", help="AWS region with Bedrock access")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    client = BedrockClient(model_id=args.model, region_name=args.region)
    understanding = WebsiteUnderstanding(client)
    result = understanding.run(args.pages_dir)

    output_path = save_understanding_result(result, args.output)

    print(f"Understood {len(result.pages)} pages, mapped {len(result.relationships)} relationships.")
    print(f"Output written to: {output_path.resolve()}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
