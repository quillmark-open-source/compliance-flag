from __future__ import annotations


def count_tokens(text: str) -> tuple[int, str]:
    """Count tokens with tiktoken when available, otherwise estimate."""
    try:
        import tiktoken

        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text)), "tiktoken"
    except ImportError:
        return max(len(text) // 4, 1) if text else 0, "estimated"
