from __future__ import annotations

from importlib.resources import files

PACKAGE = "compliance_flag"


def read_text_asset(*parts: str) -> str:
    """Read a packaged text asset."""
    resource = files(PACKAGE).joinpath("assets", *parts)
    return resource.read_text(encoding="utf-8")
