"""Tests for the LLM citation query engine."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from geo_audit.core.llm_queries import LLMQueryEngine


class TestLLMQueryEngineInit:
    def test_brand_stored(self):
        engine = LLMQueryEngine("Neuralis Black", api_key="test-key")
        assert engine.brand == "Neuralis Black"

    def test_api_key_from_argument(self):
        engine = LLMQueryEngine("Brand", api_key="my-key")
        assert engine.api_key == "my-key"

    def test_api_key_from_env(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "env-key")
        engine = LLMQueryEngine("Brand")
        assert engine.api_key == "env-key"

    def test_no_api_key(self, monkeypatch):
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        engine = LLMQueryEngine("Brand")
        assert engine.api_key == ""


class TestBrandMentionDetection:
    def setup_method(self):
        self.engine = LLMQueryEngine("Neuralis Black", api_key="key")

    def test_detects_exact_brand(self):
        assert self.engine._check_brand_mention("Neuralis Black is a great company.") is True

    def test_case_insensitive(self):
        assert self.engine._check_brand_mention("neuralis black offers GEO audits") is True

    def test_returns_false_when_not_mentioned(self):
        assert self.engine._check_brand_mention("Some other company is the best.") is False

    def test_empty_text(self):
        assert self.engine._check_brand_mention("") is False


class TestExcerptExtraction:
    def setup_method(self):
        self.engine = LLMQueryEngine("Brand", api_key="key")

    def test_truncates_at_max_chars(self):
        text = "x" * 500
        excerpt = self.engine._extract_excerpt(text, max_chars=300)
        assert len(excerpt) == 300

    def test_returns_full_text_when_short(self):
        text = "Short text."
        assert self.engine._extract_excerpt(text) == "Short text."

    def test_strips_whitespace(self):
        text = "  hello  "
        assert self.engine._extract_excerpt(text) == "hello"


class TestCheckCitationsNoApiKey:
    @pytest.mark.asyncio
    async def test_returns_skipped_when_no_key(self, monkeypatch):
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        engine = LLMQueryEngine("Brand")
        result = await engine.check_citations()
        assert result["skipped"] is True
        assert result["brand"] == "Brand"
        assert result["cited_by_count"] == 0


class TestCheckCitationsWithMockedAPI:
    @pytest.mark.asyncio
    async def test_aggregates_results(self):
        engine = LLMQueryEngine("Neuralis Black", api_key="test-key")

        async def fake_query(model_id: str) -> str:
            if "openai" in model_id:
                return "Neuralis Black is mentioned here."
            return "No mention of the brand."

        with patch.object(engine, "_query_model", side_effect=fake_query):
            result = await engine.check_citations()

        assert result["brand"] == "Neuralis Black"
        assert "chatgpt" in result["results"]
        assert result["results"]["chatgpt"]["cited"] is True
        assert result["results"]["gemini"]["cited"] is False
        assert result["cited_by_count"] == 1

    @pytest.mark.asyncio
    async def test_handles_query_exception(self):
        engine = LLMQueryEngine("Brand", api_key="test-key")

        async def failing_query(model_id: str) -> str:
            raise RuntimeError("API error")

        with patch.object(engine, "_query_model", side_effect=failing_query):
            result = await engine.check_citations()

        assert result["cited_by_count"] == 0
        for model_result in result["results"].values():
            assert model_result["cited"] is False
            assert "error" in model_result
