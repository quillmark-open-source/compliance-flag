from __future__ import annotations

import html
from datetime import datetime
from pathlib import Path

SEVERITY_COLORS = {
    "critical": "#b91c1c",
    "high": "#ea580c",
    "medium": "#ca8a04",
    "low": "#2563eb",
}


def _esc(value: object) -> str:
    return html.escape("" if value is None else str(value))


def _format_datetime(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.strftime("%Y-%m-%d %H:%M %Z")
    except (AttributeError, ValueError):
        return _esc(value)


def _render_remediation(remediation: object) -> str:
    if isinstance(remediation, str):
        return f"<p>{_esc(remediation)}</p>"
    if not isinstance(remediation, dict):
        return '<p class="empty">No recommended changes were provided.</p>'

    summary = remediation.get("summary")
    steps = remediation.get("steps", [])
    suggested_language = remediation.get("suggested_language")

    parts: list[str] = []
    if summary:
        parts.append(f"<p>{_esc(summary)}</p>")

    if isinstance(steps, str):
        steps = [steps]
    if steps:
        items = "\n".join(f"  <li>{_esc(step)}</li>" for step in steps)
        parts.append(f"<ol>\n{items}\n</ol>")

    if suggested_language:
        parts.append(
            "<h5>Suggested Language</h5>\n"
            f"<blockquote>{_esc(suggested_language)}</blockquote>"
        )

    return (
        "\n".join(parts) or '<p class="empty">No recommended changes were provided.</p>'
    )


def _render_finding(finding: dict, index: int) -> str:
    severity = finding.get("severity", "low")
    color = SEVERITY_COLORS.get(severity, SEVERITY_COLORS["low"])
    rule = finding.get("rule", {})
    content = finding.get("content", {})
    violation = finding.get("violation", {})
    related = finding.get("related_rules", [])
    related_html = ""
    if related:
        items = "\n".join(
            f"    <li>{_esc(item.get('authority'))} {_esc(item.get('citation'))}"
            f" {_esc(item.get('rule_name', ''))}</li>"
            for item in related
        )
        related_html = f"""  <h4>Related Rules</h4>
  <ul>
{items}
  </ul>
"""

    context_html = ""
    if content.get("context"):
        context_html = (
            f"  <p><strong>Context:</strong> {_esc(content.get('context'))}</p>\n"
        )

    return f"""<section class="finding" style="border-left-color: {color}">
  <div class="finding-head">
    <span class="badge" style="background: {color}">{_esc(severity).title()}</span>
    <span class="finding-number">#{index}</span>
  </div>
  <h3>{_esc(rule.get("citation"))} - {_esc(rule.get("rule_name"))}</h3>
  <p class="rule-description">{_esc(rule.get("description"))}</p>
{related_html}\
  <blockquote>{_esc(content.get("excerpt"))}</blockquote>
{context_html}\
  <h4>Issue</h4>
  <p>{_esc(violation.get("explanation"))}</p>
  <h4>Recommended Changes</h4>
  {_render_remediation(violation.get("remediation"))}
</section>
"""


def render_html(report_document: dict) -> str:
    report = report_document.get("report", report_document)
    firm = report.get("firm", {})
    generator = report.get("generator", {})
    scan = report.get("scan", {})
    source = scan.get("source", {})
    summary = report.get("summary", {})
    disclaimer = report.get("disclaimer", {})
    by_severity = summary.get("by_severity", {})
    findings = report.get("findings", [])
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    sorted_findings = sorted(
        findings, key=lambda item: severity_order.get(item.get("severity", "low"), 4)
    )
    findings_html = "\n".join(
        _render_finding(finding, index + 1)
        for index, finding in enumerate(sorted_findings)
    )
    if not findings_html:
        findings_html = '<p class="empty">No potential findings were reported.</p>'

    badges = "\n".join(
        f'<span class="summary-badge">{level}: {_esc(by_severity.get(level, 0))}</span>'
        for level in ["critical", "high", "medium", "low"]
    )
    executive_summary = "\n".join(
        f"<p>{_esc(paragraph.strip())}</p>"
        for paragraph in str(report.get("executive_summary", "")).split("\n")
        if paragraph.strip()
    )

    location = _esc(source.get("location"))

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Compliance Flag Report - {_esc(firm.get("name", "Unknown Firm"))}</title>
<style>
  :root {{
    color-scheme: light;
    --ink: #172033;
    --muted: #5b6475;
    --line: #d9dee8;
    --paper: #ffffff;
    --wash: #f6f8fb;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    color: var(--ink);
    background: var(--wash);
    line-height: 1.55;
  }}
  main {{ max-width: 960px; margin: 0 auto; padding: 32px 20px 56px; }}
  header {{
    background: #101827;
    color: white;
    padding: 28px;
    border-radius: 8px;
    margin-bottom: 20px;
  }}
  h1 {{ margin: 0 0 6px; font-size: 28px; }}
  h2 {{ margin-top: 0; }}
  h3 {{ margin-bottom: 6px; }}
  .meta {{ color: #cbd5e1; font-size: 14px; }}
  .panel, .finding {{
    background: var(--paper);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 22px;
    margin-bottom: 18px;
  }}
  .summary-badge {{
    display: inline-block;
    border: 1px solid var(--line);
    border-radius: 999px;
    padding: 4px 10px;
    margin: 4px 6px 4px 0;
    font-size: 13px;
    text-transform: capitalize;
  }}
  .finding {{
    border-left: 5px solid #2563eb;
  }}
  .finding-head {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
  }}
  .badge {{
    color: white;
    border-radius: 999px;
    padding: 3px 10px;
    font-size: 12px;
    font-weight: 700;
  }}
  .finding-number {{ color: var(--muted); font-size: 13px; }}
  .rule-description, .empty {{ color: var(--muted); }}
  .report-disclaimer {{
    color: var(--muted);
    font-size: 12px;
    margin-top: 30px;
    padding-top: 16px;
    border-top: 1px solid var(--line);
  }}
  .report-disclaimer p {{
    margin: 0 0 8px;
  }}
  blockquote {{
    margin: 14px 0;
    padding: 12px 14px;
    border-left: 3px solid var(--line);
    background: var(--wash);
  }}
  a {{ color: #1d4ed8; overflow-wrap: anywhere; }}
  @media print {{
    body {{ background: white; }}
    main {{ max-width: none; padding: 0; }}
    header, .panel, .finding {{ break-inside: avoid; }}
  }}
</style>
</head>
<body>
<main>
  <header>
    <h1>Compliance Flag Report</h1>
    <div class="meta">
      {_esc(firm.get("name", "Unknown Firm"))} |
      generated {_format_datetime(report.get("generated_at", ""))} |
      by {_esc(generator.get("name", "Compliance Flag"))}
      {_esc(generator.get("kind", "CLI"))}
      v{_esc(generator.get("version", report.get("scanner_version", "")))}
    </div>
  </header>
  <section class="panel">
    <h2>Source</h2>
    <p><strong>Type:</strong> {_esc(source.get("type"))}</p>
    <p><strong>Title:</strong> {_esc(source.get("page_title"))}</p>
    <p><strong>Location:</strong> <a href="{location}">{location}</a></p>
  </section>
  <section class="panel">
    <h2>Summary</h2>
    <p><strong>Total findings:</strong> {_esc(summary.get("total_findings", 0))}</p>
    <div>{badges}</div>
  </section>
  <section class="panel">
    <h2>Executive Summary</h2>
    {executive_summary or '<p class="empty">No executive summary was provided.</p>'}
  </section>
  <h2>Findings</h2>
{findings_html}
  <footer class="report-disclaimer">
    <p>{_esc(disclaimer.get("text"))}</p>
    <p>
      {_esc(disclaimer.get("product", "Compliance Flag"))}:
      <a href="{_esc(disclaimer.get("website", "https://complianceflag.com/"))}">
        {_esc(disclaimer.get("website", "https://complianceflag.com/"))}
      </a>
    </p>
  </footer>
</main>
</body>
</html>
"""


def save_html_report(report_document: dict, report_path: Path) -> Path:
    html_path = report_path.with_suffix(".html")
    html_path.write_text(render_html(report_document), encoding="utf-8")
    return html_path
