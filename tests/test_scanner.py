import copy
import json

import pytest
from jsonschema import ValidationError

from compliance_flag.input.file import SourceDocument
from compliance_flag.providers.anthropic import ModelResponse, ModelUsage
from compliance_flag.scanner import scan_document

VALID_MODEL_REPORT = {
    "report": {
        "id": "9a87c2d6-0e1d-4a03-bb5d-50672f8b6f2e",
        "generated_at": "2026-05-08T12:00:00Z",
        "scanner_version": "0.1.0",
        "firm": {"name": "Example Firm"},
        "scan": {
            "started_at": "2026-05-08T12:00:00Z",
            "completed_at": "2026-05-08T12:00:00Z",
            "source": {
                "type": "file",
                "location": "example.md",
                "page_title": "Example",
            },
        },
        "summary": {
            "total_findings": 0,
            "by_severity": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
            },
            "by_category": {},
        },
        "executive_summary": "No findings.",
        "findings": [],
    }
}


class FakeProvider:
    report = VALID_MODEL_REPORT

    def __init__(self, **kwargs):
        pass

    def complete(self, *, system: str, user: str) -> ModelResponse:
        return ModelResponse(
            text=json.dumps(self.report),
            usage=ModelUsage(input_tokens=1, output_tokens=1),
            stop_reason="end_turn",
        )


def test_scan_document_rejects_schema_invalid_model_output(monkeypatch):
    invalid_report = copy.deepcopy(VALID_MODEL_REPORT)
    invalid_report["report"]["unexpected_extra_field"] = "not allowed"
    FakeProvider.report = invalid_report
    monkeypatch.setattr("compliance_flag.scanner.AnthropicProvider", FakeProvider)

    with pytest.raises(ValidationError):
        scan_document(
            SourceDocument(
                source_type="file",
                location="example.md",
                title="Example",
                content="Body",
            )
        )


def test_scan_document_accepts_schema_valid_model_output(monkeypatch):
    FakeProvider.report = VALID_MODEL_REPORT
    monkeypatch.setattr("compliance_flag.scanner.AnthropicProvider", FakeProvider)

    result = scan_document(
        SourceDocument(
            source_type="file",
            location="example.md",
            title="Example",
            content="Body",
        )
    )

    assert result.schema_valid is True
    assert result.report["report"]["scan"]["source"]["location"] == "example.md"
