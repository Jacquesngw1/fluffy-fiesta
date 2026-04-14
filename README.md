# GEO Audit Tool – Neuralis Black

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/neuralis-black/geo-audit-tool/actions/workflows/ci.yml/badge.svg)](https://github.com/neuralis-black/geo-audit-tool/actions/workflows/ci.yml)

> **Automated Generative Engine Optimization audits for the AI‑first web.**

The GEO Audit Tool scans any website and returns a detailed **GEO Readiness Score** based on:

- **LLM Citation Presence** – Is your brand cited in ChatGPT, Perplexity, and Gemini?
- **Entity Resolution & Schema** – Is your `Organization` schema correct and connected?
- **Technical Foundation** – `robots.txt`, HTTPS, page speed, mobile‑friendliness.
- **Content Extractability** – Does your site have `llms.txt` and semantic HTML?

The tool is the open‑source core of [Neuralis Black's](https://www.neuralisblack.com) GEO audit service—designed for European tech startups in longevity, climate tech, and autonomous software.

---

## ✨ Features

- 🔍 **Multi‑LLM Citation Analysis** – Query ChatGPT, Perplexity, Gemini (via OpenRouter API).
- 📊 **GEO Score (0‑100)** – Composite metric with historical tracking.
- 📄 **Investor‑Ready PDF Reports** – Export professional audit summaries.
- 🧩 **Schema.org Validation** – Checks `Organization`, `sameAs`, and `WebSite` markup.
- ⚡ **CLI & Web Interface** – Run audits from terminal or browser (Streamlit).
- 🇪🇺 **GDPR‑Compliant by Design** – All data stays on your machine / EU cloud.

---

## 📦 Installation

### 1. Clone the repository
```bash
git clone https://github.com/neuralis-black/geo-audit-tool.git
cd geo-audit-tool
```

### 2. Set up a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Install Playwright browsers (for crawling)
```bash
playwright install chromium
```

### 5. Configure environment variables
Copy `.env.example` to `.env` and add your **OpenRouter API key** (free tier available).

```bash
cp .env.example .env
```

---

## 🛠️ Usage

### CLI Audit
```bash
python -m geo_audit.cli --url https://yourstartup.com --brand "Your Brand"
```

Example output:
```
🔍 Running GEO Audit for https://yourstartup.com...
✅ Crawl complete (23 pages)
📊 GEO Score: 67/100
⚠️  Priority Recommendations:
  - [P0] Add llms.txt file
  - [P1] Implement Organization schema with sameAs links
📄 Report saved: reports/audit_20250409_153022.pdf
```

### Web Interface (Streamlit)
```bash
streamlit run src/geo_audit/web.py
```
Then open `http://localhost:8501` in your browser.

---

## ⚙️ Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENROUTER_API_KEY` | API key for querying LLMs (get one at [openrouter.ai](https://openrouter.ai)) | Yes |
| `REDIS_URL` | Redis connection for queue (optional; defaults to in‑memory) | No |
| `OUTPUT_DIR` | Directory for generated reports (default: `./reports`) | No |

---

## 🧪 Development & Testing

Run tests with pytest:
```bash
pytest tests/ -v
```

Lint and format code:
```bash
black src tests
flake8 src tests
```

---

## 🤝 Contributing

We welcome contributions! Please read [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines on submitting issues and pull requests.

The roadmap is tracked in [GitHub Projects](https://github.com/neuralis-black/geo-audit-tool/projects).

---

## 📄 License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.

---

## 🔗 Related Resources

- [Neuralis Black – GEO Strategy](https://www.neuralisblack.com)
- [llms.txt Specification](https://llmstxt.org/)
- [Schema.org Organization](https://schema.org/Organization)

---

**Built with ❤️ for the Generative Era.**