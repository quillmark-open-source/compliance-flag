# Usage

## Local File

```bash
compliance-flag scan --file page.html
```

Supported local file types are `.html`, `.htm`, `.md`, and `.txt`.

## URL

```bash
compliance-flag scan --url https://example.com
```

URL mode captures the page content first, saves the raw source material, and analyzes that captured content.

## Output

Each scan writes:

- `scan-*.json` structured report
- `scan-*.html` human-readable report
- `scan-*.source.html` or another source-appropriate extension for the raw captured source
- `scan-*.source-meta.json` capture metadata such as source URL, content type, status code, and saved filename

Local file scans preserve the input file extension. URL scans choose the source
extension from a conservative `Content-Type` allowlist, such as `text/html` to
`.html`, `text/plain` to `.txt`, `text/markdown` to `.md`, and JSON or XML media
types to `.json` or `.xml`. If the response type is missing or unknown, URL
source captures default to `.html`.
