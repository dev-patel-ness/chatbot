"""Background ingestion pipeline orchestrator for the Admin Portal.

Reuses the existing Stage 1-4 CLI modules unmodified by writing to a
per-website output directory, exactly like the CLIs do.
"""
from __future__ import annotations

import logging
import os

from flows.discovery import FlowDiscoveryEngine
from ingestion.crawler import WebCrawler
from ingestion.storage import save_crawl_result
from knowledge.db import get_connection
from knowledge.embeddings import BedrockEmbeddings
from knowledge.ingest import KnowledgeIngestor
from understanding.analyzer import WebsiteUnderstanding
from understanding.bedrock_client import BedrockClient
from understanding.storage import save_understanding_result

from .db import update_page_count, update_status

logger = logging.getLogger(__name__)

REGION = os.environ.get("AWS_REGION", "us-east-1")
CHAT_MODEL = os.environ.get("BEDROCK_CHAT_MODEL", "amazon.nova-pro-v1:0")
EMBEDDING_MODEL = os.environ.get("BEDROCK_EMBEDDING_MODEL", "amazon.titan-embed-text-v2:0")


def run_ingestion_pipeline(website_pk: int, website_id: str, url: str, max_pages: int, max_depth: int) -> None:
    """Runs crawl -> understand -> embed -> discover flows, updating status at each stage."""
    output_dir = f"./output/{website_id}"
    conn = get_connection()
    try:
        update_status(conn, website_pk, "crawling")
        crawler = WebCrawler(max_pages=max_pages, max_depth=max_depth)
        crawl_result = crawler.crawl(url)
        save_crawl_result(crawl_result, output_dir)
        update_page_count(conn, website_pk, len(crawl_result.discovered_urls))

        update_status(conn, website_pk, "understanding")
        llm_client = BedrockClient(model_id=CHAT_MODEL, region_name=REGION)
        understanding_result = WebsiteUnderstanding(llm_client).run(f"{output_dir}/pages")
        save_understanding_result(understanding_result, f"{output_dir}/understanding")

        update_status(conn, website_pk, "embedding")
        embeddings = BedrockEmbeddings(model_id=EMBEDDING_MODEL, region_name=REGION)
        KnowledgeIngestor(embeddings, conn).ingest(
            f"{output_dir}/pages", f"{output_dir}/understanding/understanding.json", website_id
        )

        update_status(conn, website_pk, "discovering_flows")
        FlowDiscoveryEngine(llm_client).run(
            conn, f"{output_dir}/understanding/understanding.json", website_id
        )

        update_status(conn, website_pk, "ready")
        logger.info("Ingestion pipeline complete for website_id=%s", website_id)
    except Exception as exc:
        logger.exception("Ingestion pipeline failed for website_id=%s", website_id)
        update_status(conn, website_pk, "failed", error_message=str(exc))
    finally:
        conn.close()
