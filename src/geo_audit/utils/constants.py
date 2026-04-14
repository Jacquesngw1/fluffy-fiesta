"""Application-wide constants for the GEO Audit Tool."""

from __future__ import annotations

# Default maximum pages to crawl per audit
DEFAULT_MAX_PAGES: int = 50

# Default output directory for generated reports
DEFAULT_OUTPUT_DIR: str = "./reports"

# Request timeout for HTTP checks (seconds)
REQUEST_TIMEOUT: int = 30

# LLM models available through OpenRouter
LLM_MODELS: dict[str, str] = {
    "chatgpt": "openai/gpt-4o-mini",
    "gemini": "google/gemini-flash-1.5",
    "perplexity": "perplexity/sonar-small-online",
}

# GEO score thresholds
SCORE_EXCELLENT: int = 80
SCORE_GOOD: int = 60
SCORE_FAIR: int = 40

# Report formats supported
SUPPORTED_REPORT_FORMATS: list[str] = ["pdf", "html", "json"]

# Schema.org types considered important for GEO
IMPORTANT_SCHEMA_TYPES: list[str] = [
    "Organization",
    "WebSite",
    "LocalBusiness",
    "Person",
    "Product",
    "Article",
    "FAQPage",
    "BreadcrumbList",
]

# Important sameAs domains for entity resolution
IMPORTANT_SAME_AS_DOMAINS: list[str] = [
    "linkedin.com",
    "twitter.com",
    "x.com",
    "wikidata.org",
    "crunchbase.com",
    "facebook.com",
    "instagram.com",
    "github.com",
]
