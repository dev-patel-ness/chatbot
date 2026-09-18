"""Web Crawler (architecture.md §5) — discovers pages using Playwright.

Answers "which pages should I visit?" via breadth-first traversal of
same-domain links, then hands each rendered page to the ContentExtractor.
"""
from __future__ import annotations

import logging
from collections import deque
from urllib.parse import urldefrag, urlparse

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from .models import CrawlResult, PageData
from .scraper import ContentExtractor

logger = logging.getLogger(__name__)

_STATIC_ASSET_EXTENSIONS = (
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp",
    ".css", ".js", ".zip", ".xml", ".ico", ".woff", ".woff2",
)


class WebCrawler:
    """Breadth-first crawler restricted to the seed URL's domain."""

    def __init__(
        self,
        max_pages: int = 25,
        max_depth: int = 2,
        timeout_ms: int = 15_000,
        user_agent: str | None = None,
    ) -> None:
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.timeout_ms = timeout_ms
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ChatbotPlatformCrawler/1.0"
        )
        self.extractor = ContentExtractor()

    def crawl(self, seed_url: str) -> CrawlResult:
        seed_domain = urlparse(seed_url).netloc
        result = CrawlResult(seed_url=seed_url)

        visited: set[str] = set()
        queue: deque[tuple[str, int]] = deque([(self._normalize(seed_url), 0)])
        queued: set[str] = {self._normalize(seed_url)}

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(user_agent=self.user_agent)
            page = context.new_page()
            page.set_default_timeout(self.timeout_ms)

            while queue and len(visited) < self.max_pages:
                url, depth = queue.popleft()
                if url in visited:
                    continue
                visited.add(url)

                page_data = self._fetch_page(page, url, depth)
                result.pages.append(page_data)

                if page_data.error:
                    result.failed_urls.append(url)
                    continue

                result.discovered_urls.append(url)

                if depth >= self.max_depth:
                    continue

                for link in page_data.links + page_data.navigation:
                    normalized = self._normalize(link.href)
                    if not self._is_crawlable(normalized, seed_domain):
                        continue
                    if normalized in visited or normalized in queued:
                        continue
                    queued.add(normalized)
                    queue.append((normalized, depth + 1))

            context.close()
            browser.close()

        return result

    def _fetch_page(self, page, url: str, depth: int) -> PageData:
        try:
            response = page.goto(url, wait_until="networkidle")
            status_code = response.status if response else None
            html = page.content()
            page_data = self.extractor.extract(url, html, depth=depth, status_code=status_code)
            return page_data
        except PlaywrightError as exc:
            logger.warning("Failed to crawl %s: %s", url, exc)
            return PageData(url=url, depth=depth, error=str(exc))

    def _normalize(self, url: str) -> str:
        url, _ = urldefrag(url)
        return url.rstrip("/")

    def _is_crawlable(self, url: str, seed_domain: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        if parsed.netloc != seed_domain:
            return False
        if url.lower().endswith(_STATIC_ASSET_EXTENSIONS):
            return False
        return True
