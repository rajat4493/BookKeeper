from __future__ import annotations

import json, re
from pathlib import Path

VOWELS = set("aeiouyAEIOUY")

def _sentences(text: str) -> list[str]:
    return re.split(r"(?<=[.!?])\s+", text.strip())

def _words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z']+", text)

def _syllables(word: str) -> int:
    w = word.lower()
    count, prev_v = 0, False
    for ch in w:
        v = ch in VOWELS
        if v and not prev_v:
            count += 1
        prev_v = v
    if w.endswith("e") and count > 1:
        count -= 1
    return max(1, count)

def flesch_reading_ease(text: str) -> float:
    sents = _sentences(text)
    words = _words(text)
    if not sents or not words:
        return 0.0
    syllables = sum(_syllables(w) for w in words)
    ws = len(words) / max(1, len(sents))
    ss = syllables / max(1, len(words))
    return 206.835 - 1.015 * ws - 84.6 * ss

def report(md_path: Path, out_json: Path) -> None:
    text = md_path.read_text(encoding='utf-8')
    sentences = _sentences(text)
    words = _words(text)
    fre = flesch_reading_ease(text)
    data = {
        "sentences": len(sentences),
        "words": len(words),
        "avg_words_per_sentence": round(len(words)/max(1,len(sentences)), 2),
        "flesch_reading_ease": round(fre, 2),
        "note": "60-70 is plain English; aim 55-75 for general audiences.",
    }
    out_json.write_text(json.dumps(data, indent=2), encoding='utf-8')
