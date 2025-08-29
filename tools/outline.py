from __future__ import annotations
from .ollama_client import generate
from .util import extract_json

TPL = """
Return STRICT JSON with keys: title, subtitle, audience, chapters.
- title: compelling book title for: {topic}
- subtitle: concise promise (<= 110 chars)
- audience: {audience}
- chapters: a list of exactly {chapters} items; each item has:
  - title
  - subsections: {sub_lo}-{sub_hi} concise bullet titles

Constraints:
- Style preset: {style}
- Tone: {tone}
- Language: {lang}
- Region focus: {region}
- Avoid filler; ensure progression from fundamentals to advanced.
Return ONLY JSON.
"""

def build_outline(cfg: dict) -> dict:
  prompt = TPL.format(
                topic=cfg["topic"],
                audience=cfg["audience"],
                chapters=cfg["chapters"],
                sub_lo=cfg["subsections_per_chapter"][0],
                sub_hi=cfg["subsections_per_chapter"][1],
                style=cfg["style_preset"],
                tone=cfg.get("tone", "practical, concise, human"),
                lang=cfg["language"],
                region=cfg.get("region") or "generic/global",
            )
  raw = generate(cfg["writer_model"], prompt, options={"temperature": 0.7})
  data = extract_json(raw)
  data["chapters"] = data.get("chapters", [])[: cfg["chapters"]]
  return data
