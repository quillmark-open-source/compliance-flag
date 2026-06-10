# Changelog

## 0.2.1 - 2026-06-10

### Fixed

- Generated HTML reports now include explicit paragraph, heading, and list
  spacing so reports remain readable when viewed inside pages with CSS resets.
- Generated HTML report source now emits line breaks between block elements for
  easier inspection and review.

### Changed

- Refreshed the bundled example report artifacts from the newer Opus-generated
  sample report, with sanitized repo-relative paths and current package
  metadata.

## 0.2.0 - 2026-06-10

### Changed

- Default model upgraded from `claude-opus-4-6` to `claude-opus-4-8`, with adaptive thinking enabled so the prompts' two-phase analysis runs as intended.
- Model output is now constrained server-side with structured outputs (`output_config` JSON schema), replacing the free-text JSON repair layer (`repair_report_shape` was removed). Requires `anthropic>=0.77.0`.
- `max_tokens` raised from 32,000 to 64,000 so finding-dense scans are not truncated mid-report.
- URL fetching now pins direct connections to the resolved DNS addresses (Host header and TLS SNI keep the original hostname), closing a DNS-rebinding window between resolution and connect. Resolved addresses are tried in order if one fails to connect, internationalized hostnames are IDNA-encoded, redirect hops do not reuse connections across hosts, and pinning is skipped when a proxy is configured (the proxy resolves DNS itself).
- URL scans now allow intranet, localhost, and firewall-restricted destinations when the operator is authorized to assess them; URL mode validates URL shape and resolution instead of treating internet reachability as the authorization boundary.
- Captured web pages with HTML content types are saved as `.source.html.txt` so the untrusted capture is not executed by a double-click; the source metadata sidecar marks the capture as untrusted.
- Schema validation now enforces `date-time` and `uri` formats (`jsonschema[format-nongpl]` dependency); previously those format assertions were silently skipped.
- Local files that are not valid UTF-8 are decoded via their BOM (UTF-8/UTF-16) or fall back to Windows-1252 instead of failing the scan.
- Report JSON filenames gain a numeric suffix instead of silently overwriting an earlier scan from the same second.
- Pre-flight token counts are now labeled estimates; the inaccurate OpenAI `tiktoken` path was removed (exact usage is still reported from the API response).
- Mid-stream retry now covers timeouts, all transport errors, and retryable API server errors; a model `refusal` stop reason is reported clearly. Truncated (`max_tokens`) responses still fail the scan.
- Package version is now sourced solely from `compliance_flag.__init__` via hatchling dynamic versioning.
- Release workflow now runs tests, checks the release tag against the package version, and validates distributions before publishing; build and publish are separate jobs and all actions are pinned to commit SHAs.
- CI now tests Python 3.14 and runs `ruff format --check`, `mypy`, and `twine check`.

### Fixed

- `scan --file ""` no longer falls through to the URL code path with a confusing error.
- JSON extraction no longer miscounts braces inside JSON string values when recovering a report from prose-wrapped output.
- Summary recalculation no longer writes schema-invalid severity keys when a finding has an unknown severity.

## 0.1.1 - 2026-06-07

- Documentation and CLI help release. Clarified that Compliance Flag is an AI-assisted Python CLI that uses Anthropic's Opus model through the user's Anthropic API key.
- Updated README, repository docs, package metadata, support/contribution notes, and `--model` help text for PyPI resubmission.
- Updated the report schema to accept package patch versions used by generated report metadata.

## 0.1.0.post2 - 2026-05-27

- Documentation-only release. Added website references to the README and docs overview so the PyPI package page points readers to complianceflag.com, website-hosted docs, the sample report, and project status.
- Added website and documentation links to package metadata for PyPI project links. No scanner behavior changes.

## 0.1.0.post1 - 2026-05-26

- Documentation-only release. Expanded README with developer and reviewer guidance: How It Works, Requirements, Quick Start, Reading a Report, Configuration, and Exit Codes sections. No code changes.

## 0.1.0 - 2026-05-10

- Added modern Python package scaffold with `src/` layout.
- Added `compliance-flag scan` CLI for local files and captured URL content.
- Migrated alpha scanner prompts, schema, examples, and regulatory assets.
- Added JSON report validation, summary repair, HTML rendering, and evidence output.
- Added initial tests and GitHub project health files.
