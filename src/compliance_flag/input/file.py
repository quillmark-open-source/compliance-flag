from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from compliance_flag.logging import log
from compliance_flag.tokens import count_tokens

SUPPORTED_EXTENSIONS = {".html", ".htm", ".txt", ".md"}
MAX_FILE_SIZE = 512 * 1024


@dataclass(frozen=True)
class SourceDocument:
    source_type: str
    location: str
    title: str
    content: str


def extract_title(content: str, fallback: str) -> str:
    """Extract a title from HTML or Markdown-ish content."""
    match = re.search(r"<title[^>]*>(.*?)</title>", content, re.IGNORECASE | re.DOTALL)
    if match and match.group(1).strip():
        return re.sub(r"\s+", " ", match.group(1)).strip()

    heading = re.search(r"^\s*#\s+(.+)$", content, re.MULTILINE)
    if heading and heading.group(1).strip():
        return heading.group(1).strip()

    return fallback


def load_file(path: str) -> SourceDocument:
    """Load and validate a local input file."""
    resolved = Path(path).expanduser().resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"file not found: {path}")

    extension = resolved.suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(f"unsupported file type '{extension}'. Supported: {supported}")

    size = resolved.stat().st_size
    if size == 0:
        raise ValueError(f"file is empty: {path}")
    if size > MAX_FILE_SIZE:
        raise ValueError(f"file too large ({size:,} bytes). Max: {MAX_FILE_SIZE:,}")

    content = resolved.read_text(encoding="utf-8")
    tokens, method = count_tokens(content)
    log(f"loaded input file: {resolved.name} ({tokens:,} tokens, {method})")

    return SourceDocument(
        source_type="file",
        location=str(resolved),
        title=extract_title(content, resolved.name),
        content=content,
    )
