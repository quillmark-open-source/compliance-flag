import json
from pathlib import Path

import pytest

from compliance_flag.cli import build_parser, main
from compliance_flag.providers.anthropic import ModelUsage
from compliance_flag.scanner import ScanResult


def test_scan_parses_file_source():
    parser = build_parser()
    args = parser.parse_args(["scan", "--file", "page.html", "--out", "out"])

    assert args.file == "page.html"
    assert args.url is None
    assert args.out == "out"


def test_scan_rejects_both_file_and_url():
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["scan", "--file", "page.html", "--url", "example.com"])

    assert exc_info.value.code == 2


def test_scan_requires_a_source():
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["scan"])

    assert exc_info.value.code == 2


def test_url_help_mentions_authorized_urls(capsys):
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["scan", "--help"])

    assert exc_info.value.code == 0
    assert "authorized URL" in capsys.readouterr().out


def _fake_scan_result() -> ScanResult:
    return ScanResult(
        report={
            "report": {
                "findings": [],
                "summary": {"total_findings": 0},
            }
        },
        usage=ModelUsage(input_tokens=10, output_tokens=20),
    )


def test_run_scan_writes_all_artifacts(tmp_path: Path, monkeypatch):
    source = tmp_path / "page.md"
    source.write_text("# Example\n\nBody", encoding="utf-8")
    out_dir = tmp_path / "out"
    monkeypatch.setattr(
        "compliance_flag.cli.scan_document",
        lambda document, model=None: _fake_scan_result(),
    )

    with pytest.raises(SystemExit) as exc_info:
        main(["scan", "--file", str(source), "--out", str(out_dir)])

    assert exc_info.value.code == 0
    report_paths = [
        path
        for path in out_dir.glob("scan-page-*.json")
        if ".source-meta" not in path.name
    ]
    assert len(report_paths) == 1
    report_path = report_paths[0]
    assert report_path.with_suffix(".html").is_file()
    assert report_path.with_suffix(".source.md").is_file()
    metadata_path = report_path.with_suffix(".source-meta.json")
    assert metadata_path.is_file()
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["source_type"] == "file"


def test_run_scan_reports_missing_file_with_exit_code_1(tmp_path: Path, capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["scan", "--file", str(tmp_path / "missing.md")])

    assert exc_info.value.code == 1
    assert "error: file not found" in capsys.readouterr().err


def test_run_scan_empty_file_argument_stays_on_file_path(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["scan", "--file", ""])

    assert exc_info.value.code == 1
    assert "file not found" in capsys.readouterr().err


def test_run_scan_converts_keyboard_interrupt_to_130(tmp_path: Path, monkeypatch):
    source = tmp_path / "page.md"
    source.write_text("# Example", encoding="utf-8")

    def interrupt(document, model=None):
        raise KeyboardInterrupt

    monkeypatch.setattr("compliance_flag.cli.scan_document", interrupt)

    with pytest.raises(SystemExit) as exc_info:
        main(["scan", "--file", str(source), "--out", str(tmp_path / "out")])

    assert exc_info.value.code == 130
