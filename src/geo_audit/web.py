"""
Streamlit web interface for the GEO Audit Tool.

Run with:
    streamlit run src/geo_audit/web.py
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from geo_audit.core.auditor import GEOAuditor
from geo_audit.utils.helpers import save_report

load_dotenv()

st.set_page_config(
    page_title="GEO Audit Tool – Neuralis Black",
    page_icon="🔍",
    layout="centered",
)


def render_header() -> None:
    st.title("🔍 GEO Audit Tool")
    st.markdown(
        "**Automated Generative Engine Optimization audits for the AI‑first web.** "
        "Enter a URL and brand name below to receive your GEO Readiness Score."
    )
    st.divider()


def render_score_card(score: dict) -> None:
    total = score.get("total", 0)
    color = "green" if total >= 70 else "orange" if total >= 40 else "red"
    st.markdown(
        f"<h2 style='text-align:center; color:{color};'>GEO Score: {total}/100</h2>",
        unsafe_allow_html=True,
    )

    categories = score.get("categories", {})
    if categories:
        cols = st.columns(len(categories))
        for col, (name, value) in zip(cols, categories.items()):
            col.metric(label=name, value=f"{value}/100")


def render_recommendations(recommendations: list) -> None:
    if not recommendations:
        st.success("✅ No critical issues found – your site is GEO-ready!")
        return

    st.subheader("⚠️ Priority Recommendations")
    priority_color = {"P0": "🔴", "P1": "🟠", "P2": "🟡", "P3": "🟢"}
    for rec in recommendations:
        priority = rec.get("priority", "P2")
        icon = priority_color.get(priority, "⚪")
        st.markdown(f"{icon} **[{priority}]** {rec.get('message', '')}")


def render_details(results: dict) -> None:
    with st.expander("📋 Schema.org Results"):
        st.json(results.get("schema", {}))
    with st.expander("🤖 LLM Citation Results"):
        st.json(results.get("citations", {}))
    with st.expander("⚙️ Technical Check Results"):
        st.json(results.get("technical", {}))
    with st.expander("📄 Full JSON Output"):
        st.code(json.dumps(results, indent=2, default=str), language="json")


def render_download(results: dict, output_dir: Path) -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"audit_{timestamp}.json"
    try:
        save_report(results, json_path, fmt="json")
        with open(json_path, "rb") as f:
            st.download_button(
                label="⬇️ Download JSON Report",
                data=f,
                file_name=json_path.name,
                mime="application/json",
            )
    except Exception as exc:  # noqa: BLE001
        st.warning(f"Could not prepare download: {exc}")


def main() -> None:
    render_header()

    with st.form("audit_form"):
        url = st.text_input(
            "Website URL",
            placeholder="https://yourstartup.com",
        )
        brand = st.text_input(
            "Brand Name",
            placeholder="Your Brand",
        )
        col1, col2 = st.columns(2)
        with col1:
            max_pages = st.number_input(
                "Max Pages to Crawl", min_value=1, max_value=200, value=50
            )
        with col2:
            skip_llm = st.checkbox(
                "Skip LLM checks",
                value=not bool(os.getenv("OPENROUTER_API_KEY")),
                help="Disable LLM citation queries (faster; no API key needed).",
            )
        submitted = st.form_submit_button("🚀 Run Audit", use_container_width=True)

    if submitted:
        if not url:
            st.error("Please enter a URL.")
            return
        if not brand:
            st.error("Please enter a brand name.")
            return

        with st.spinner(f"Auditing {url} – this may take a minute…"):
            auditor = GEOAuditor(
                url=url,
                brand=brand,
                max_pages=int(max_pages),
                skip_llm=skip_llm,
            )
            try:
                results = asyncio.run(auditor.run_full_audit())
            except Exception as exc:  # noqa: BLE001
                st.error(f"Audit failed: {exc}")
                return

        st.success("✅ Audit complete!")
        render_score_card(results.get("score", {}))
        render_recommendations(results.get("recommendations", []))
        render_details(results)

        output_dir = Path(os.getenv("OUTPUT_DIR", "./reports"))
        output_dir.mkdir(parents=True, exist_ok=True)
        render_download(results, output_dir)


if __name__ == "__main__":
    main()
