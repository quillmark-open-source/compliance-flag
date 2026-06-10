from __future__ import annotations

from dataclasses import dataclass

from compliance_flag.console import log
from compliance_flag.resources import read_text_asset
from compliance_flag.tokens import estimate_tokens


@dataclass(frozen=True)
class RuleSource:
    filename: str
    label: str


RULE_SOURCES = [
    RuleSource(
        "sec-rule-275-206-4-1-investor-marketing.md",
        "SEC Rule 275.206(4)-1 - Investment Adviser Marketing",
    ),
    RuleSource(
        "sec-rule-275-204-2-books-and-records.md",
        "SEC Rule 275.204-2 - Books and Records",
    ),
    RuleSource("sec-rule-279.md", "SEC Part 279 - Forms Under the Advisers Act"),
]


def load_rules() -> str:
    """Load bundled codified rule text for prompt injection."""
    log("loading regulatory rules")
    sections: list[str] = []
    for source in RULE_SOURCES:
        content = read_text_asset("regulations", source.filename)
        log(f"  loaded {source.filename} (~{estimate_tokens(content):,} tokens)")
        sections.append(
            f"### BEGIN: {source.label}\n\n{content}\n\n### END: {source.label}"
        )
    return "\n\n---\n\n".join(sections)
