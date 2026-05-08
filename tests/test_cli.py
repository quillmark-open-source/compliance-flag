from compliance_flag.cli import build_parser


def test_scan_requires_exactly_one_source():
    parser = build_parser()
    args = parser.parse_args(["scan", "--file", "page.html", "--out", "out"])

    assert args.file == "page.html"
    assert args.url is None
    assert args.out == "out"
