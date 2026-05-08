import json
import re
from pathlib import Path

from compliance_flag.reports.schema import validate_report

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_REPORT = ROOT / "examples" / "reports" / "example-blog-post-report.json"
EXAMPLE_HTML = ROOT / "examples" / "reports" / "example-blog-post-report.html"
EXAMPLE_METADATA = (
    ROOT / "examples" / "reports" / "example-blog-post-report.source-meta.json"
)


def test_example_report_is_valid():
    report = json.loads(EXAMPLE_REPORT.read_text(encoding="utf-8"))

    validate_report(report)


def test_example_report_uses_relative_source_paths():
    paths = [EXAMPLE_REPORT, EXAMPLE_HTML, EXAMPLE_METADATA]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in paths)

    assert not re.search(r"(?i)(/users/|/home/|[a-z]:\\\\)", combined)
    assert "tests/fixtures/example-blog-post.html" in combined
