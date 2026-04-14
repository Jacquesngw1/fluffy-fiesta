"""
GEO score calculation.

The composite GEO Readiness Score (0-100) is calculated from four categories:

  1. Citations   (30 %) – LLM citation presence across queried models
  2. Schema      (25 %) – Schema.org completeness & entity resolution
  3. Technical   (25 %) – HTTPS, robots.txt, page speed, llms.txt
  4. Content     (20 %) – Semantic HTML quality and extractability

Each category score is 0-100; the composite is the weighted average.
"""

from __future__ import annotations

from typing import Any


# Category weights (must sum to 1.0)
_WEIGHTS: dict[str, float] = {
    "citations": 0.30,
    "schema": 0.25,
    "technical": 0.25,
    "content": 0.20,
}


def calculate_geo_score(
    schema_results: dict[str, Any],
    citations: dict[str, Any],
    tech_results: dict[str, Any],
) -> dict[str, Any]:
    """
    Calculate the composite GEO Readiness Score.

    Args:
        schema_results: Output from SchemaValidator.analyze()
        citations:      Output from LLMQueryEngine.check_citations()
        tech_results:   Output from TechnicalChecker.run_checks()

    Returns:
        {
            "total": int,               # 0-100 composite score
            "categories": {
                "Citations": int,
                "Schema": int,
                "Technical": int,
                "Content": int,
            }
        }
    """
    citation_score = _score_citations(citations)
    schema_score = _score_schema(schema_results)
    technical_score = _score_technical(tech_results)
    content_score = _score_content(tech_results)

    category_scores = {
        "Citations": citation_score,
        "Schema": schema_score,
        "Technical": technical_score,
        "Content": content_score,
    }

    total = round(
        citation_score * _WEIGHTS["citations"]
        + schema_score * _WEIGHTS["schema"]
        + technical_score * _WEIGHTS["technical"]
        + content_score * _WEIGHTS["content"]
    )

    return {"total": total, "categories": category_scores}


# ------------------------------------------------------------------
# Category scorers
# ------------------------------------------------------------------


def _score_citations(citations: dict[str, Any]) -> int:
    """Score LLM citation presence (0-100)."""
    if citations.get("skipped"):
        return 50  # Neutral score when checks are skipped

    results = citations.get("results", {})
    if not results:
        return 0

    total_models = len(results)
    cited_count = sum(1 for v in results.values() if v.get("cited"))
    return round((cited_count / total_models) * 100)


def _score_schema(schema_results: dict[str, Any]) -> int:
    """Score Schema.org completeness (0-100)."""
    score = 0
    if schema_results.get("organization_present"):
        score += 40
    if schema_results.get("same_as_links"):
        score += 35
    if schema_results.get("website_schema_present"):
        score += 25
    return min(score, 100)


def _score_technical(tech_results: dict[str, Any]) -> int:
    """Score technical foundation (0-100)."""
    score = 0
    if tech_results.get("https"):
        score += 30
    if tech_results.get("robots_txt_present"):
        score += 15
    # page speed contributes up to 30 points
    speed = tech_results.get("page_speed_score", 0)
    score += round(speed * 0.30)
    # llms.txt contributes 25 points
    if tech_results.get("llms_txt_present"):
        score += 25
    return min(score, 100)


def _score_content(tech_results: dict[str, Any]) -> int:
    """Score content extractability (0-100)."""
    score = 0
    if tech_results.get("llms_txt_present"):
        score += 40
    semantic = tech_results.get("semantic_html_score", 0)
    score += round(semantic * 0.60)
    return min(score, 100)
