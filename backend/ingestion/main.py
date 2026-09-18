"""CLI entry point for Stage 1: Website Ingestion (Crawler + Scraper).

Usage:
    python -m ingestion.main --url https://www.ness.com --max-pages 25 --max-depth 2 --output ./output
"""
from __future__ import annotations

import argparse
import logging
import sys

from .crawler import WebCrawler
from .storage import save_crawl_result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Crawl and scrape a website (Stage 1 ingestion).")
    parser.add_argument("--url", required=True, help="Seed URL to start crawling from")
    parser.add_argument("--max-pages", type=int, default=25, help="Maximum number of pages to visit")
    parser.add_argument("--max-depth", type=int, default=2, help="Maximum link-following depth")
    parser.add_argument("--output", default="./output", help="Directory to write sitemap + page JSON files")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    crawler = WebCrawler(max_pages=args.max_pages, max_depth=args.max_depth)
    result = crawler.crawl(args.url)

    output_path = save_crawl_result(result, args.output)

    print(f"Crawled {len(result.discovered_urls)} pages, {len(result.failed_urls)} failed.")
    print(f"Output written to: {output_path.resolve()}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
