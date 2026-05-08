from __future__ import annotations

from datetime import datetime


def log(message: str) -> None:
    """Print a small timestamped CLI log line."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"  [{timestamp}] {message}")
