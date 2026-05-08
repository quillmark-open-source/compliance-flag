import pytest

from compliance_flag.cli import build_parser


def test_scan_requires_exactly_one_source():
    parser = build_parser()
    args = parser.parse_args(["scan", "--file", "page.html", "--out", "out"])

    assert args.file == "page.html"
    assert args.url is None
    assert args.out == "out"


def test_url_help_mentions_authorized_public_urls(capsys):
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["scan", "--help"])

    assert exc_info.value.code == 0
    assert "authorized public URL" in capsys.readouterr().out
