"""Tests for the Schema.org validator."""

from __future__ import annotations

import json

import pytest

from geo_audit.core.schema_validator import SchemaValidator


def _page(url: str, schemas: list[dict]) -> dict:
    """Helper to build a page dict with embedded JSON-LD."""
    ld_scripts = "".join(
        f'<script type="application/ld+json">{json.dumps(s)}</script>'
        for s in schemas
    )
    return {"url": url, "html": f"<html><head>{ld_scripts}</head><body></body></html>"}


class TestSchemaValidatorNoPages:
    def test_empty_pages(self):
        result = SchemaValidator([]).analyze()
        assert result["organization_present"] is False
        assert result["website_schema_present"] is False
        assert result["same_as_links"] == []


class TestOrganizationDetection:
    def test_detects_organization(self):
        pages = [_page("https://example.com", [{"@type": "Organization", "name": "Acme"}])]
        result = SchemaValidator(pages).analyze()
        assert result["organization_present"] is True

    def test_no_organization(self):
        pages = [_page("https://example.com", [{"@type": "WebSite"}])]
        result = SchemaValidator(pages).analyze()
        assert result["organization_present"] is False


class TestWebSiteDetection:
    def test_detects_website_schema(self):
        pages = [_page("https://example.com", [{"@type": "WebSite"}])]
        result = SchemaValidator(pages).analyze()
        assert result["website_schema_present"] is True


class TestSameAsLinks:
    def test_extracts_same_as_list(self):
        org = {
            "@type": "Organization",
            "sameAs": ["https://linkedin.com/company/acme", "https://twitter.com/acme"],
        }
        pages = [_page("https://example.com", [org])]
        result = SchemaValidator(pages).analyze()
        assert "https://linkedin.com/company/acme" in result["same_as_links"]

    def test_extracts_same_as_string(self):
        org = {"@type": "Organization", "sameAs": "https://linkedin.com/company/acme"}
        pages = [_page("https://example.com", [org])]
        result = SchemaValidator(pages).analyze()
        assert "https://linkedin.com/company/acme" in result["same_as_links"]

    def test_deduplicates_same_as_links(self):
        org = {
            "@type": "Organization",
            "sameAs": ["https://linkedin.com/company/acme", "https://linkedin.com/company/acme"],
        }
        pages = [_page("https://example.com", [org])]
        result = SchemaValidator(pages).analyze()
        assert result["same_as_links"].count("https://linkedin.com/company/acme") == 1


class TestSchemaTypesFound:
    def test_collects_all_types(self):
        pages = [
            _page("https://example.com", [{"@type": "Organization"}]),
            _page("https://example.com/about", [{"@type": "Person"}]),
        ]
        result = SchemaValidator(pages).analyze()
        assert "Organization" in result["schema_types_found"]
        assert "Person" in result["schema_types_found"]


class TestIssueGeneration:
    def test_issues_when_nothing_present(self):
        result = SchemaValidator([]).analyze()
        assert any("Organization" in i for i in result["issues"])
        assert any("WebSite" in i for i in result["issues"])

    def test_no_issues_when_fully_configured(self):
        org = {
            "@type": "Organization",
            "sameAs": ["https://linkedin.com/company/acme"],
        }
        site = {"@type": "WebSite"}
        pages = [_page("https://example.com", [org, site])]
        result = SchemaValidator(pages).analyze()
        # Organization and WebSite are present; sameAs coverage may still flag minor issues
        assert not any("No Organization schema" in i for i in result["issues"])
        assert not any("No WebSite" in i for i in result["issues"])


class TestMalformedJsonLd:
    def test_ignores_invalid_json(self):
        html = '<script type="application/ld+json">{ invalid json }</script>'
        page = {"url": "https://example.com", "html": html}
        result = SchemaValidator([page]).analyze()
        assert result["organization_present"] is False
