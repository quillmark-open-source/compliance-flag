from __future__ import annotations

import copy
import json

import jsonschema

from compliance_flag.resources import read_text_asset


def load_schema() -> dict:
    return json.loads(read_text_asset("schemas", "report-schema.json"))


def load_model_output_schema() -> dict:
    """Load the schema shown to the model before hardcoded fields are added."""
    schema = copy.deepcopy(load_schema())
    report_schema = schema["properties"]["report"]
    for hardcoded_field in ["disclaimer", "generator"]:
        report_schema["properties"].pop(hardcoded_field, None)
    report_schema["required"] = [
        field
        for field in report_schema["required"]
        if field not in {"disclaimer", "generator"}
    ]
    return schema


def model_output_schema_json() -> str:
    return json.dumps(load_model_output_schema(), indent=2)


def validate_report(report: dict) -> None:
    validator = jsonschema.Draft202012Validator(
        load_schema(),
        format_checker=jsonschema.FormatChecker(),
    )
    validator.validate(report)


def repair_report_shape(report: dict) -> None:
    """Fill deterministic report fields that models may occasionally omit."""
    body = report.get("report", report)
    for finding in body.get("findings", []):
        rule = finding.get("rule")
        if not isinstance(rule, dict):
            continue
        if not rule.get("description"):
            citation = rule.get("citation", "the cited rule")
            rule_name = rule.get("rule_name", "the cited requirement")
            rule["description"] = (
                f"Potential concern under {citation} ({rule_name})."
            )
        violation = finding.get("violation")
        if not isinstance(violation, dict):
            continue
        remediation = violation.get("remediation")
        if isinstance(remediation, str):
            violation["remediation"] = {
                "summary": "Review and remediate the issue identified in this finding.",
                "steps": [remediation],
            }
        elif isinstance(remediation, dict):
            steps = remediation.get("steps")
            if isinstance(steps, str):
                remediation["steps"] = [steps]
            if not remediation.get("summary"):
                remediation["summary"] = (
                    "Review and remediate the issue identified in this finding."
                )
            if not remediation.get("steps"):
                remediation["steps"] = [
                    "Update the content to address the potential compliance concern."
                ]


def fix_summary(report: dict) -> None:
    """Recalculate summary counts from the actual findings array."""
    body = report.get("report", report)
    findings = body.get("findings", [])

    by_severity: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    by_category: dict[str, int] = {}

    for finding in findings:
        severity = finding.get("severity", "unknown")
        by_severity[severity] = by_severity.get(severity, 0) + 1

        category = finding.get("category", "unknown")
        by_category[category] = by_category.get(category, 0) + 1

    body["summary"] = {
        "total_findings": len(findings),
        "by_severity": by_severity,
        "by_category": by_category,
    }
