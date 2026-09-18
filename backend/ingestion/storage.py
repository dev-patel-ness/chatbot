"""Persists crawl output to disk as a sitemap + one JSON file per page."""
from __future__ import annotations

import json
import re
from pathlib import Path

from .models import CrawlResult


def _slugify_url(url: str) -> str:
    slug = re.sub(r"^https?://", "", url)
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", slug).strip("_")
    return slug or "index"


def save_crawl_result(result: CrawlResult, output_dir: str | Path) -> Path:
    """Writes sitemap.json and pages/<slug>.json files. Returns the output dir."""
    output_path = Path(output_dir)
    pages_path = output_path / "pages"
    pages_path.mkdir(parents=True, exist_ok=True)

    for page in result.pages:
        filename = f"{_slugify_url(page.url)}.json"
        (pages_path / filename).write_text(
            page.model_dump_json(indent=2), encoding="utf-8"
        )

    sitemap = {
        "seed_url": result.seed_url,
        "discovered_urls": result.discovered_urls,
        "failed_urls": result.failed_urls,
        "total_pages": len(result.pages),
    }
    (output_path / "sitemap.json").write_text(
        json.dumps(sitemap, indent=2), encoding="utf-8"
    )

    return output_path
