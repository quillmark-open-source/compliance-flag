# Roadmap

Compliance Flag is moving from an alpha scanner into a beta-quality open-source
CLI and Codex-assisted review workflow. This roadmap tracks near-term work that
should improve reliability, cost, reviewer trust, and release readiness.

## Release Track

### v0.1.0 - Initial alpha

Status: current

The first release is a CLI preview for early testing and feedback. It
establishes the package structure, SEC-focused scan flow, report schema, HTML
rendering, source artifact preservation, example report, and baseline project
documentation.

This release should be considered alpha-quality: useful for controlled review
support experiments, but not yet a stable compliance workflow or API contract.

### v0.2.0 - Codex plugin beta

Status: next focus

The next major milestone is an OpenAI Codex plugin that wraps the CLI workflow
for repository-local scans, report generation, and reviewer handoff.

Planned plugin work:

- Provide a Codex-native entry point for running Compliance Flag scans from a
  local workspace.
- Guide users through source selection, scan execution, report review, and next
  actions.
- Surface generated JSON, HTML, source artifacts, and future screenshots in a
  reviewer-friendly workflow.
- Keep SEC Marketing Rule scope, disclaimer behavior, source preservation, and
  report boundaries consistent with the CLI.
- Document when to use the CLI directly versus the Codex plugin workflow.

## Improvement Areas

### Reduce scan token usage with visible-text extraction

Status: planned

Current URL scans send the captured HTML document to Anthropic's Opus model. This preserves
context but can be expensive: the first successful beta URL scan captured about
58k page tokens and produced about 105k billed input tokens after regulatory
context and prompt assembly. Local `.htm` and `.html` files have the same issue
when they include markup, CSS, and JavaScript.

Planned change:

- Save the full raw HTML source exactly as captured.
- Add a deterministic extraction step that strips HTML tags, CSS, and JavaScript from URL captures and local `.htm` / `.html` files before model analysis.
- Preserve important page context such as title, headings, link text, image alt text, disclosures, footer content, testimonials, awards, performance tables, and nearby labels.
- Exclude scripts, styles, repeated navigation where safe, tracking snippets, and other non-visible markup.
- Include extraction metadata in the saved source artifacts/report so reviewers can distinguish raw source from analyzed text.
- Add tests with realistic HTML fixtures to verify disclosures, footers, testimonials, and performance-like content are not dropped.

Goal: materially reduce token usage and scan time while keeping the audit trail strong.

## Backlog

- Port the alpha URL safety gate into the package URL input flow.
- Add mocked provider tests for the full scan pipeline.
- Add a stable report schema version and migration notes.
- Document regulatory source provenance before release.
- Save a webpage screenshot artifact during URL scans so reviewers can compare the rendered page with captured source and extracted text.
- Add an OpenAI model provider alongside the current Anthropic provider.
- Support `.docx` and `.pdf` source files with reliable text extraction and source artifact preservation.
- Add configuration for model, max output tokens, and provider defaults.
- Add a `render` command for regenerating HTML from an existing JSON report.
