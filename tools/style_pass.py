from __future__ import annotations

import random
import re
from pathlib import Path

REPL = [
    (r"\bHowever,\b", "But "),
    (r"\bTherefore,\b", "So "),
    (r"\bIn addition,\b", "Also, "),
]


def tweak_line(ln: str) -> str:
    line = ln
    if len(line) > 140 and random.random() < 0.25:
        line = re.sub(r", and ", ". And ", line, count=1)
    if random.random() < 0.20:
        for pat, rep in REPL:
            if re.search(pat, line):
                line = re.sub(pat, rep, line)
                break
    return line


def style_variation(in_path: Path, out_path: Path) -> None:
    lines = Path(in_path).read_text(encoding="utf-8").splitlines()
    out_lines: list[str] = []
    for ln in lines:
        if ln.startswith("#") or ln.startswith("```"):
            out_lines.append(ln)
        else:
            out_lines.append(tweak_line(ln))
    Path(out_path).write_text("\n".join(out_lines), encoding="utf-8")
