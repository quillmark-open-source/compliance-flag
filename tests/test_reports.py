import json
from urllib.parse import urlparse

import pytest
from bs4 import BeautifulSoup
from jsonschema import ValidationError

from compliance_flag.disclaimer import REPORT_DISCLAIMER, report_generator
from compliance_flag.reports.json_extract import extract_json
from compliance_flag.reports.render_html import render_html
from compliance_flag.reports.schema import (
    _strip_unsupported_keywords,
    backfill_stripped_constraints,
    fix_summary,
    load_model_output_schema,
    validate_report,
)


def test_report_disclaimer_restricts_use_to_authorized_content():
    text = REPORT_DISCLAIMER["text"]

    assert "authorized personnel" in text
    assert "explicit permission" in text
    assert "third-party websites" in text


def test_extract_json_from_markdown_fence():
    assert extract_json('before\n```json\n{"ok": true}\n```\nafter') == {"ok": True}


def test_extract_json_handles_braces_inside_strings():
    payload = {"report": {"executive_summary": "Beware of } stray { braces"}}
    text = f"Here is the report:\n{json.dumps(payload)}\nDone."

    assert extract_json(text) == payload


def test_extract_json_rejects_non_object_json():
    with pytest.raises(ValueError, match="not a report object"):
        extract_json('[{"severity": "high"}]')


def test_extract_json_rejects_text_without_json():
    with pytest.raises(ValueError, match="could not extract valid JSON"):
        extract_json("no json here { unbalanced")


def test_fix_summary_recalculates_counts():
    report = {
        "report": {
            "findings": [
                {"severity": "high", "category": "general_prohibitions"},
                {"severity": "low", "category": "recordkeeping"},
                {"severity": "low", "category": "recordkeeping"},
            ]
        }
    }

    fix_summary(report)

    summary = report["report"]["summary"]
    assert summary["total_findings"] == 3
    assert summary["by_severity"]["high"] == 1
    assert summary["by_severity"]["low"] == 2
    assert summary["by_category"]["recordkeeping"] == 2


def test_fix_summary_ignores_unknown_severities_and_non_dict_findings():
    report = {
        "report": {
            "findings": [
                {"severity": "moderate", "category": "general_prohibitions"},
                "not a finding",
                {"category": "recordkeeping"},
            ]
        }
    }

    fix_summary(report)

    summary = report["report"]["summary"]
    assert summary["total_findings"] == 3
    assert set(summary["by_severity"]) == {"critical", "high", "medium", "low"}
    assert all(count == 0 for count in summary["by_severity"].values())


def _valid_report(findings: list | None = None) -> dict:
    return {
        "report": {
            "id": "11111111-1111-4111-8111-111111111111",
            "generated_at": "2026-05-08T12:00:00Z",
            "scanner_version": "0.1.0",
            "generator": report_generator("0.1.0"),
            "firm": {"name": "Example Adviser"},
            "scan": {
                "started_at": "2026-05-08T12:00:00Z",
                "completed_at": "2026-05-08T12:01:00Z",
                "source": {
                    "type": "file",
                    "location": "sample.html",
                    "page_title": "Sample",
                },
            },
            "summary": {
                "total_findings": len(findings or []),
                "by_severity": {
                    "critical": 0,
                    "high": 0,
                    "medium": len(findings or []),
                    "low": 0,
                },
                "by_category": (
                    {"general_prohibitions": len(findings)} if findings else {}
                ),
            },
            "executive_summary": "Summary.",
            "disclaimer": REPORT_DISCLAIMER,
            "findings": findings or [],
        }
    }


