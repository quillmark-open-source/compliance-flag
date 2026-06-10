from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from compliance_flag import __version__
from compliance_flag.console import log
from compliance_flag.disclaimer import REPORT_DISCLAIMER, report_generator
from compliance_flag.input.file import SourceDocument
from compliance_flag.prompts import build_prompts
from compliance_flag.providers.anthropic import AnthropicProvider, ModelUsage
from compliance_flag.reports.json_extract import extract_json
from compliance_flag.reports.schema import (
    backfill_stripped_constraints,
    fix_summary,
    load_model_output_schema,
    validate_report,
)


@dataclass(frozen=True)
class ScanResult:
    report: dict
    usage: ModelUsage


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _stamp_report(report: dict, document: SourceDocument, *, started_at: str) -> None:
    now_iso = _utc_now()
    body = report.get("report", report)
    body["generated_at"] = now_iso
    body["scanner_version"] = __version__
    body["generator"] = report_generator(__version__)
    body["disclaimer"] = dict(REPORT_DISCLAIMER)
    scan = body.setdefault("scan", {})
    scan["started_at"] = started_at
    scan["completed_at"] = now_iso
    source = scan.setdefault("source", {})
    source["type"] = document.source_type
    source["location"] = document.location
    source["page_title"] = document.title


def scan_document(document: SourceDocument, *, model: str | None = None) -> ScanResult:
    """Analyze a captured source document and return a structured report."""
    started_at = _utc_now()
    log(f"target: {document.location}")
    prompts = build_prompts(
        source_type=document.source_type,
        location=document.location,
        title=document.title,
        content=document.content,
    )
    provider = AnthropicProvider(model=model) if model else AnthropicProvider()
    response = provider.complete(
        system=prompts.system,
        user=prompts.user,
        output_schema=load_model_output_schema(),
    )
    if response.stop_reason == "max_tokens":
        raise RuntimeError("model response was truncated at max_tokens")
    if response.stop_reason == "refusal":
        raise RuntimeError(
            "model declined to analyze this content (stop_reason: refusal)"
        )
    if not response.text.strip():
        raise RuntimeError("model response did not include text content")

    report = extract_json(response.text)
    backfill_stripped_constraints(report)
    fix_summary(report)
    _stamp_report(report, document, started_at=started_at)
    validate_report(report)

    return ScanResult(report=report, usage=response.usage)
