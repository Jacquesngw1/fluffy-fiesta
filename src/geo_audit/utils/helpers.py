"""
Shared utility helpers for the GEO Audit Tool.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def save_report(results: dict[str, Any], path: Path, fmt: str = "json") -> None:
    """
    Persist the audit *results* to *path* in the given *fmt*.

    Supported formats: "json", "html", "pdf".

    For "pdf" and "html", Jinja2 is used to render the report_template.html;
    WeasyPrint converts HTML to PDF. Falls back to JSON if template rendering
    fails.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if fmt == "json":
        _save_json(results, path)
    elif fmt in ("html", "pdf"):
        html_content = _render_html(results)
        if fmt == "html":
            path.write_text(html_content, encoding="utf-8")
            logger.info("HTML report saved to %s", path)
        else:
            _save_pdf(html_content, path)
    else:
        raise ValueError(f"Unsupported report format: {fmt!r}")


def score_label(score: int) -> str:
    """Return a human-readable label for a GEO score."""
    if score >= 80:
        return "Excellent"
    if score >= 60:
        return "Good"
    if score >= 40:
        return "Fair"
    return "Poor"


def format_url(url: str) -> str:
    """Normalise a URL by stripping trailing slashes."""
    return url.rstrip("/")


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------


def _save_json(results: dict[str, Any], path: Path) -> None:
    path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    logger.info("JSON report saved to %s", path)


def _render_html(results: dict[str, Any]) -> str:
    """Render the Jinja2 HTML report template with *results*."""
    try:
        from jinja2 import Environment, FileSystemLoader

        template_dir = Path(__file__).parent.parent / "templates"
        env = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=True)
        template = env.get_template("report_template.html")
        return template.render(results=results)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Template rendering failed (%s); falling back to JSON.", exc)
        return f"<pre>{json.dumps(results, indent=2, default=str)}</pre>"


def _save_pdf(html_content: str, path: Path) -> None:
    """Convert *html_content* to a PDF and write it to *path*."""
    try:
        import weasyprint

        weasyprint.HTML(string=html_content).write_pdf(str(path))
        logger.info("PDF report saved to %s", path)
    except Exception as exc:  # noqa: BLE001
        logger.warning("PDF generation failed (%s); saving as HTML instead.", exc)
        html_path = path.with_suffix(".html")
        html_path.write_text(html_content, encoding="utf-8")
        logger.info("HTML fallback saved to %s", html_path)
