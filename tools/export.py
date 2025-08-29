from __future__ import annotations

import os, shutil, subprocess
from pathlib import Path

def has(cmd: str) -> bool:
    return shutil.which(cmd) is not None

def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)

def _find_chrome() -> str | None:
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
    ]
    return next((c for c in candidates if c and os.path.exists(c)), None)

def export_all(cfg: dict, md_final: Path, cover: Path, outdir: Path) -> None:
    css = Path("css/pandoc.css")
    title = cfg["topic"]

    if has("pandoc"):
        if cfg["export"].get("epub", True):
            run([
                "pandoc", str(md_final), "-o", str(outdir/"book.epub"),
                "--toc", "--css", str(css),
                "--metadata", f"title={title}",
                "--epub-cover-image", str(cover)
            ])
        if cfg["export"].get("docx", True):
            run(["pandoc", str(md_final), "-o", str(outdir/"book.docx"), "--toc"])

    if not cfg["export"].get("pdf", True):
        return

    engine = cfg["export"].get("pdf_engine", "tectonic")

    if engine in ("tectonic", "xelatex", "lualatex", "pdflatex"):
        if not has("pandoc"):
            print("Pandoc not found → skipping PDF.")
            return
        run([
            "pandoc", str(md_final), "-o", str(outdir/"book.pdf"),
            f"--pdf-engine={engine}", "--toc"
        ])
        return

    if engine == "chrome":
        if not has("pandoc"):
            print("Pandoc not found → cannot produce HTML for chrome. Skipping PDF.")
            return
        html_path = outdir / "book.html"
        run(["pandoc", str(md_final), "-o", str(html_path),
             "--toc", "--css", str(css), "--metadata", f"title={title}"])
        chrome = _find_chrome()
        if not chrome:
            print("Chrome/Chromium not found → PDF skipped (HTML available).")
            return
        run([chrome, "--headless", "--disable-gpu",
             f"--print-to-pdf={outdir/'book.pdf'}", str(html_path)])
        return

    print(f"Unknown pdf_engine '{engine}'. Skipping PDF (EPUB/DOCX still generated).")
