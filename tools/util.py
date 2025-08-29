from __future__ import annotations

import json
import re

JSON_RE = re.compile(r"\{[\s\S]*\}\s*$")


def extract_json(text: str) -> dict:
    """Extract the last JSON object from a model response."""
    m = JSON_RE.search(text.strip())
    if not m:
        # Attempt to remove code fences
        stripped = text.replace("```json", "").replace("```", "").strip()
        m = JSON_RE.search(stripped)
        if not m:
            raise ValueError("Could not parse JSON from model output")
        return json.loads(m.group(0))
    return json.loads(m.group(0))
