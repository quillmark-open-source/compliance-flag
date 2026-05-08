# Compliance Flag

Compliance Flag is an open-source Python CLI for generating reviewer-ready reports that flag potential SEC Marketing Rule issues in authorized public URLs and local content files.

The project helps teams capture source material, analyze RIA marketing content against bundled regulatory source material, and produce structured reports for qualified compliance, legal, or supervisory review.

## Status

Compliance Flag is moving from alpha to beta. The current package scaffold includes:

- `compliance-flag scan --file` for local `.html`, `.htm`, `.md`, and `.txt` files
- experimental `compliance-flag scan --url` support that captures page content before analysis
- structured JSON reports validated against a bundled schema
- HTML report rendering
- saved raw source files and source metadata alongside each report
- bundled prompt, schema, and regulatory source assets migrated from the alpha scanner

## Install For Development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Set an Anthropic API key before running scans:

```bash
export ANTHROPIC_API_KEY="..."
```

## Usage

Scan a local file:

```bash
compliance-flag scan --file tests/fixtures/example-blog-post.html
```

Scan an authorized public URL:

```bash
compliance-flag scan --url https://example.com
```

Write output to a specific directory:

```bash
compliance-flag scan --file page.html --out reports/example
```

Each scan writes:

- a JSON report
- an HTML report
- a raw captured source file, such as `.source.html`
- a source metadata file, `.source-meta.json`

## Intended Use

Compliance Flag is a review-support tool. It is not a compliance approval system, legal reviewer, or substitute for qualified professional judgment.

Only use Compliance Flag on websites, files, pages, or other content that you own, control, administer, or have explicit permission to assess. Do not run URL scans against third-party websites without authorization.

The initial project focus is SEC Rule 275.206(4)-1, Investment adviser marketing. Related SEC sources may be used as supporting context where appropriate.

## Development

```bash
pytest
ruff check .
python -m build
```

## Maintainer

Compliance Flag is a [Quillmark Open Source](https://github.com/quillmark-open-source) project maintained by [Quillmark LLC](https://quillmark.ai/).

## License

Apache-2.0. See [LICENSE](LICENSE).

## Disclaimer

See [DISCLAIMER.md](DISCLAIMER.md).
