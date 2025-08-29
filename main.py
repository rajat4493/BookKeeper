#!/usr/bin/env python3
from __future__ import annotations

import argparse, json
from pathlib import Path
from rich import print

from tools.config import load_config, make_slug
from tools.outline import build_outline
from tools.draft import write_book
from tools.style_pass import style_variation
from tools.humanize import humanize
from tools.grammar import grammar_fix
from tools.make_cover import make_cover
from tools.export import export_all
from tools.quality import report as quality_report

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--pack", default="")
    args = parser.parse_args()

    cfg = load_config(args.config, pack=args.pack)
    slug = make_slug(cfg["topic"])
    outdir = Path("books") / slug
    outdir.mkdir(parents=True, exist_ok=True)

    outline_path = outdir / "outline.json"
    md_path = outdir / "book.md"
    refined_path = outdir / "book_refined.md"
    human_path = outdir / "book_human.md"
    final_path = outdir / "book_final.md"
    cover_path = outdir / "cover.png"
    quality_path = outdir / "quality.json"

    print(f"[bold]▶ Generating outline[/bold] → {outline_path}")
    outline = build_outline(cfg)
    outline_path.write_text(json.dumps(outline, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[bold]▶ Drafting chapters[/bold] → {md_path}")
    write_book(cfg, outline, md_path)

    print(f"[bold]▶ Style pass[/bold] → {refined_path}")
    style_variation(md_path, refined_path)

    if cfg.get("humanize", {}).get("enabled", False):
        print(f"[bold]▶ Humanize[/bold] → {human_path}")
        humanize(cfg, refined_path, human_path)
        source_for_grammar = human_path
    else:
        source_for_grammar = refined_path

    print(f"[bold]▶ Grammar pass[/bold] → {final_path}")
    grammar_fix(cfg, source_for_grammar, final_path)

    print(f"[bold]▶ Cover[/bold] → {cover_path}")
    make_cover(cfg, outline, cover_path)

    print(f"[bold]▶ Quality report[/bold] → {quality_path}")
    quality_report(final_path, quality_path)

    print(f"[bold]▶ Exporting[/bold]")
    export_all(cfg, final_path, cover_path, outdir)

    print(f"\n[green]Done.[/green] Output folder: {outdir}\n")

if __name__ == "__main__":
    main()
