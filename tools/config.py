from __future__ import annotations

import re
from pathlib import Path
import yaml

DEFAULTS: dict = {
    "language": "en-US",
    "style_preset": "business-playbook",
    "chapters": 10,
    "subsections_per_chapter": [4, 6],
    "word_target": 9000,
    "include_citations": False,
    "writer_model": "llama3.1:latest",
    "refiner_model": "qwen2:7b-instruct",
    "export": {"pdf": True, "epub": True, "docx": True, "pdf_engine": "wkhtmltopdf"},
}


def make_slug(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9\-\s]", "", text)
    text = re.sub(r"\s+", "-", text)
    return text[:80] or "book"


def deep_merge(a: dict, b: dict) -> dict:
    out = dict(a)
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_yaml(path: str | Path) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def load_config(path: str, pack: str = "") -> dict:
    cfg = deep_merge(DEFAULTS, load_yaml(path))
    if pack:
        pack_path = Path("packs") / f"{pack}.yaml"
        if pack_path.exists():
            cfg = deep_merge(cfg, load_yaml(pack_path))

    # derived
    words_per_chapter = max(400, int(cfg["word_target"] / max(1, cfg["chapters"])))
    cfg["words_per_chapter"] = words_per_chapter
    if not cfg.get("refiner_model"):
        cfg["refiner_model"] = cfg["writer_model"]
    return cfg
