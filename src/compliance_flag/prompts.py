from __future__ import annotations

import json
import string
from dataclasses import dataclass
from datetime import datetime, timezone

from compliance_flag.reports.schema import model_output_schema_json
from compliance_flag.resources import read_text_asset
from compliance_flag.rules import load_rules
from compliance_flag.tokens import count_tokens


@dataclass(frozen=True)
class PromptPair:
    system: str
    user: str


def _render_template(template: str, **values: str) -> str:
    normalized = template
    for key in values:
        normalized = normalized.replace(f"{{{{{key}}}}}", f"${{{key}}}")
    return string.Template(normalized).safe_substitute(**values)


def _json_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def build_prompts(
    *,
    source_type: str,
    location: str,
    content: str,
    title: str,
) -> PromptPair:
    """Build model prompts from packaged templates."""
    rules = load_rules()
    schema = model_output_schema_json()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    system_template = (
        read_text_asset("prompts", "system-url.md")
        if source_type == "web"
        else read_text_asset("prompts", "system-file.md")
    )
    user_template = (
        read_text_asset("prompts", "user-url.md")
        if source_type == "web"
        else read_text_asset("prompts", "user-file.md")
    )

    system = _render_template(system_template, rules=rules, schema=schema)
    user = _render_template(
        user_template,
        date=today,
        filename_json=_json_string(location),
        url_json=_json_string(location),
        title_json=_json_string(title),
        content_json=_json_string(content),
    )

    system_tokens, method = count_tokens(system)
    user_tokens, _ = count_tokens(user)
    label = "~" if method == "estimated" else ""
    print(f"  prompt tokens ({method}):")
    print(f"    system: {label}{system_tokens:,}")
    print(f"    user:   {label}{user_tokens:,}")
    print(f"    total:  {label}{system_tokens + user_tokens:,}")

    return PromptPair(system=system, user=user)
