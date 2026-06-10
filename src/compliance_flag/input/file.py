from __future__ import annotations

import codecs
import re
from dataclasses import dataclass
from pathlib import Path

from compliance_flag.console import log
from compliance_flag.tokens import estimate_tokens

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


_BOM_ENCODINGS = (
    (codecs.BOM_UTF8, "utf-8-sig"),
    (codecs.BOM_UTF16_LE, "utf-16"),
    (codecs.BOM_UTF16_BE, "utf-16"),
)


def _decode_content(raw: bytes) -> str:
    """Decode file bytes, tolerating common non-UTF-8 exports."""
    for bom, encoding in _BOM_ENCODINGS:
        if raw.startswith(bom):
            return raw.decode(encoding, errors="replace")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp1252", errors="replace")


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

    content = _decode_content(resolved.read_bytes())
    log(
        f"loaded input file: {resolved.name} "
        f"(~{estimate_tokens(content):,} tokens, estimated)"
    )

    return SourceDocument(
        source_type="file",
        location=str(resolved),
        title=extract_title(content, resolved.name),
        content=content,
    )
