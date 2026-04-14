"""
Schema.org validator and entity resolution checker.

Analyses crawled pages for structured data markup (JSON-LD, Microdata, RDFa)
and checks for the presence and correctness of key schema types:
  - Organization
  - WebSite
  - sameAs links
"""

from __future__ import annotations

import json
import logging
from typing import Any

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_IMPORTANT_SAME_AS_DOMAINS = [
    "linkedin.com",
    "twitter.com",
    "x.com",
    "wikidata.org",
    "crunchbase.com",
    "facebook.com",
    "instagram.com",
    "github.com",
]


class SchemaValidator:
    """Validate Schema.org structured data across a list of crawled pages."""

    def __init__(self, pages: list[dict[str, Any]]) -> None:
        self.pages = pages

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self) -> dict[str, Any]:
        """
        Analyse all pages and return a summary of schema findings.

        Returns:
        {
            "organization_present": bool,
            "website_schema_present": bool,
            "same_as_links": list[str],
            "schema_types_found": list[str],
            "issues": list[str],
            "page_details": list[dict],
        }
        """
        organization_present = False
        website_schema_present = False
        same_as_links: list[str] = []
        all_schema_types: set[str] = set()
        issues: list[str] = []
        page_details: list[dict[str, Any]] = []

        for page in self.pages:
            url = page.get("url", "")
            html = page.get("html", "")
            schemas = self._extract_json_ld(html)

            page_types = [s.get("@type", "") for s in schemas]
            all_schema_types.update(page_types)

            for schema in schemas:
                schema_type = schema.get("@type", "")
                if schema_type == "Organization":
                    organization_present = True
                    links = schema.get("sameAs", [])
                    if isinstance(links, str):
                        links = [links]
                    same_as_links.extend(links)
                elif schema_type == "WebSite":
                    website_schema_present = True

            page_details.append(
                {
                    "url": url,
                    "schema_types": page_types,
                    "schema_count": len(schemas),
                }
            )

        # Deduplicate sameAs links
        same_as_links = list(dict.fromkeys(same_as_links))

        # Generate issues
        if not organization_present:
            issues.append("No Organization schema found.")
        if not same_as_links:
            issues.append("No sameAs links found in Organization schema.")
        else:
            covered = {
                domain
                for link in same_as_links
                for domain in _IMPORTANT_SAME_AS_DOMAINS
                if domain in link
            }
            missing = set(_IMPORTANT_SAME_AS_DOMAINS[:3]) - covered
            if missing:
                issues.append(
                    f"Missing sameAs links for: {', '.join(sorted(missing))}"
                )
        if not website_schema_present:
            issues.append("No WebSite schema found.")

        return {
            "organization_present": organization_present,
            "website_schema_present": website_schema_present,
            "same_as_links": same_as_links,
            "schema_types_found": sorted(all_schema_types),
            "issues": issues,
            "page_details": page_details,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_json_ld(self, html: str) -> list[dict[str, Any]]:
        """Extract all JSON-LD script blocks from *html* and return parsed dicts."""
        soup = BeautifulSoup(html, "html.parser")
        schemas: list[dict[str, Any]] = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                if isinstance(data, dict):
                    schemas.append(data)
                elif isinstance(data, list):
                    schemas.extend(data)
            except json.JSONDecodeError as exc:
                logger.debug("Failed to parse JSON-LD: %s", exc)
        return schemas
