from __future__ import annotations

import json
import re


def extract_json(text: str) -> dict:
    """Extract a JSON object from raw model text."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"```(?:json)?\s*\n(.*?)\n```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    brace_start = text.find("{")
    if brace_start != -1:
        depth = 0
        for index in range(brace_start, len(text)):
            if text[index] == "{":
                depth += 1
            elif text[index] == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(text[brace_start : index + 1])

    raise ValueError("could not extract valid JSON from response")
