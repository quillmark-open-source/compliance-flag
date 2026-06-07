# Getting Started

Install the project in editable mode:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Set `ANTHROPIC_API_KEY`, then scan a local file:

```bash
export ANTHROPIC_API_KEY="..."
compliance-flag scan --file tests/fixtures/example-blog-post.html
```

The API key is a credential from Anthropic, not from Compliance Flag. Create one in the [Anthropic Console API keys page](https://platform.claude.com/settings/keys) after setting up an Anthropic API account. When a scan runs, the CLI sends the captured source content and bundled regulatory context to Anthropic's Opus model through this key so the model can draft the report findings.

Generated reports are written to `reports/` by default.

Only scan local files, websites, or pages that you own, control, administer, or have explicit permission to assess.
