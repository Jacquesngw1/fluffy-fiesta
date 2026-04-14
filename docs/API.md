# API Reference

## `GEOAuditor`

Main orchestration class. Coordinates all audit steps.

```python
from geo_audit.core.auditor import GEOAuditor

auditor = GEOAuditor(
    url="https://example.com",
    brand="Example Brand",
    max_pages=50,
    skip_llm=False,
)
results = await auditor.run_full_audit()
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | `str` | — | Target website URL |
| `brand` | `str` | — | Brand name to check for in LLM citations |
| `max_pages` | `int` | `50` | Maximum pages to crawl |
| `skip_llm` | `bool` | `False` | Skip LLM citation checks |

### Return value

`run_full_audit()` returns a dictionary:

```json
{
  "url": "https://example.com",
  "brand": "Example Brand",
  "score": {
    "total": 67,
    "categories": {
      "Citations": 33,
      "Schema": 65,
      "Technical": 80,
      "Content": 60
    }
  },
  "schema": { ... },
  "citations": { ... },
  "technical": { ... },
  "recommendations": [
    { "priority": "P0", "category": "content", "message": "Add an llms.txt file..." },
    ...
  ]
}
```

---

## `Crawler`

Asynchronous website crawler using Playwright.

```python
from geo_audit.core.crawler import Crawler

crawler = Crawler("https://example.com", max_pages=50)
pages = await crawler.crawl()
```

Each element of `pages` is:

```json
{
  "url": "https://example.com/about",
  "html": "<html>...</html>",
  "status": 200,
  "response_time_ms": 342.5
}
```

---

## `SchemaValidator`

Validates Schema.org structured data.

```python
from geo_audit.core.schema_validator import SchemaValidator

validator = SchemaValidator(pages)
schema_results = validator.analyze()
```

### Return value

```json
{
  "organization_present": true,
  "website_schema_present": true,
  "same_as_links": ["https://linkedin.com/company/example"],
  "schema_types_found": ["Organization", "WebSite"],
  "issues": [],
  "page_details": [...]
}
```

---

## `LLMQueryEngine`

Queries multiple LLMs via OpenRouter API for brand citations.

```python
from geo_audit.core.llm_queries import LLMQueryEngine

engine = LLMQueryEngine("Example Brand", api_key="your-key")
citations = await engine.check_citations()
```

### Return value

```json
{
  "brand": "Example Brand",
  "cited_by_count": 2,
  "results": {
    "chatgpt": { "cited": true, "excerpt": "...", "model": "openai/gpt-4o-mini" },
    "gemini":  { "cited": true, "excerpt": "...", "model": "google/gemini-flash-1.5" },
    "perplexity": { "cited": false, "excerpt": "", "model": "perplexity/sonar-small-online" }
  }
}
```

---

## `TechnicalChecker`

Runs technical GEO foundation checks.

```python
from geo_audit.core.technical_checks import TechnicalChecker

checker = TechnicalChecker("https://example.com", pages)
tech_results = checker.run_checks()
```

### Return value

```json
{
  "https": true,
  "robots_txt_present": true,
  "llms_txt_present": false,
  "avg_response_time_ms": 450.0,
  "page_speed_score": 80,
  "semantic_html_score": 70,
  "issues": ["No llms.txt file found at the root."]
}
```

---

## `calculate_geo_score`

Calculates the composite GEO Readiness Score.

```python
from geo_audit.core.scoring import calculate_geo_score

score = calculate_geo_score(schema_results, citations, tech_results)
# {"total": 67, "categories": {"Citations": 33, "Schema": 65, ...}}
```

---

## Utility functions (`geo_audit.utils.helpers`)

### `save_report(results, path, fmt)`

Save audit results to file.

| Parameter | Type | Description |
|-----------|------|-------------|
| `results` | `dict` | Audit results from `GEOAuditor.run_full_audit()` |
| `path` | `Path` | Output file path |
| `fmt` | `str` | `"json"`, `"html"`, or `"pdf"` |

### `score_label(score)`

Convert a numeric score to a human-readable label.

```python
score_label(85)  # "Excellent"
score_label(65)  # "Good"
score_label(45)  # "Fair"
score_label(25)  # "Poor"
```
