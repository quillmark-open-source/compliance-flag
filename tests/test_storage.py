import json
from pathlib import Path

from compliance_flag.input.file import SourceDocument
from compliance_flag.reports.storage import save_source_artifacts, source_extension


def test_source_extension_uses_file_suffix():
    document = SourceDocument(
        source_type="file",
        location="/tmp/page.md",
        title="Page",
        content="# Page",
    )

    assert source_extension(document) == ".md"


def test_source_extension_uses_web_content_type():
    document = SourceDocument(
        source_type="web",
        location="https://example.com/page",
        title="Page",
        content="<html></html>",
    )

    assert source_extension(document, "text/html; charset=utf-8") == ".html"
    assert source_extension(document, "text/plain") == ".txt"
    assert source_extension(document, "application/activity+json") == ".json"


def test_source_extension_defaults_web_to_html():
    document = SourceDocument(
        source_type="web",
        location="https://example.com/page",
        title="Page",
        content="<html></html>",
    )

    assert source_extension(document) == ".html"


def test_save_source_artifacts_writes_raw_source_and_metadata(tmp_path: Path):
    document = SourceDocument(
        source_type="web",
        location="https://example.com/page",
        title="Example",
        content="<html><body>Raw</body></html>",
    )
    report_path = tmp_path / "scan-example-20260508-120000.json"

    paths = save_source_artifacts(
        document,
        report_path,
        content_type="text/html; charset=utf-8",
        status_code=200,
    )

    assert paths.source == tmp_path / "scan-example-20260508-120000.source.html"
    assert paths.metadata == (
        tmp_path / "scan-example-20260508-120000.source-meta.json"
    )
    assert paths.source.read_text(encoding="utf-8") == document.content

    metadata = json.loads(paths.metadata.read_text(encoding="utf-8"))
    assert metadata["source_type"] == "web"
    assert metadata["location"] == "https://example.com/page"
    assert metadata["final_url"] == "https://example.com/page"
    assert metadata["content_type"] == "text/html; charset=utf-8"
    assert metadata["media_type"] == "text/html"
    assert metadata["status_code"] == 200
    assert metadata["saved_as"] == "scan-example-20260508-120000.source.html"
