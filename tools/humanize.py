from __future__ import annotations

import re, random
from pathlib import Path
from .ollama_client import generate

CONTRACTIONS = [
    (r"\bcan not\b", "cannot"),
    (r"\bdo not\b", "don't"),
    (r"\bdoes not\b", "doesn't"),
    (r"\bdid not\b", "didn't"),
    (r"\bare not\b", "aren't"),
    (r"\bis not\b", "isn't"),
    (r"\bwill not\b", "won't"),
    (r"\bhave not\b", "haven't"),
    (r"\bhas not\b", "hasn't"),
    (r"\bhad not\b", "hadn't"),
    (r"\bI am\b", "I'm"),
    (r"\byou are\b", "you're"),
    (r"\bwe are\b", "we're"),
    (r"\bthey are\b", "they're"),
    (r"\bI will\b", "I'll"),
    (r"\byou will\b", "you'll"),
]

def _contractions(text: str) -> str:
    for pat, rep in CONTRACTIONS:
        text = re.sub(pat, rep, text, flags=re.IGNORECASE)
    return text

def _insert_rhetorical_q(paragraphs: list[str], rate: float) -> list[str]:
    out = []
    for i, p in enumerate(paragraphs):
        out.append(p)
        if i < len(paragraphs) - 1 and random.random() < rate:
            out.append(random.choice([
                "Ever tried this approach before?",
                "Does that line up with your experience?",
                "What would it look like if you applied this today?",
            ]))
    return out

def _add_checklists(text: str) -> str:
    return re.sub(
        r"(\*\*Key Takeaways\*\*.*?)(\n\n)",
        r"\1\n- [ ] Try one idea today\n- [ ] Note one obstacle\n- [ ] Share a learning with a teammate\2",
        text,
        flags=re.DOTALL
    )

def humanize(cfg: dict, in_path: Path, out_path: Path) -> None:
    t = in_path.read_text(encoding='utf-8')
    hcfg = cfg.get('humanize', {})
    rate_q = float(hcfg.get('rhetorical_question_rate', 0.1))
    add_check = bool(hcfg.get('add_checklists', True))
    use_contr = bool(hcfg.get('contractions', True))

    # LLM light rewrite for warmth/voice
    persona = cfg.get('persona', 'a friendly coach')
    tone = cfg.get('tone', 'conversational, concise')
    prompt = f"""Rewrite the following markdown to be warmer, more conversational, and mentor-like.
Use second person where natural, occasional first-person as a mentor.
Keep headings and markdown intact. Keep facts intact.
Tone: {tone}
Persona: {persona}
Return only the revised markdown.
---
{t}
"""
    try:
        revised = generate(cfg['refiner_model'], prompt, options={'temperature': 0.7})
    except Exception:
        revised = t  # fallback

    if use_contr:
        revised = _contractions(revised)

    paras = [p.strip() for p in revised.split('\n\n') if p.strip()]
    revised = '\n\n'.join(_insert_rhetorical_q(paras, rate_q))

    if add_check:
        revised = _add_checklists(revised)

    out_path.write_text(revised, encoding='utf-8')
