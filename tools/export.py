from __future__ import annotations

import shutil, subprocess, re
from pathlib import Path

def has(cmd: str) -> bool:
    return shutil.which(cmd) is not None

def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)

def _sanitize_markdown_for_pandoc(src: Path, dest: Path) -> None:
    """
    Make a safe copy of markdown for Pandoc:
    - Strip any accidental YAML front matter at the top.
    - Replace standalone '---' lines outside code fences with '<hr/>' so Pandoc
      doesn't try to parse mid-file YAML.
    """
    text = src.read_text(encoding="utf-8")
    lines = text.splitlines()

    # 1) If the file *starts* with a YAML block (--- ... ---), drop it.
    if lines and lines[0].strip() == "---":
        j = 1
        while j < len(lines) and lines[j].strip() != "---":
            j += 1
        if j < len(lines):
            lines = lines[j + 1:]  # remove the YAML front matter entirely

    # 2) Replace any mid-file '---' line with <hr/> outside code fences.
    out_lines = []
    in_code = False
    for ln in lines:
        if ln.strip().startswith("```"):
            in_code = not in_code
            out_lines.append(ln)
            continue
        if not in_code and ln.strip() == "---":
            out_lines.append("<hr/>")
        else:
            out_lines.append(ln)

    dest.write_text("\n".join(out_lines), encoding="utf-8")

def export_all(cfg: dict, md_final: Path, cover: Path, outdir: Path) -> None:
    css = Path("css/pandoc.css")
    title = cfg["topic"]

    # Always sanitize to a temp file before handing to Pandoc
    md_safe = outdir / "book_pandoc.md"
    _sanitize_markdown_for_pandoc(md_final, md_safe)

    # EPUB
    if cfg["export"].get("epub", True) and has("pandoc"):
        run([
            "pandoc",
            str(md_safe),
            "-o", str(outdir / "book.epub"),
            "--toc",
            "--css", str(css),
            "--metadata", f"title={title}",
            "--epub-cover-image", str(cover),
        ])

    # DOCX
    if cfg["export"].get("docx", True) and has("pandoc"):
        run(["pandoc", str(md_safe), "-o", str(outdir / "book.docx"), "--toc"])

    # PDF
    if not cfg["export"].get("pdf", True):
        return

    engine = cfg["export"].get("pdf_engine", "tectonic")

    if engine in ("tectonic", "xelatex", "lualatex", "pdflatex"):
        if not has("pandoc"):
            print("Pandoc not found → skipping PDF.")
            return
        run([
            "pandoc",
            str(md_safe),
            "-o", str(outdir / "book.pdf"),
            f"--pdf-engine={engine}",
            "--toc",
        ])
        return

    if engine == "chrome":
        if not has("pandoc"):
            print("Pandoc not found → cannot produce HTML for chrome. Skipping PDF.")
            return
        html_path = outdir / "book.html"
        run([
            "pandoc",
            str(md_safe),
            "-o", str(html_path),
            "--toc",
            "--css", str(css),
            "--metadata", f"title={title}",
        ])
        # headless Chrome printing handled elsewhere if desired
        return

    print(f"Unknown pdf_engine '{engine}'. Skipping PDF (EPUB/DOCX still generated).")
