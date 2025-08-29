# Topic‑Agnostic eBook Generator (Local • Ollama)

Generate 20–50 page eBooks on **any topic** locally on macOS (or Linux) using **Ollama** and free models. No cloud fees.

## Quick Start (macOS)
1. Install dependencies:
   ```bash
   brew install ollama pandoc wkhtmltopdf jq
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Pull a model:
   ```bash
   ollama pull llama3.1:8b-instruct
   ```
3. Edit `book.yml` (topic, audience, etc.).
4. Run:
   ```bash
   chmod +x make_book.sh
   ./make_book.sh --config book.yml
   ```
5. Outputs in `books/<slug>/`: `book.md`, `book.epub`, `book.pdf`, `book.docx`, `cover.png`.

> PDF engine: defaults to `wkhtmltopdf`. For LaTeX quality, install MacTeX and set `export.pdf_engine: xelatex` in `book.yml`.

## Domain Packs
Optional YAMLs in `packs/` to tweak structure/tone (e.g., `business-playbook`, `tutorial`, `health-wellness`).
