"""
Multi-LLM citation checking via the OpenRouter API.

Queries ChatGPT (OpenAI), Gemini (Google), and Perplexity to determine whether
a given brand is cited in AI-generated responses.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# Models available through OpenRouter
_MODELS: dict[str, str] = {
    "chatgpt": "openai/gpt-4o-mini",
    "gemini": "google/gemini-flash-1.5",
    "perplexity": "perplexity/sonar-small-online",
}

_CITATION_PROMPT_TEMPLATE = (
    "Which companies, products, or tools are well-known in the same industry or "
    "category as '{brand}'? List the most recognised ones you are aware of, "
    "including {brand} if applicable."
)


class LLMQueryEngine:
    """Query multiple LLMs and detect brand citations."""

    def __init__(self, brand: str, api_key: str | None = None) -> None:
        self.brand = brand
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def check_citations(self) -> dict[str, Any]:
        """
        Query all configured LLMs and check if the brand is mentioned.

        Returns:
        {
            "brand": str,
            "results": {
                "chatgpt": {"cited": bool, "excerpt": str, "model": str},
                ...
            },
            "cited_by_count": int,
        }
        """
        if not self.api_key:
            logger.warning(
                "OPENROUTER_API_KEY is not set; skipping LLM citation checks."
            )
            return {"brand": self.brand, "results": {}, "cited_by_count": 0, "skipped": True}

        import asyncio

        tasks = {
            name: self._query_model(model_id)
            for name, model_id in _MODELS.items()
        }
        responses = await asyncio.gather(*tasks.values(), return_exceptions=True)
        results: dict[str, Any] = {}
        for name, response in zip(tasks.keys(), responses):
            if isinstance(response, Exception):
                logger.warning("LLM query failed for %s: %s", name, response)
                results[name] = {"cited": False, "excerpt": "", "model": _MODELS[name], "error": str(response)}
            else:
                cited = self._check_brand_mention(response)
                excerpt = self._extract_excerpt(response)
                results[name] = {
                    "cited": cited,
                    "excerpt": excerpt,
                    "model": _MODELS[name],
                }

        cited_by_count = sum(1 for v in results.values() if v.get("cited"))
        return {
            "brand": self.brand,
            "results": results,
            "cited_by_count": cited_by_count,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _query_model(self, model_id: str) -> str:
        """Send a prompt to the specified OpenRouter model and return the text."""
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise RuntimeError(
                "openai package is required. Run: pip install openai"
            ) from exc

        client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        prompt = _CITATION_PROMPT_TEMPLATE.format(brand=self.brand)
        completion = await client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0.2,
        )
        return completion.choices[0].message.content or ""

    def _check_brand_mention(self, text: str) -> bool:
        """Return True if the brand name appears in the LLM response."""
        return self.brand.lower() in text.lower()

    def _extract_excerpt(self, text: str, max_chars: int = 300) -> str:
        """Extract the first *max_chars* characters of the response as an excerpt."""
        return text[:max_chars].strip()
