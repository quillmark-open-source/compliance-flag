# Usage

Each scan sends captured content and bundled regulatory context to Anthropic's Opus model through the user's `ANTHROPIC_API_KEY`, then validates the model output against the bundled report schema.

## Local File

```bash
compliance-flag scan --file page.html
```

Supported local file types are `.html`, `.htm`, `.md`, and `.txt`.

## URL

```bash
compliance-flag scan --url https://example.com
```

URL mode is only for pages you own, control, administer, or have explicit permission to assess. Do not run URL scans against third-party websites or systems without authorization. Authorized URLs can include intranet, localhost, or firewall-restricted resources when the scanner is run in an environment allowed to reach them.

URL mode captures the page content first, saves the raw source material, and analyzes that captured content.

## Model

The package default is `claude-opus-4-8`, Anthropic's Opus model. Use `--model` only when you have a specific reason to test another Anthropic model:

```bash
compliance-flag scan --file page.html --model anthropic-model-name
```

Model override is experimental. The override must support adaptive thinking and structured outputs (Opus 4.6 and later, Sonnet 4.6, Fable 5) — older models are rejected by the API — and non-default models may produce output that fails schema validation.

## Output

Each scan writes:

- `scan-*.json` structured report
- `scan-*.html` human-readable report
- `scan-*.source.html.txt` or another source-appropriate extension for the raw captured source
- `scan-*.source-meta.json` capture metadata such as source URL, content type, status code, and saved filename

Local file scans preserve the input file extension. URL scans choose the source
extension from a conservative `Content-Type` allowlist, such as `text/plain` to
`.txt`, `text/markdown` to `.md`, and JSON or XML media types to `.json` or
`.xml`. HTML captures (and responses with a missing or unknown type) are saved
as `.html.txt` so the untrusted page cannot be opened directly as HTML by a
double-click.
