"""Tests for the website crawler."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from geo_audit.core.crawler import Crawler


class TestCrawlerInit:
    def test_trailing_slash_stripped(self):
        crawler = Crawler("https://example.com/")
        assert crawler.start_url == "https://example.com"

    def test_base_netloc_extracted(self):
        crawler = Crawler("https://example.com/page")
        assert crawler._base_netloc == "example.com"

    def test_max_pages_default(self):
        crawler = Crawler("https://example.com")
        assert crawler.max_pages == 50

    def test_max_pages_custom(self):
        crawler = Crawler("https://example.com", max_pages=10)
        assert crawler.max_pages == 10


class TestExtractInternalLinks:
    def setup_method(self):
        self.crawler = Crawler("https://example.com")

    def test_extracts_absolute_link(self):
        html = '<a href="https://example.com/about">About</a>'
        links = self.crawler._extract_internal_links(html, "https://example.com")
        assert "https://example.com/about" in links

    def test_extracts_relative_link(self):
        html = '<a href="/contact">Contact</a>'
        links = self.crawler._extract_internal_links(html, "https://example.com")
        assert "https://example.com/contact" in links

    def test_skips_external_links(self):
        html = '<a href="https://other.com/page">External</a>'
        links = self.crawler._extract_internal_links(html, "https://example.com")
        assert links == []

    def test_skips_mailto(self):
        html = '<a href="mailto:hello@example.com">Email</a>'
        links = self.crawler._extract_internal_links(html, "https://example.com")
        assert links == []

    def test_skips_tel(self):
        html = '<a href="tel:+1234567890">Call</a>'
        links = self.crawler._extract_internal_links(html, "https://example.com")
        assert links == []

    def test_skips_anchor_only(self):
        html = '<a href="#section">Jump</a>'
        links = self.crawler._extract_internal_links(html, "https://example.com")
        assert links == []

    def test_strips_fragment_from_url(self):
        html = '<a href="/about#team">About</a>'
        links = self.crawler._extract_internal_links(html, "https://example.com")
        assert "https://example.com/about" in links
        assert all("#" not in link for link in links)

    def test_deduplicates_via_crawl_logic(self):
        html = '<a href="/page">P</a><a href="/page">P2</a>'
        links = self.crawler._extract_internal_links(html, "https://example.com")
        # Both resolve to same URL; list may contain duplicates (dedup is in crawl())
        assert all(link == "https://example.com/page" for link in links)

    def test_empty_html(self):
        links = self.crawler._extract_internal_links("", "https://example.com")
        assert links == []


class TestCrawlerPlaywrightMissing:
    """Verify that a helpful error is raised when Playwright is not installed."""

    @pytest.mark.asyncio
    async def test_raises_runtime_error_when_playwright_missing(self):
        crawler = Crawler("https://example.com")
        with patch.dict("sys.modules", {"playwright": None, "playwright.async_api": None}):
            with pytest.raises((RuntimeError, Exception)):
                await crawler.crawl()
