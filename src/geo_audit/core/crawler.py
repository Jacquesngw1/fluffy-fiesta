"""
Website crawler using Playwright (headless Chromium).

The Crawler visits a website up to `max_pages` pages, following internal links,
and returns a list of page data dictionaries containing the URL, HTML content,
response status, and response time.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)


class Crawler:
    """Asynchronous website crawler backed by Playwright."""

    def __init__(self, start_url: str, max_pages: int = 50) -> None:
        self.start_url = start_url.rstrip("/")
        self.max_pages = max_pages
        self._base_netloc = urlparse(start_url).netloc

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def crawl(self) -> list[dict[str, Any]]:
        """
        Crawl the website starting from *start_url*.

        Returns a list of page data dictionaries:
        {
            "url": str,
            "html": str,
            "status": int,
            "response_time_ms": float,
        }
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:
            raise RuntimeError(
                "Playwright is not installed. "
                "Run: pip install playwright && playwright install chromium"
            ) from exc

        pages: list[dict[str, Any]] = []
        visited: set[str] = set()
        queue: list[str] = [self.start_url]

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (compatible; GEOAuditBot/0.1; "
                    "+https://github.com/neuralis-black/geo-audit-tool)"
                )
            )
            try:
                while queue and len(pages) < self.max_pages:
                    url = queue.pop(0)
                    if url in visited:
                        continue
                    visited.add(url)

                    page_data = await self._fetch_page(context, url)
                    if page_data:
                        pages.append(page_data)
                        new_links = self._extract_internal_links(
                            page_data["html"], url
                        )
                        for link in new_links:
                            if link not in visited and link not in queue:
                                queue.append(link)
            finally:
                await context.close()
                await browser.close()

        logger.info("Crawled %d page(s) for %s", len(pages), self.start_url)
        return pages

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _fetch_page(
        self, context: Any, url: str
    ) -> dict[str, Any] | None:
        """Fetch a single page and return its data dict, or None on error."""
        page = None
        try:
            page = await context.new_page()
            start = time.monotonic()
            response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            elapsed_ms = (time.monotonic() - start) * 1000

            html = await page.content()
            status = response.status if response else 0

            return {
                "url": url,
                "html": html,
                "status": status,
                "response_time_ms": round(elapsed_ms, 2),
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to fetch %s: %s", url, exc)
            return None
        finally:
            if page:
                await page.close()

    def _extract_internal_links(self, html: str, base_url: str) -> list[str]:
        """Parse all internal <a href> links from *html* relative to *base_url*."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        links: list[str] = []
        for tag in soup.find_all("a", href=True):
            href = tag["href"].strip()
            # Skip anchors, mailto, javascript, etc.
            if href.startswith(("#", "mailto:", "tel:", "javascript:")):
                continue
            absolute = urljoin(base_url, href).split("#")[0].rstrip("/")
            if urlparse(absolute).netloc == self._base_netloc:
                links.append(absolute)
        return links
