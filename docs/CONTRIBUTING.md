# Contributing to GEO Audit Tool

Thank you for your interest in contributing! This document explains how to get started.

---

## Code of Conduct

Be respectful and constructive. We follow the [Contributor Covenant](https://www.contributor-covenant.org/) code of conduct.

---

## Getting Started

1. **Fork** the repository and clone your fork.
2. Create a **virtual environment** and install dependencies:

   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   playwright install chromium
   ```

3. Copy `.env.example` to `.env` and add your OpenRouter API key.

4. Create a feature branch:

   ```bash
   git checkout -b feat/my-new-feature
   ```

---

## Development Workflow

### Running Tests

```bash
pytest tests/ -v
```

### Linting & Formatting

```bash
black src tests
flake8 src tests
```

### Running the CLI Locally

```bash
python -m geo_audit.cli --url https://example.com --brand "Example" --no-llm
```

---

## Submitting a Pull Request

1. Ensure all tests pass and linting is clean.
2. Add or update tests for any new functionality.
3. Update `docs/API.md` if you change or add public API surface.
4. Open a pull request against `main` with a clear description of your changes.

---

## Reporting Issues

Use the GitHub Issue templates in `.github/ISSUE_TEMPLATE/`:

- **Bug reports** – include reproduction steps, expected vs actual behaviour, and environment details.
- **Feature requests** – describe the problem and your proposed solution.

---

## Roadmap

The project roadmap is tracked in [GitHub Projects](https://github.com/neuralis-black/geo-audit-tool/projects). Contributions aligned with roadmap items are especially welcome.

---

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](../LICENSE).
