"""Tests for the GEO scoring module."""

from __future__ import annotations

import pytest

from geo_audit.core.scoring import (
    calculate_geo_score,
    _score_citations,
    _score_schema,
    _score_technical,
    _score_content,
)


class TestScoreCitations:
    def test_all_cited(self):
        citations = {
            "results": {
                "chatgpt": {"cited": True},
                "gemini": {"cited": True},
                "perplexity": {"cited": True},
            }
        }
        assert _score_citations(citations) == 100

    def test_none_cited(self):
        citations = {
            "results": {
                "chatgpt": {"cited": False},
                "gemini": {"cited": False},
                "perplexity": {"cited": False},
            }
        }
        assert _score_citations(citations) == 0

    def test_partial_citations(self):
        citations = {
            "results": {
                "chatgpt": {"cited": True},
                "gemini": {"cited": False},
                "perplexity": {"cited": False},
            }
        }
        score = _score_citations(citations)
        assert score == 33  # round(1/3 * 100)

    def test_skipped_returns_neutral(self):
        assert _score_citations({"skipped": True}) == 50

    def test_empty_results(self):
        assert _score_citations({"results": {}}) == 0


class TestScoreSchema:
    def test_full_schema(self):
        schema = {
            "organization_present": True,
            "same_as_links": ["https://linkedin.com/company/acme"],
            "website_schema_present": True,
        }
        assert _score_schema(schema) == 100

    def test_no_schema(self):
        schema = {
            "organization_present": False,
            "same_as_links": [],
            "website_schema_present": False,
        }
        assert _score_schema(schema) == 0

    def test_organization_only(self):
        schema = {
            "organization_present": True,
            "same_as_links": [],
            "website_schema_present": False,
        }
        assert _score_schema(schema) == 40


class TestScoreTechnical:
    def test_perfect_technical(self):
        tech = {
            "https": True,
            "robots_txt_present": True,
            "page_speed_score": 100,
            "llms_txt_present": True,
        }
        assert _score_technical(tech) == 100

    def test_no_technical(self):
        tech = {
            "https": False,
            "robots_txt_present": False,
            "page_speed_score": 0,
            "llms_txt_present": False,
        }
        assert _score_technical(tech) == 0


class TestScoreContent:
    def test_perfect_content(self):
        tech = {"llms_txt_present": True, "semantic_html_score": 100}
        assert _score_content(tech) == 100

    def test_no_content(self):
        tech = {"llms_txt_present": False, "semantic_html_score": 0}
        assert _score_content(tech) == 0


class TestCalculateGeoScore:
    def test_returns_total_and_categories(self):
        schema = {
            "organization_present": True,
            "same_as_links": ["https://linkedin.com"],
            "website_schema_present": True,
        }
        citations = {
            "results": {
                "chatgpt": {"cited": True},
                "gemini": {"cited": True},
                "perplexity": {"cited": True},
            }
        }
        tech = {
            "https": True,
            "robots_txt_present": True,
            "page_speed_score": 100,
            "llms_txt_present": True,
            "semantic_html_score": 100,
        }
        result = calculate_geo_score(schema, citations, tech)
        assert "total" in result
        assert "categories" in result
        assert result["total"] == 100
        assert set(result["categories"].keys()) == {"Citations", "Schema", "Technical", "Content"}

    def test_score_within_bounds(self):
        schema = {"organization_present": False, "same_as_links": [], "website_schema_present": False}
        citations = {"skipped": True}
        tech = {
            "https": False,
            "robots_txt_present": False,
            "page_speed_score": 0,
            "llms_txt_present": False,
            "semantic_html_score": 0,
        }
        result = calculate_geo_score(schema, citations, tech)
        assert 0 <= result["total"] <= 100
