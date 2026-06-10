from pathlib import Path

import pytest

from compliance_flag.input.file import extract_title, load_file


def test_extract_title_from_html():
    content = "<html><head><title> Example Firm </title></head><body></body></html>"
    assert extract_title(content, "fallback.html") == "Example Firm"


def test_extract_title_from_markdown_heading():
    assert (
        extract_title("# Quarterly Update\n\nBody", "fallback.md") == "Quarterly Update"
    )


def test_load_file_rejects_unsupported_extension(tmp_path: Path):
    path = tmp_path / "sample.pdf"
    path.write_text("content", encoding="utf-8")

    with pytest.raises(ValueError, match="unsupported file type"):
        load_file(str(path))


def test_load_file_tolerates_windows_1252_content(tmp_path: Path):
    path = tmp_path / "sample.html"
    # 0x92 is a cp1252 right single quote; invalid as UTF-8.
    path.write_bytes(b"<html><body>The firm\x92s results \x97 2026</body></html>")

    document = load_file(str(path))

    assert "firm’s" in document.content
    assert "—" in document.content


def test_load_file_decodes_utf16_with_bom(tmp_path: Path):
    path = tmp_path / "sample.txt"
    path.write_bytes("UTF-16 marketing text".encode("utf-16"))

    document = load_file(str(path))

    assert document.content == "UTF-16 marketing text"
