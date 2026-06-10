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
        "firm": {"name": "Example Firm"},
        "executive_summary": "No findings.",
        "findings": [],
    }
}

DOCUMENT = SourceDocument(
    source_type="file",
    location="example.md",
    title="Example",
    content="Body",
)


class FakeProvider:
    report = VALID_MODEL_REPORT
    stop_reason = "end_turn"
    text = None
    last_output_schema = None

    def __init__(self, **kwargs):
        pass

    def complete(self, *, system, user, output_schema=None) -> ModelResponse:
        FakeProvider.last_output_schema = output_schema
        text = self.text if self.text is not None else json.dumps(self.report)
        return ModelResponse(
            text=text,
            usage=ModelUsage(input_tokens=1, output_tokens=1),
            stop_reason=self.stop_reason,
        )


@pytest.fixture(autouse=True)
def fake_provider(monkeypatch):
    FakeProvider.report = VALID_MODEL_REPORT
    FakeProvider.stop_reason = "end_turn"
    FakeProvider.text = None
    FakeProvider.last_output_schema = None
    monkeypatch.setattr("compliance_flag.scanner.AnthropicProvider", FakeProvider)


def test_scan_document_rejects_schema_invalid_model_output():
    invalid_report = copy.deepcopy(VALID_MODEL_REPORT)
    invalid_report["report"]["unexpected_extra_field"] = "not allowed"
    FakeProvider.report = invalid_report

    with pytest.raises(ValidationError):
        scan_document(DOCUMENT)


def test_scan_document_accepts_schema_valid_model_output():
    result = scan_document(DOCUMENT)

    body = result.report["report"]
    assert body["scan"]["source"]["location"] == "example.md"
    assert body["summary"]["total_findings"] == 0
    assert body["disclaimer"]["product"] == "Compliance Flag"
    # ISO 8601 strings compare chronologically.
    assert body["scan"]["started_at"] <= body["scan"]["completed_at"]


def test_scan_document_passes_model_output_schema_to_provider():
    scan_document(DOCUMENT)

    schema = FakeProvider.last_output_schema
    assert schema is not None
    assert "summary" not in schema["properties"]["report"]["properties"]


def test_scan_document_rejects_truncated_response():
    FakeProvider.stop_reason = "max_tokens"

    with pytest.raises(RuntimeError, match="truncated at max_tokens"):
        scan_document(DOCUMENT)


def test_scan_document_reports_model_refusal():
    FakeProvider.stop_reason = "refusal"
    FakeProvider.text = ""

    with pytest.raises(RuntimeError, match="refusal"):
        scan_document(DOCUMENT)


def test_scan_document_rejects_empty_response():
    FakeProvider.text = "   "

    with pytest.raises(RuntimeError, match="did not include text content"):
        scan_document(DOCUMENT)
