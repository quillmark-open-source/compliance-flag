# Contributing

Thanks for helping improve Compliance Flag.

## Development Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
```

## Contribution Guidelines

- Keep changes focused and easy to review.
- Add or update tests when behavior changes.
- Preserve review-support language. Do not describe findings as final legal or compliance determinations.
- Treat regulatory source changes carefully. Include source URLs, retrieval dates, and notes in `docs/regulatory-sources.md`.
- Do not commit generated reports, local evidence captures, Anthropic API keys, or customer/private content.

## Pull Requests

Open a pull request with:

- a concise description of the change
- test results
- any known limitations or follow-up work
