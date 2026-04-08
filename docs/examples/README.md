# Examples

This directory contains example audit outputs and scripts demonstrating how to use the GEO Audit Tool programmatically.

## Running a programmatic audit

```python
import asyncio
from geo_audit.core.auditor import GEOAuditor

async def main():
    auditor = GEOAuditor(
        url="https://example.com",
        brand="Example Brand",
        max_pages=10,
        skip_llm=True,  # Set to False and add OPENROUTER_API_KEY for LLM checks
    )
    results = await auditor.run_full_audit()
    print(f"GEO Score: {results['score']['total']}/100")
    for rec in results["recommendations"]:
        print(f"  [{rec['priority']}] {rec['message']}")

asyncio.run(main())
```

## Saving a report

```python
from pathlib import Path
from geo_audit.utils.helpers import save_report

save_report(results, Path("./reports/my_audit.json"), fmt="json")
save_report(results, Path("./reports/my_audit.html"), fmt="html")
```
