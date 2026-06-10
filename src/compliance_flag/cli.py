from __future__ import annotations

import argparse
import sys
from pathlib import Path

from compliance_flag import __version__
from compliance_flag.console import log
from compliance_flag.input.file import load_file
from compliance_flag.input.url import fetch_url
from compliance_flag.providers.anthropic import DEFAULT_MODEL
from compliance_flag.reports.render_html import save_html_report
from compliance_flag.reports.storage import save_report, save_source_artifacts
from compliance_flag.scanner import scan_document


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="compliance-flag",
        description="Flag potential SEC Marketing Rule issues in URLs and local files.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="scan a URL or local file")
    source = scan.add_mutually_exclusive_group(required=True)
    source.add_argument("--file", help="local .html, .htm, .md, or .txt file")
    source.add_argument("--url", help="authorized URL to fetch and scan")
    scan.add_argument("--out", default="reports", help="output directory")
    scan.add_argument("--model", help=f"Opus model override (default: {DEFAULT_MODEL})")
    scan.set_defaults(func=run_scan)

    return parser


def run_scan(args: argparse.Namespace) -> int:
    try:
        print()
        log("compliance flag scan starting")
        print()

        if args.file is not None:
            document = load_file(args.file)
            content_type = None
            status_code = None
        else:
            fetch_result = fetch_url(args.url)
            document = fetch_result.document
            content_type = fetch_result.content_type
            status_code = fetch_result.status_code

        result = scan_document(document, model=args.model)
        report_path = save_report(result.report, document, Path(args.out))
        source_paths = save_source_artifacts(
            document,
            report_path,
            content_type=content_type,
            status_code=status_code,
        )
        html_path = save_html_report(result.report, report_path)

        findings = result.report.get("report", {}).get("findings", [])
        log("scan complete")
        log(f"report: {report_path}")
        log(f"html: {html_path}")
        log(f"source: {source_paths.source}")
        log(f"source metadata: {source_paths.metadata}")
        log(f"findings: {len(findings)}")
        log(
            "usage: "
            f"{result.usage.input_tokens:,} input, "
            f"{result.usage.output_tokens:,} output tokens"
        )
        print()
        return 0
    except KeyboardInterrupt:
        print()
        log("scan cancelled")
        return 130
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    raise SystemExit(args.func(args))
