# AGENTS.md

Guidance for coding agents working in this repository.

## Project Context

Compliance Flag is an open-source Python CLI for generating reviewer-ready
reports that flag potential SEC Marketing Rule issues in public URLs and local
content files.

The project is moving from an alpha scanner toward a beta-quality package. Treat
the current codebase as editable product code, but keep changes tightly scoped
and easy to review.

## Current Product Boundaries

- Focus on SEC Marketing Rule review support.
- Do not add non-SEC rule sets, categories, checks, or references without an
  explicit maintainer request.
- Do not frame scan output as legal advice, compliance approval, or a final
  determination.
- Keep the report disclaimer hardcoded in generated JSON and HTML output. Do not
  place the disclaimer in model prompts.
- Keep HTML report branding as `Compliance Flag Report`; generator metadata
  should identify the `Compliance Flag CLI` and version.

## Repository Layout

- `src/compliance_flag/cli.py` contains the CLI entry point.
- `src/compliance_flag/scanner.py` coordinates prompt construction, provider
  calls, report repair, validation, and report stamping.
- `src/compliance_flag/input/` contains file and URL capture logic.
- `src/compliance_flag/providers/` contains model provider integrations.
- `src/compliance_flag/reports/` contains JSON extraction, schema repair,
  validation, HTML rendering, and report storage.
- `src/compliance_flag/assets/prompts/` contains model prompts.
- `src/compliance_flag/assets/schemas/` contains report schemas.
- `src/compliance_flag/assets/regulations/` contains bundled SEC regulatory
  source material.
- `tests/` contains focused pytest coverage.
- `docs/` contains user and project documentation.
- `legacy_alpha/`, `reports/`, `dist/`, caches, and virtual environments are
  local/generated material and should not be committed.

## Development Commands

Use the repo's configured tools:

```bash
ruff check .
pytest
python3 -m build
```

When dependencies are not installed yet:

```bash
python -m pip install -e ".[dev]"
```

Live scans require `ANTHROPIC_API_KEY` and can take a few minutes. Prefer unit
tests for routine verification unless the requested change specifically affects
provider, prompt, URL capture, or report output behavior.

## Coding Guidelines

- Follow existing package structure and naming before adding new abstractions.
- Keep generated reports deterministic where possible; model output can vary, so
  code-level stamping, disclaimer insertion, metadata, and schema repair should
  be deterministic.
- Prefer narrow schema repair for known model omissions over broad post-hoc
  rewriting of findings.
- Keep URL input safety, source preservation, and reviewer auditability in
  mind when changing capture or extraction code.
- If reducing token usage, preserve raw captured source and clearly separate
  analyzed text from raw source in saved artifacts.
- Avoid committing secrets, API keys, live report outputs, downloaded regulatory
  material with uncertain redistribution rights, or generated build artifacts.

## Git And Release Hygiene

- Do not create commits, tags, pushes, or pull requests unless the maintainer
  explicitly asks in the current turn.
- When explicitly asked to make a commit, append this trailer to the commit
  message:

  ```text
  Co-authored-by: Codex <noreply@openai.com>
  ```

- The maintainer intends to make the first public commit. Leave staging and
  committing to them unless asked otherwise.
- Before a public-ready commit, run a hygiene sweep for prohibited/out-of-scope
  references, secrets, generated reports, and ignored legacy material.

Useful checks:

```bash
rg -n "ANTHROPIC_API_KEY|sk-|api_key|secret|password|private" . -g '!legacy_alpha/**' -g '!reports/**' -g '!dist/**' -g '!**/__pycache__/**'
git status --short --ignored
```

## Documentation Notes

- Keep `README.md`, `DISCLAIMER.md`, `docs/rule-boundaries.md`, and
  `docs/regulatory-sources.md` aligned when changing scope or regulatory source
  behavior.
- Update `ROADMAP.md` when a planned beta item is added, completed, or
  intentionally deferred.
