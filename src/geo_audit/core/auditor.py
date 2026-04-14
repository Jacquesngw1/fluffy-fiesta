"""
Main orchestration class for the GEO audit.

The GEOAuditor coordinates crawling, schema validation, LLM citation checking,
and technical checks to produce a unified GEO Readiness Score.
"""

from __future__ import annotations

import logging
from typing import Any

from .crawler import Crawler
from .llm_queries import LLMQueryEngine
from .schema_validator import SchemaValidator
from .scoring import calculate_geo_score
from .technical_checks import TechnicalChecker

logger = logging.getLogger(__name__)


class GEOAuditor:
    """Orchestrates a full GEO audit for a given URL and brand."""

    def __init__(
        self,
        url: str,
        brand: str,
        max_pages: int = 50,
        skip_llm: bool = False,
    ) -> None:
        self.url = url
        self.brand = brand
        self.max_pages = max_pages
        self.skip_llm = skip_llm
        self.results: dict[str, Any] = {}

    async def run_full_audit(self) -> dict[str, Any]:
        """Run all audit steps and return the consolidated results dictionary."""
        logger.info("Starting full GEO audit for %s", self.url)

        # 1. Crawl website
        logger.info("Step 1/4 – Crawling website…")
        crawler = Crawler(self.url, max_pages=self.max_pages)
        pages = await crawler.crawl()
        logger.info("Crawled %d page(s)", len(pages))

        # 2. Validate schema.org markup
        logger.info("Step 2/4 – Validating Schema.org markup…")
        validator = SchemaValidator(pages)
        schema_results = validator.analyze()

        # 3. Query LLMs for brand citations
        citations: dict[str, Any] = {}
        if self.skip_llm:
            logger.info("Step 3/4 – Skipping LLM citation checks (--no-llm).")
            citations = {"skipped": True}
        else:
            logger.info("Step 3/4 – Querying LLMs for brand citations…")
            llm = LLMQueryEngine(self.brand)
            citations = await llm.check_citations()

        # 4. Run technical checks
        logger.info("Step 4/4 – Running technical checks…")
        tech_checker = TechnicalChecker(self.url, pages)
        tech_results = tech_checker.run_checks()

        # 5. Calculate composite score
        score = calculate_geo_score(schema_results, citations, tech_results)

        self.results = {
            "url": self.url,
            "brand": self.brand,
            "score": score,
            "schema": schema_results,
            "citations": citations,
            "technical": tech_results,
            "recommendations": self._generate_recommendations(
                schema_results, citations, tech_results
            ),
        }
        logger.info("Audit complete. GEO Score: %s/100", score.get("total"))
        return self.results

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _generate_recommendations(
        self,
        schema_results: dict,
        citations: dict,
        tech_results: dict,
    ) -> list[dict[str, str]]:
        """Generate a prioritised list of actionable recommendations."""
        recs: list[dict[str, str]] = []

        # --- Content extractability ---
        if not tech_results.get("llms_txt_present"):
            recs.append(
                {
                    "priority": "P0",
                    "category": "content",
                    "message": (
                        "Add an llms.txt file to the root of your domain "
                        "to improve LLM indexing."
                    ),
                }
            )

        # --- Schema.org ---
        if not schema_results.get("organization_present"):
            recs.append(
                {
                    "priority": "P1",
                    "category": "schema",
                    "message": "Implement Organization schema with sameAs links.",
                }
            )
        if not schema_results.get("same_as_links"):
            recs.append(
                {
                    "priority": "P1",
                    "category": "schema",
                    "message": (
                        "Add sameAs links in your Organization schema "
                        "(LinkedIn, Wikidata, Crunchbase)."
                    ),
                }
            )
        if not schema_results.get("website_schema_present"):
            recs.append(
                {
                    "priority": "P2",
                    "category": "schema",
                    "message": "Add a WebSite schema with SearchAction.",
                }
            )

        # --- Technical ---
        if not tech_results.get("https"):
            recs.append(
                {
                    "priority": "P0",
                    "category": "technical",
                    "message": "Enable HTTPS on your domain.",
                }
            )
        if not tech_results.get("robots_txt_present"):
            recs.append(
                {
                    "priority": "P2",
                    "category": "technical",
                    "message": "Add a robots.txt file.",
                }
            )
        if tech_results.get("page_speed_score", 100) < 50:
            recs.append(
                {
                    "priority": "P1",
                    "category": "technical",
                    "message": (
                        "Improve page speed (current score is below 50). "
                        "Compress images and minimise JavaScript."
                    ),
                }
            )

        # --- LLM citations ---
        if not citations.get("skipped"):
            cited_count = sum(
                1 for v in citations.get("results", {}).values() if v.get("cited")
            )
            if cited_count == 0:
                recs.append(
                    {
                        "priority": "P1",
                        "category": "citations",
                        "message": (
                            f'"{self.brand}" was not cited by any queried LLM. '
                            "Create authoritative content and earn backlinks."
                        ),
                    }
                )

        # Sort by priority
        priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
        recs.sort(key=lambda r: priority_order.get(r.get("priority", "P3"), 3))
        return recs
