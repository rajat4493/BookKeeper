from __future__ import annotations

from pathlib import Path


def grammar_fix(cfg: dict, in_path: Path, out_path: Path) -> None:
    text = Path(in_path).read_text(encoding="utf-8")
    lang = cfg.get("language", "en-US")
    try:
        import language_tool_python  # type: ignore
        tool = language_tool_python.LanguageTool(lang)
        matches = tool.check(text)
        fixed = language_tool_python.utils.correct(text, matches)
    except Exception:
        # Graceful fallback if LanguageTool/Java is unavailable
        fixed = text
    Path(out_path).write_text(fixed, encoding="utf-8")
