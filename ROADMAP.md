# Roadmap

Compliance Flag is moving from an alpha scanner into a beta-quality open-source CLI. This roadmap tracks near-term work that should improve reliability, cost, reviewer trust, and release readiness.

## Beta Priorities

### 1. Reduce scan token usage with visible-text extraction

Status: planned

Current URL scans send the captured HTML document to the model. This preserves context but can be expensive: the first successful beta URL scan captured about 58k page tokens and produced about 105k billed input tokens after regulatory context and prompt assembly. Local `.htm` and `.html` files have the same issue when they include markup, CSS, and JavaScript.

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
- Document regulatory source provenance before public release.
- Save a webpage screenshot artifact during URL scans so reviewers can compare the rendered page with captured source and extracted text.
- Add an OpenAI model provider alongside the current Anthropic provider.
- Support `.docx` and `.pdf` source files with reliable text extraction and source artifact preservation.
- Add configuration for model, max output tokens, and provider defaults.
- Add a `render` command for regenerating HTML from an existing JSON report.
