from __future__ import annotations

import copy
import json

import jsonschema

from compliance_flag.resources import read_text_asset

# Fields stamped or recalculated by the scanner after the model responds.
# They are removed from the schema the model fills in via structured outputs.
HARDCODED_REPORT_FIELDS = [
    "disclaimer",
    "generator",
    "generated_at",
    "scanner_version",
    "summary",
    "scan",
]

# JSON Schema keywords the structured-outputs API does not accept. They are
# stripped from the model-facing schema and still enforced client-side by
# validate_report against the full schema.
_UNSUPPORTED_OUTPUT_KEYWORDS = {
    "pattern",
    "minimum",
    "maximum",
    "multipleOf",
    "minLength",
    "maxLength",
    "minItems",
    "maxItems",
}


def load_schema() -> dict:
    return json.loads(read_text_asset("schemas", "report-schema.json"))


def _strip_unsupported_keywords(node: object, *, is_name_map: bool = False) -> None:
    """Strip unsupported keywords from schema nodes.

    Dicts under ``properties``/``$defs`` map names to schemas; their keys are
    names, not keywords, so nothing is popped from them directly.
    """
    if isinstance(node, dict):
        if not is_name_map:
            for keyword in _UNSUPPORTED_OUTPUT_KEYWORDS:
                node.pop(keyword, None)
        for key, value in node.items():
            _strip_unsupported_keywords(
                value,
                is_name_map=not is_name_map and key in {"properties", "$defs"},
            )
    elif isinstance(node, list):
        for item in node:
            _strip_unsupported_keywords(item)


def load_model_output_schema() -> dict:
    """Load the schema the model fills in via structured outputs.

    Fields the scanner stamps afterward are removed, as are schema keywords
    the structured-outputs API rejects (those remain enforced client-side).
    """
    schema = copy.deepcopy(load_schema())
    report_schema = schema["properties"]["report"]
    for hardcoded_field in HARDCODED_REPORT_FIELDS:
        report_schema["properties"].pop(hardcoded_field, None)
    report_schema["required"] = [
        field
        for field in report_schema["required"]
        if field not in HARDCODED_REPORT_FIELDS
    ]
    _strip_unsupported_keywords(schema)
    return schema


def model_output_schema_json() -> str:
    return json.dumps(load_model_output_schema(), indent=2)


def validate_report(report: dict) -> None:
    validator = jsonschema.Draft202012Validator(
        load_schema(),
        format_checker=jsonschema.FormatChecker(),
    )
    validator.validate(report)


def backfill_stripped_constraints(report: dict) -> None:
    """Repair the few constraints structured outputs cannot enforce.

    ``minItems: 1`` on remediation steps is stripped from the model-facing
    schema, so an empty steps array would otherwise fail validation only
    after the API call has been paid for.
    """
    body = report.get("report", report)
    findings = body.get("findings", [])
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        remediation = finding.get("violation", {}).get("remediation")
        if isinstance(remediation, dict) and remediation.get("steps") == []:
            remediation["steps"] = [
                "Update the content to address the potential compliance concern."
            ]


KNOWN_SEVERITIES = ("critical", "high", "medium", "low")


def fix_summary(report: dict) -> None:
    """Recalculate summary counts from the actual findings array."""
    body = report.get("report", report)
    findings = body.get("findings", [])

    by_severity: dict[str, int] = dict.fromkeys(KNOWN_SEVERITIES, 0)
    by_category: dict[str, int] = {}

    for finding in findings:
        if not isinstance(finding, dict):
            continue
        severity = finding.get("severity")
        if severity in by_severity:
            by_severity[severity] += 1

        category = finding.get("category", "unknown")
        by_category[category] = by_category.get(category, 0) + 1

    body["summary"] = {
        "total_findings": len(findings),
        "by_severity": by_severity,
        "by_category": by_category,
    }
