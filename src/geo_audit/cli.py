"""
Command-line interface for the GEO Audit Tool.

Usage:
    python -m geo_audit.cli --url https://example.com --brand "Example Brand"
    geo-audit --url https://example.com --brand "Example Brand"
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from geo_audit.core.auditor import GEOAuditor
from geo_audit.utils.helpers import save_report

load_dotenv()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="geo-audit",
        description="Automated GEO (Generative Engine Optimization) audit tool.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  geo-audit --url https://example.com --brand "Example Brand"
  geo-audit --url https://example.com --brand "Example" --output ./my-reports --format json
        """,
    )
    parser.add_argument(
        "--url",
        required=True,
        help="The URL of the website to audit.",
    )
    parser.add_argument(
        "--brand",
        required=True,
        help='The brand name to search for in LLM citations (e.g. "Neuralis Black").',
    )
    parser.add_argument(
        "--output",
        default=os.getenv("OUTPUT_DIR", "./reports"),
        help="Directory where the report will be saved (default: ./reports).",
    )
    parser.add_argument(
        "--format",
        choices=["pdf", "html", "json"],
        default="pdf",
        help="Output format for the report (default: pdf).",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=int(os.getenv("MAX_PAGES", "50")),
        help="Maximum number of pages to crawl (default: 50).",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Skip LLM citation checks (faster; useful when no API key is set).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )
    return parser


async def run_audit(args: argparse.Namespace) -> dict:
    """Run the full GEO audit and return the results dictionary."""
    print(f"\n🔍 Running GEO Audit for {args.url}...")
    auditor = GEOAuditor(
        url=args.url,
        brand=args.brand,
        max_pages=args.max_pages,
        skip_llm=args.no_llm,
    )
    results = await auditor.run_full_audit()
    return results


def print_results(results: dict) -> None:
    """Print a human-readable summary of the audit results."""
    score = results.get("score", {})
    total = score.get("total", 0)
    recommendations = results.get("recommendations", [])

    print(f"\n📊 GEO Score: {total}/100")

    category_scores = score.get("categories", {})
    if category_scores:
        print("\n   Category Breakdown:")
        for category, value in category_scores.items():
            print(f"   • {category}: {value}")

    if recommendations:
        print("\n⚠️  Priority Recommendations:")
        for rec in recommendations[:5]:
            priority = rec.get("priority", "P2")
            message = rec.get("message", "")
            print(f"   - [{priority}] {message}")
    else:
        print("\n✅ No critical recommendations – your site is GEO-ready!")


def main() -> None:
    """Entry point for the CLI."""
    parser = build_parser()
    args = parser.parse_args()

    # Validate that the API key is available when LLM checks are enabled
    if not args.no_llm and not os.getenv("OPENROUTER_API_KEY"):
        print(
            "⚠️  Warning: OPENROUTER_API_KEY is not set. "
            "LLM citation checks will be skipped.\n"
            "   Set the key in .env or use --no-llm to suppress this warning."
        )
        args.no_llm = True

    try:
        results = asyncio.run(run_audit(args))
    except KeyboardInterrupt:
        print("\n\nAudit cancelled by user.")
        sys.exit(0)
    except Exception as exc:  # noqa: BLE001
        print(f"\n❌ Audit failed: {exc}")
        sys.exit(1)

    print_results(results)

    # Save report
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_dir / f"audit_{timestamp}.{args.format}"

    try:
        save_report(results, filename, fmt=args.format)
        print(f"\n📄 Report saved: {filename}")
    except Exception as exc:  # noqa: BLE001
        print(f"\n⚠️  Could not save report: {exc}")
        # Still print JSON to stdout as fallback
        print("\nJSON output:")
        print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()
