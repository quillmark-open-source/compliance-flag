from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from compliance_flag.input.file import SourceDocument

CONTENT_TYPE_EXTENSIONS = {
    "text/html": ".html",
    "application/xhtml+xml": ".html",
    "text/plain": ".txt",
    "text/markdown": ".md",
    "text/x-markdown": ".md",
    "application/json": ".json",
    "application/xml": ".xml",
    "text/xml": ".xml",
}


@dataclass(frozen=True)
class SourceArtifactPaths:
    source: Path
    metadata: Path


def output_basename(document: SourceDocument) -> str:
    if document.source_type == "web":
        stem = urlparse(document.location).netloc or "unknown"
    else:
        stem = Path(document.location).stem
    stem = re.sub(r"[^\w.-]", "_", stem)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"scan-{stem}-{timestamp}"


def save_report(report: dict, document: SourceDocument, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    basename = output_basename(document)
    path = out_dir / f"{basename}.json"
    counter = 1
    while path.exists():
        path = out_dir / f"{basename}-{counter}.json"
        counter += 1
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _media_type(content_type: str | None) -> str:
    return (content_type or "").split(";", 1)[0].strip().lower()


def _extension_from_content_type(content_type: str | None) -> str | None:
    media_type = _media_type(content_type)
    if not media_type:
        return None
    if media_type in CONTENT_TYPE_EXTENSIONS:
        return CONTENT_TYPE_EXTENSIONS[media_type]
    if media_type.endswith("+json"):
        return ".json"
    if media_type.endswith("+xml"):
        return ".xml"
    if media_type.startswith("text/"):
        return ".txt"
    return None


def source_extension(document: SourceDocument, content_type: str | None = None) -> str:
    if document.source_type == "file":
        suffix = Path(document.location).suffix.lower()
        return suffix or ".txt"

    extension = _extension_from_content_type(content_type) or ".html"
    if extension == ".html":
        # Captured web pages are untrusted; the .txt suffix prevents a
        # double-click from executing the page's scripts locally.
        return ".html.txt"
    return extension


def save_source_artifacts(
    document: SourceDocument,
    report_path: Path,
    *,
    content_type: str | None = None,
    status_code: int | None = None,
) -> SourceArtifactPaths:
    extension = source_extension(document, content_type)
    source_path = report_path.with_suffix(f".source{extension}")
    metadata_path = report_path.with_suffix(".source-meta.json")
    captured_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    source_path.write_text(document.content, encoding="utf-8")

    metadata = {
        "source_type": document.source_type,
        "location": document.location,
        "title": document.title,
        "content_type": content_type or "",
        "status_code": status_code,
        "saved_as": source_path.name,
        "captured_at": captured_at,
    }
    if document.source_type == "web":
        metadata["final_url"] = document.location
        metadata["media_type"] = _media_type(content_type)
        metadata["warning"] = (
            "raw untrusted capture of a remote page; do not open as HTML"
        )

    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return SourceArtifactPaths(source=source_path, metadata=metadata_path)
