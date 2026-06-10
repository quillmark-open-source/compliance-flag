from __future__ import annotations

import json
import re


def extract_json(text: str) -> dict:
    """Extract a JSON object from raw model text.

    Structured outputs make the whole response valid JSON in the normal case;
    the fallbacks recover objects wrapped in code fences or prose.
    """
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        pass
    else:
        if isinstance(value, dict):
            return value
        raise ValueError("model response was JSON but not a report object")

    match = re.search(r"```(?:json)?\s*\n(.*?)\n```", text, re.DOTALL)
    if match:
        try:
            value = json.loads(match.group(1))
            if isinstance(value, dict):
                return value
        except json.JSONDecodeError:
            pass

    decoder = json.JSONDecoder()
    start = text.find("{")
    while start != -1:
        try:
            value, _ = decoder.raw_decode(text, start)
        except json.JSONDecodeError:
            pass
        else:
            if isinstance(value, dict):
                return value
        start = text.find("{", start + 1)

    raise ValueError("could not extract valid JSON from response")
