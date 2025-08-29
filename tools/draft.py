from __future__ import annotations
from pathlib import Path
from .ollama_client import generate

CHAPTER_TPL = """
Write a detailed chapter (~{words} words) for a {style} eBook.
Chapter: {title}
Subsections: {subs}
Audience: {audience}
Tone: {tone}
Language: {lang}
Region: {region}
Include:
- Varied sentence length, bullets, brief examples
- 1 small table if useful (markdown table)
- End with a 'Key Takeaways' list
Avoid:
- Repetition, vague generalities, hallucinated stats
"""

def write_book(cfg: dict, outline: dict, md_path: Path) -> None:
            words = cfg["words_per_chapter"]
            chapters = outline.get("chapters", [])
            title = outline.get("title", cfg["topic"])
            subtitle = outline.get("subtitle", "")

            with md_path.open("w", encoding="utf-8") as f:
                f.write(f"# {title}\n\n")
                if subtitle:
                    f.write(f"_{subtitle}_\n\n")
                for i, ch in enumerate(chapters, start=1):
                    subs = ", ".join(ch.get("subsections", []))
                    prompt = CHAPTER_TPL.format(
                        words=words,
                        style=cfg["style_preset"],
                        title=ch.get("title", f"Chapter {i}"),
                        subs=subs,
                        audience=cfg["audience"],
                        tone=cfg.get("tone", "practical, concise, human"),
                        lang=cfg["language"],
                        region=(cfg.get("region") or "generic/global"),
                    )
                    text = generate(cfg["writer_model"], prompt, options={"temperature": 0.8})
                    f.write(f"\n\n## {i}. {ch.get('title', 'Untitled')}\n\n{text.strip()}\n")
