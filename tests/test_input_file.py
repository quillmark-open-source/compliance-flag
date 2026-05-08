from pathlib import Path

import pytest

from compliance_flag.input.file import extract_title, load_file


def test_extract_title_from_html():
    content = "<html><head><title> Example Firm </title></head><body></body></html>"
    assert extract_title(content, "fallback.html") == "Example Firm"


def test_extract_title_from_markdown_heading():
    assert (
        extract_title("# Quarterly Update\n\nBody", "fallback.md")
        == "Quarterly Update"
    )


def test_load_file_rejects_unsupported_extension(tmp_path: Path):
    path = tmp_path / "sample.pdf"
    path.write_text("content", encoding="utf-8")

    with pytest.raises(ValueError, match="unsupported file type"):
        load_file(str(path))