def _valid_finding() -> dict:
    return {
        "id": "22222222-2222-4222-8222-222222222222",
        "severity": "medium",
        "category": "general_prohibitions",
        "rule": {
            "authority": "SEC",
            "citation": "§ 275.206(4)-1(a)(2)",
            "rule_name": "Substantiation Requirement",
            "description": (
                "Advertisements must have a reasonable basis for "
                "material statements of fact."
            ),
        },
        "source": {
            "type": "file",
            "location": "sample.html",
            "accessed_at": "2026-05-08T12:00:00Z",
        },
        "content": {"excerpt": "We deliver superior outcomes."},
        "violation": {
            "explanation": "The claim may require substantiation.",
            "remediation": {
                "summary": "Revise or substantiate the claim.",
                "steps": [
                    "Document the factual basis for the claim.",
                    "Revise the language if substantiation is unavailable.",
                ],
                "suggested_language": (
                    "Our team provides investment advisory services "
                    "tailored to client needs."
                ),
            },
        },
    }


def test_report_schema_accepts_structured_remediation():
    validate_report(_valid_report([_valid_finding()]))


def test_report_schema_accepts_package_patch_versions():
    report = _valid_report()
    report["report"]["scanner_version"] = "0.1.1"
    report["report"]["generator"] = report_generator("0.1.1")

    validate_report(report)


def test_report_schema_rejects_malformed_timestamps():
    finding = _valid_finding()
    finding["source"]["accessed_at"] = "yesterday"

    with pytest.raises(ValidationError):
        validate_report(_valid_report([finding]))


def test_report_schema_rejects_malformed_generated_at():
    report = _valid_report()
    report["report"]["generated_at"] = "not a timestamp"

    with pytest.raises(ValidationError):
        validate_report(report)


def test_model_output_schema_excludes_hardcoded_fields():
    schema = load_model_output_schema()
    report_schema = schema["properties"]["report"]

    for field in [
        "disclaimer",
        "generator",
        "generated_at",
        "scanner_version",
        "summary",
        "scan",
    ]:
        assert field not in report_schema["required"]
        assert field not in report_schema["properties"]


def test_model_output_schema_strips_unsupported_keywords():
    text = json.dumps(load_model_output_schema())

    for keyword in ["pattern", "minimum", "minItems", "maxLength"]:
        assert f'"{keyword}"' not in text


def test_render_html_formats_structured_remediation_as_numbered_list():
    html = render_html(
        {
            "report": {
                "generated_at": "2026-05-08T12:00:00Z",
                "scanner_version": "0.1.0",
                "generator": report_generator("0.1.0"),
                "firm": {"name": "Example Adviser"},
                "scan": {
                    "source": {
                        "type": "file",
                        "location": "sample.html",
                        "page_title": "Sample",
                    }
                },
                "summary": {
                    "total_findings": 1,
                    "by_severity": {
                        "critical": 0,
                        "high": 0,
                        "medium": 1,
                        "low": 0,
                    },
                },
                "executive_summary": "One finding.\nSecond paragraph.",
                "disclaimer": REPORT_DISCLAIMER,
                "findings": [
                    {
                        "severity": "medium",
                        "rule": {
                            "citation": "§ 275.206(4)-1(a)(2)",
                            "rule_name": "Substantiation Requirement",
                            "description": "Claims must be substantiated.",
                        },
                        "content": {"excerpt": "A claim."},
                        "violation": {
                            "explanation": "The claim may need support.",
                            "remediation": {
                                "summary": "Revise or substantiate the claim.",
                                "steps": [
                                    "Gather support for the statement.",
                                    "Revise the statement if support is unavailable.",
                                ],
                                "suggested_language": (
                                    "We provide advisory services tailored to "
                                    "client needs."
                                ),
                            },
                        },
                    }
                ],
            }
        }
    )

    assert "<h4>Recommended Changes</h4>" in html
    assert "<p>One finding.</p>\n<p>Second paragraph.</p>" in html
    assert "<p>Revise or substantiate the claim.</p>\n<ol>" in html
    assert "<ol>\n  <li>Gather support for the statement.</li>" in html
    assert "  <li>Revise the statement if support is unavailable.</li>\n</ol>" in html
    assert "</ol>\n<h5>Suggested Language</h5>" in html
    assert "<h5>Suggested Language</h5>" in html


