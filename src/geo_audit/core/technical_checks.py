"""
Technical foundation checks for GEO readiness.

Checks include:
  - HTTPS enforcement
  - robots.txt presence
  - llms.txt presence
  - Semantic HTML quality
  - Average page response time (as a proxy for page speed)
"""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

_REQUEST_TIMEOUT = 10  # seconds


class TechnicalChecker:
    """Run technical GEO readiness checks against a crawled website."""

    def __init__(self, base_url: str, pages: list[dict[str, Any]]) -> None:
        self.base_url = base_url.rstrip("/")
        self.pages = pages
        parsed = urlparse(base_url)
        self._scheme = parsed.scheme
        self._netloc = parsed.netloc

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_checks(self) -> dict[str, Any]:
        """
        Run all technical checks and return a results dictionary.

        Returns:
        {
            "https": bool,
            "robots_txt_present": bool,
            "llms_txt_present": bool,
            "avg_response_time_ms": float,
            "page_speed_score": int,        # 0-100 heuristic
            "semantic_html_score": int,     # 0-100 heuristic
            "issues": list[str],
        }
        """
        results: dict[str, Any] = {}

        results["https"] = self._check_https()
        results["robots_txt_present"] = self._check_file_exists("/robots.txt")
        results["llms_txt_present"] = self._check_file_exists("/llms.txt")
        results["avg_response_time_ms"] = self._calculate_avg_response_time()
        results["page_speed_score"] = self._calculate_speed_score(
            results["avg_response_time_ms"]
        )
        results["semantic_html_score"] = self._calculate_semantic_score()
        results["issues"] = self._collect_issues(results)
        return results

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _check_https(self) -> bool:
        return self._scheme == "https"

    def _check_file_exists(self, path: str) -> bool:
        url = f"https://{self._netloc}{path}" if self._check_https() else f"http://{self._netloc}{path}"
        try:
            resp = requests.head(url, timeout=_REQUEST_TIMEOUT, allow_redirects=True)
            return resp.status_code == 200
        except requests.RequestException as exc:
            logger.debug("Could not fetch %s: %s", url, exc)
            return False

    def _calculate_avg_response_time(self) -> float:
        if not self.pages:
            return 0.0
        times = [
            p.get("response_time_ms", 0.0)
            for p in self.pages
            if p.get("response_time_ms") is not None
        ]
        return round(sum(times) / len(times), 2) if times else 0.0

    def _calculate_speed_score(self, avg_ms: float) -> int:
        """Convert average response time to a 0-100 heuristic score."""
        if avg_ms <= 500:
            return 100
        if avg_ms <= 1000:
            return 80
        if avg_ms <= 2000:
            return 60
        if avg_ms <= 3000:
            return 40
        if avg_ms <= 5000:
            return 20
        return 0

    def _calculate_semantic_score(self) -> int:
        """
        Score semantic HTML quality across all pages.

        Checks for presence of: <main>, <nav>, <article>, <section>,
        <header>, <footer>, <h1>, <meta name="description">.
        """
        if not self.pages:
            return 0

        from bs4 import BeautifulSoup

        semantic_tags = ["main", "nav", "article", "section", "header", "footer"]
        scores: list[int] = []

        for page in self.pages:
            html = page.get("html", "")
            soup = BeautifulSoup(html, "html.parser")
            found = sum(1 for tag in semantic_tags if soup.find(tag))
            has_h1 = bool(soup.find("h1"))
            has_meta_desc = bool(
                soup.find("meta", attrs={"name": "description"})
            )
            page_score = int(
                (found / len(semantic_tags)) * 60
                + (20 if has_h1 else 0)
                + (20 if has_meta_desc else 0)
            )
            scores.append(page_score)

        return round(sum(scores) / len(scores))

    def _collect_issues(self, results: dict[str, Any]) -> list[str]:
        issues: list[str] = []
        if not results.get("https"):
            issues.append("Site is not served over HTTPS.")
        if not results.get("robots_txt_present"):
            issues.append("No robots.txt file found at the root.")
        if not results.get("llms_txt_present"):
            issues.append("No llms.txt file found at the root.")
        if results.get("page_speed_score", 100) < 60:
            issues.append(
                f"Slow average response time ({results['avg_response_time_ms']:.0f} ms)."
            )
        if results.get("semantic_html_score", 100) < 50:
            issues.append("Low semantic HTML score – add landmark elements.")
        return issues
