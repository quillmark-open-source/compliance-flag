# Getting Started

Install the project in editable mode:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Set `ANTHROPIC_API_KEY`, then scan a local file:

```bash
compliance-flag scan --file tests/fixtures/example-blog-post.html
```

Generated reports are written to `reports/` by default.

Only scan local files, websites, or pages that you own, control, administer, or have explicit permission to assess.