def test_render_html_escapes_report_content():
    html = render_html(
        {
            "report": {
                "generated_at": "2026-05-08T12:00:00Z",
                "scanner_version": "0.1.0",
                "generator": report_generator("0.1.0"),
                "firm": {"name": "<Firm>"},
                "scan": {
                    "source": {
                        "type": "file",
                        "location": "sample.html",
                        "page_title": "<Title>",
                    }
                },
                "summary": {
                    "total_findings": 0,
                    "by_severity": {
                        "critical": 0,
                        "high": 0,
                        "medium": 0,
                        "low": 0,
                    },
                },
                "executive_summary": "Nothing <script>bad()</script>",
                "disclaimer": REPORT_DISCLAIMER,
                "findings": [],
            }
        }
    )

    assert "&lt;Firm&gt;" in html
    assert "by Compliance Flag\n      CLI\n      v0.1.0" in html
    soup = BeautifulSoup(html, "html.parser")
    footer_links = [
        urlparse(link["href"]) for link in soup.select(".report-disclaimer a[href]")
    ]
    assert any(
        link.scheme == "https"
        and link.netloc == "complianceflag.com"
        and link.path == "/"
        for link in footer_links
    )
    assert "automated review-support tool" in html
    assert "<script>bad()</script>" not in html


def test_render_html_escapes_model_controlled_finding_fields():
    hostile = "<script>alert(1)</script>"
    html = render_html(
        {
            "report": {
                "generated_at": "2026-05-08T12:00:00Z",
                "scanner_version": "0.1.0",
                "generator": report_generator("0.1.0"),
                "firm": {"name": "Example Adviser"},
                "scan": {
                    "source": {
                        "type": "file",
                        "location": "sample.html",
                        "page_title": "Sample",
                    }
                },
                "summary": {
                    "total_findings": 1,
                    "by_severity": {
                        "critical": 0,
                        "high": 1,
                        "medium": 0,
                        "low": 0,
                    },
                },
                "executive_summary": "One finding.",
                "disclaimer": REPORT_DISCLAIMER,
                "findings": [
                    {
                        "severity": "high",
                        "rule": {
                            "citation": f"cite {hostile}",
                            "rule_name": f"name {hostile}",
                            "description": f"desc {hostile}",
                        },
                        "related_rules": [
                            {
                                "authority": "SEC",
                                "citation": f"related {hostile}",
                                "rule_name": f"related-name {hostile}",
                            }
                        ],
                        "content": {
                            "excerpt": f"excerpt {hostile}",
                            "context": f"context {hostile}",
                        },
                        "violation": {
                            "explanation": f"explanation {hostile}",
                            "remediation": {
                                "summary": f"summary {hostile}",
                                "steps": [f"step {hostile}"],
                                "suggested_language": f"language {hostile}",
                            },
                        },
                    }
                ],
            }
        }
    )

    assert hostile not in html
    assert html.count("&lt;script&gt;alert(1)&lt;/script&gt;") >= 10


def test_backfill_stripped_constraints_repairs_empty_steps():
    report = {
        "report": {
            "findings": [
                {
                    "violation": {
                        "remediation": {"summary": "Fix it.", "steps": []},
                    }
                }
            ]
        }
    }

    backfill_stripped_constraints(report)

    steps = report["report"]["findings"][0]["violation"]["remediation"]["steps"]
    assert len(steps) == 1


def test_strip_unsupported_keywords_preserves_colliding_property_names():
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "pattern": {"type": "string", "minLength": 3},
            "minimum": {"type": "integer"},
        },
        "required": ["pattern", "minimum"],
    }

    _strip_unsupported_keywords(schema)

    assert set(schema["properties"]) == {"pattern", "minimum"}
    assert "minLength" not in schema["properties"]["pattern"]
