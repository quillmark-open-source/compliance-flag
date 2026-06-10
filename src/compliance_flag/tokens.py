from __future__ import annotations


def estimate_tokens(text: str) -> int:
    """Roughly estimate the token count of text (~4 characters per token).

    Exact usage is reported from the API response after each scan; this
    estimate only sizes prompts before sending.
    """
    return max(len(text) // 4, 1) if text else 0
