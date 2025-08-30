from __future__ import annotations
import os, requests

BASE = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")

def _post(path: str, payload: dict) -> requests.Response:
    return requests.post(f"{BASE}{path}", json=payload, timeout=600)

def generate(model: str, prompt: str, options: dict | None = None) -> str:
    # Ensure we allow long outputs unless the caller overrides it
    opts = {"num_predict": 4096}
    if options:
        opts.update(options)

    # Prefer chat (works on more Ollama builds)
    payload_chat = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": opts,
    }
    r = _post("/api/chat", payload_chat)

    if r.status_code == 404:
        # Fallback to legacy /api/generate
        payload_gen = {"model": model, "prompt": prompt, "stream": False, "options": opts}
        r = _post("/api/generate", payload_gen)

    if not r.ok:
        try:
            body = r.json()
        except Exception:
            body = r.text
        raise RuntimeError(f"Ollama error {r.status_code}: {body}")

    data = r.json()
    # chat returns {"message":{"content":...}}, generate returns {"response":...}
    return (data.get("message", {}) or {}).get("content") or data.get("response", "")
