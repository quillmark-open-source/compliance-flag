# Compliance Flag

[![CI](https://github.com/quillmark-open-source/compliance-flag/actions/workflows/ci.yml/badge.svg)](https://github.com/quillmark-open-source/compliance-flag/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/compliance-flag.svg)](https://pypi.org/project/compliance-flag/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776ab.svg)](pyproject.toml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Ruff](https://img.shields.io/badge/ruff-enabled-46a146.svg)](https://docs.astral.sh/ruff/)
[![Status: alpha](https://img.shields.io/badge/status-alpha-orange.svg)](ROADMAP.md)

**Compliance Flag** is a Python CLI that prepares reviewer-ready reports on public URLs and local content files a team is authorized to review. It captures the source material, compares Registered Investment Adviser (RIA) marketing content against bundled SEC regulatory sources, and produces structured findings for qualified compliance, legal, or supervisory review.

The analysis is performed by an AI model, so each report is **structured review support, not a substitute for professional judgment**. See [Intended Use](#intended-use) and [DISCLAIMER.md](DISCLAIMER.md).

---

**Project Links:** [Website](https://complianceflag.com/) · [Documentation](docs/index.md) · [Usage](docs/usage.md) · [Rule Boundaries](docs/rule-boundaries.md) · [Regulatory Sources](docs/regulatory-sources.md) · [Roadmap](ROADMAP.md) · [Changelog](CHANGELOG.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Support](SUPPORT.md)

## Table of Contents

- [Compliance Flag](#compliance-flag)
  - [Table of Contents](#table-of-contents)
  - [Website](#website)
  - [Status](#status)
  - [How It Works](#how-it-works)
  - [Requirements](#requirements)
  - [Install](#install)
  - [Quick Start](#quick-start)
  - [Usage](#usage)
  - [Output](#output)
  - [Reading a Report](#reading-a-report)
  - [Configuration](#configuration)
  - [Exit Codes](#exit-codes)
  - [Intended Use](#intended-use)
  - [Regulatory Scope](#regulatory-scope)
  - [Development](#development)
  - [Contributing](#contributing)
  - [Security](#security)
  - [Maintainer](#maintainer)
  - [License](#license)
  - [Disclaimer](#disclaimer)

## Website

The project website is [complianceflag.com](https://complianceflag.com/). It provides a plain-language overview for compliance reviewers and technical operators, website-hosted docs, and a public sample report:

- [Website documentation](https://complianceflag.com/docs/)
- [Sample report](https://complianceflag.com/sample-home-page-audit/)
- [Project status](https://complianceflag.com/project/)

## Status

Compliance Flag is moving from alpha to beta. The current package includes:

- `compliance-flag scan --file` for local `.html`, `.htm`, `.md`, and `.txt` files
- experimental `compliance-flag scan --url` support that captures page content before analysis
- structured JSON reports validated against a bundled schema
- HTML report rendering
- saved raw source files and source metadata alongside each report
- bundled prompt, schema, and regulatory source assets migrated from the alpha scanner

See [ROADMAP.md](ROADMAP.md) for what is planned next.

## How It Works

A `scan` runs four stages:

1. **Input capture** — `--file` reads a supported local file; `--url` fetches a page with `httpx`, applies a `Content-Type` allowlist, and saves the raw bytes.
2. **Analysis** — the captured document and bundled SEC regulatory sources are sent to an Anthropic model with a versioned prompt and JSON schema.
3. **Validation** — the model response is parsed and validated against the bundled report schema; invalid output fails the scan.
4. **Rendering** — the validated report is written as JSON, rendered to HTML, and accompanied by the raw source and source metadata.

The source material is always preserved alongside the report so a reviewer can verify findings against exactly what was analyzed.

## Requirements

- Python **3.10+** (CPython 3.10, 3.11, 3.12, 3.13 are tested)
- An [Anthropic API key](https://platform.claude.com/settings/keys)
- Network access for `--url` scans and for model calls

## Install

From PyPI:

```bash
pip install compliance-flag
```

From source (latest `main`):

```bash
pip install git+https://github.com/quillmark-open-source/compliance-flag.git
```

Set your API key:

```bash
export ANTHROPIC_API_KEY="..."
```

## Quick Start

```bash
export ANTHROPIC_API_KEY="..."
compliance-flag scan --file tests/fixtures/example-blog-post.html
```

A sample report generated from that fixture is committed under [examples/reports/](examples/reports/) so you can inspect the output format without running a scan.

## Usage

```text
compliance-flag scan (--file PATH | --url URL) [--out DIR] [--model NAME]
```

Scan a local file:

```bash
compliance-flag scan --file page.html
```

Scan a URL you are authorized to review:

```bash
compliance-flag scan --url https://example.com
```

Write output to a specific directory:

```bash
compliance-flag scan --file page.html --out reports/example
```

Override the Anthropic model (experimental — the package default is recommended; other models may produce reports that fail schema validation):

```bash
compliance-flag scan --file page.html --model claude-sonnet-4-6
```

Print version or help:

```bash
compliance-flag --version
compliance-flag scan --help
```

More detail in [docs/usage.md](docs/usage.md).

## Output

Each scan writes four artifacts to the output directory (default `reports/`):

| File | Purpose |
| --- | --- |
| `scan-*.json` | Structured report, validated against the bundled schema |
| `scan-*.html` | Human-readable rendering of the same report |
| `scan-*.source.<ext>` | Raw captured source exactly as analyzed |
| `scan-*.source-meta.json` | Capture metadata (source URL, content type, status code, saved filename) |

Local file scans preserve the input file extension. URL scans choose the source extension from a conservative `Content-Type` allowlist (`text/html` → `.html`, `text/plain` → `.txt`, `text/markdown` → `.md`, JSON/XML media types → `.json`/`.xml`); unknown types default to `.html`.

## Reading a Report

A report is meant to be triaged top-down. The JSON structure mirrors the HTML rendering:

- **`executive_summary`** — a plain-language overview of what was reviewed and the headline conclusions.
- **`summary.by_severity`** — counts at `critical`, `high`, `medium`, `low`. Start with the highest severity present.
- **`summary.by_category`** — counts grouped by regulatory category (e.g. `general_prohibitions`, `recordkeeping`, `form_adv`).
- **`findings[]`** — one entry per potential issue. Each finding includes:
  - **`rule`** — the primary SEC citation, rule name, and a short description.
  - **`related_rules`** — adjacent provisions a reviewer should consider.
  - **`source`** — where in the captured material the finding came from.
  - **`content.excerpt`** + **`content.context`** — the quoted text and the surrounding rationale.
  - **`violation.explanation`** — why the model flagged it.
  - **`violation.remediation`** — a `summary`, ordered `steps`, and optional `suggested_language` to consider.
- **`disclaimer`** — the standing notice that findings are not legal conclusions.

A reviewer is expected to:

1. Open the HTML report (or the JSON if integrating with another system).
2. Confirm each excerpt against `scan-*.source.<ext>` to verify the model quoted the document accurately.
3. Apply professional judgment to accept, modify, or reject each finding. **The CLI does not decide compliance.**

For an annotated end-to-end example, see [examples/reports/example-blog-post-report.json](examples/reports/example-blog-post-report.json) and its HTML companion.

## Configuration

| Variable | Purpose |
| --- | --- |
| `ANTHROPIC_API_KEY` | Required. Authenticates calls to the Anthropic API. |

| Flag&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | Default | Purpose |
| --- | --- | --- |
| `--file` | — | Local file path (`.html`, `.htm`, `.md`, `.txt`). Mutually exclusive with `--url`. |
| `--url` | — | Authorized public URL to fetch and scan. Mutually exclusive with `--file`. |
| `--out` | `reports` | Output directory for the four scan artifacts. |
| `--model` | package default | Override the Anthropic model used for analysis. **Experimental** — non-default models may produce output that fails schema validation. |

## Exit Codes

| Code | Meaning |
| --- | --- |
| `0` | Scan completed and the report validated against the schema |
| `1` | Scan failed (input, network, API, or schema-validation error; details on stderr) |
| `130` | Cancelled by the user (`Ctrl-C`) |

A non-zero exit does **not** indicate a compliance finding — findings are reported inside the JSON/HTML output regardless of severity.

## Intended Use

Compliance Flag is a review-support tool. It is not a compliance approval system, legal reviewer, or substitute for qualified professional judgment.

Only use Compliance Flag on websites, files, pages, or other content that you **own, control, administer, or have explicit permission to assess**. Do not run URL scans against third-party websites without authorization. See [docs/rule-boundaries.md](docs/rule-boundaries.md).

## Regulatory Scope

The initial focus is **SEC Rule 275.206(4)-1**, Investment Adviser Marketing. Related SEC sources (e.g. § 275.204-2 books-and-records, Part 279 Form ADV) are used as supporting context where appropriate.

Bundled regulatory source provenance, retrieval dates, and "current-as-of" notes are tracked in [docs/regulatory-sources.md](docs/regulatory-sources.md). Treat bundled sources as point-in-time copies — verify against the authoritative source (eCFR, SEC.gov) for any consequential review.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Common tasks:

```bash
pytest              # run the test suite
ruff check .        # lint
python -m build     # build sdist + wheel into dist/
```

The package layout is `src/compliance_flag/`:

- `cli.py` — argument parsing and the `scan` entry point
- `input/` — file and URL capture
- `scanner.py` — model orchestration
- `prompts.py`, `resources.py`, `rules.py` — bundled prompt, schema, and regulatory assets
- `reports/` — JSON storage and HTML rendering
- `providers/` — Anthropic API integration

See [AGENTS.md](AGENTS.md) for guidance specific to AI-assisted contributions.

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before opening an issue or pull request. Bug reports, regulatory-source corrections, and additional test fixtures are particularly valuable at this stage.

## Security

Do not file security issues in the public tracker. Report vulnerabilities per [SECURITY.md](SECURITY.md).

## Maintainer

Compliance Flag is a [Quillmark Open Source](https://github.com/quillmark-open-source) project maintained by [Quillmark LLC](https://quillmark.ai/). General support channels are listed in [SUPPORT.md](SUPPORT.md).

## License

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).

## Disclaimer

See [DISCLAIMER.md](DISCLAIMER.md).
