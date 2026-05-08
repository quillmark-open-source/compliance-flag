from compliance_flag.disclaimer import REPORT_DISCLAIMER, report_generator
from compliance_flag.reports.json_extract import extract_json
from compliance_flag.reports.render_html import render_html
from compliance_flag.reports.schema import (
    fix_summary,
    load_model_output_schema,
    repair_report_shape,
    validate_report,
)


def test_extract_json_from_markdown_fence():
    assert extract_json('before\n```json\n{"ok": true}\n```\nafter') == {"ok": True}


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


def test_repair_report_shape_adds_missing_rule_description():
    report = {
        "report": {
            "findings": [
                {
                    "rule": {
                        "authority": "SEC",
                        "citation": "§ 275.206(4)-1(a)(2)",
                        "rule_name": "Substantiation Requirement",
                    }
                }
            ]
        }
    }

    repair_report_shape(report)

    description = report["report"]["findings"][0]["rule"]["description"]
    assert "§ 275.206(4)-1(a)(2)" in description
    assert "Substantiation Requirement" in description


def test_repair_report_shape_moves_top_level_findings_into_report():
    report = {
        "report": {
            "findings": [],
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
        },
        "findings": [
            {
                "severity": "high",
                "category": "general_prohibitions",
                "rule": {
                    "authority": "SEC",
                    "citation": "§ 275.206(4)-1(a)(4)",
                    "rule_name": "Benefits Without Risks or Limitations",
                    "description": "Benefits must be fair and balanced.",
                },
            }
        ],
    }

    repair_report_shape(report)
    fix_summary(report)

    assert "findings" not in report
    assert report["report"]["summary"]["total_findings"] == 1
    assert report["report"]["summary"]["by_severity"]["high"] == 1
    assert report["report"]["findings"][0]["rule"]["citation"] == (
        "§ 275.206(4)-1(a)(4)"
    )


def test_repair_report_shape_converts_string_remediation():
    report = {
        "report": {
            "findings": [
                {
                    "rule": {
                        "authority": "SEC",
                        "citation": "§ 275.206(4)-1(a)(2)",
                        "rule_name": "Substantiation Requirement",
                    },
                    "violation": {
                        "remediation": "Add substantiation or revise the claim."
                    },
                }
            ]
        }
    }

    repair_report_shape(report)

    remediation = report["report"]["findings"][0]["violation"]["remediation"]
    assert remediation["summary"] == (
        "Review and remediate the issue identified in this finding."
    )
    assert remediation["steps"] == ["Add substantiation or revise the claim."]


def test_report_schema_accepts_structured_remediation():
    report = {
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
                "total_findings": 1,
                "by_severity": {
                    "critical": 0,
                    "high": 0,
                    "medium": 1,
                    "low": 0,
                },
                "by_category": {"general_prohibitions": 1},
            },
            "executive_summary": "One potential issue was identified.",
            "disclaimer": REPORT_DISCLAIMER,
            "findings": [
                {
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
            ],
        }
    }

    validate_report(report)


def test_model_output_schema_excludes_hardcoded_disclaimer():
    schema = load_model_output_schema()
    report_schema = schema["properties"]["report"]

    assert "disclaimer" not in report_schema["required"]
    assert "disclaimer" not in report_schema["properties"]
    assert "generator" not in report_schema["required"]
    assert "generator" not in report_schema["properties"]


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
                "executive_summary": "One finding.",
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
    assert "<ol><li>Gather support for the statement.</li>" in html
    assert "<li>Revise the statement if support is unavailable.</li></ol>" in html
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
    assert "https://complianceflag.com/" in html
    assert "automated review-support tool" in html
    assert "<script>bad()</script>" not in html
